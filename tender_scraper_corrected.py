from playwright.sync_api import sync_playwright
import pandas as pd
import time
import os
import re
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import logging
from groq import Groq
from typing import Dict, List
import json

# ======================= CONFIG =======================

# AI-based filtering configuration
USE_AI_FILTERING = True  # Set to False to disable AI filtering
AI_BATCH_SIZE = 20  # Process this many titles in one API call (efficient batching)
MISTRAL_API_KEY = os.getenv("GROQ_API_KEY", "")  # Groq key (variable name kept so the rest of the script works)
GROQ_MODEL = "openai/gpt-oss-20b"

# Phase 2 configuration
ENABLE_PHASE_2 = True  # Set to False to skip Work Description extraction
PHASE_2_DELAY = 1  # Seconds to wait between detail page loads (avoid rate limiting)

MAX_RETRIES = 3
OUTPUT_FILE = "NIC_Filtered_Tenders_All_Portals.xlsx"
RUN_DATE = datetime.now().strftime("%Y-%m-%d")

# Parallel processing settings
MAX_CONCURRENT_PORTALS = 4  # Adjust based on your RAM (10-20 recommended)
THREAD_TIMEOUT = 600  # 10 minutes per portal max (increased for Phase 2)

# ======================= LOGGING =======================

import sys
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(threadName)-12s] %(levelname)-8s %(message)s',
    handlers=[
        logging.FileHandler(f'scraper_{RUN_DATE}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ======================= PORTALS =======================

PORTALS = {
    "West Bengal": "https://wbtenders.gov.in/nicgep/app",
    "Central Govt eProcurement": "https://eprocure.gov.in/eprocure/app",
    "CPSE eProcurement": "https://etenders.gov.in/eprocure/app",
    "Defence e-Procurement": "https://defproc.gov.in/nicgep/app",
    "PMGSY": "https://pmgsytenders.gov.in/nicgep/app",
    "BEL Defence": "https://eprocurebel.co.in/nicgep/app",
    "BHEL": "https://eprocurebhel.co.in/nicgep/app",
    "Coal India Limited": "https://coalindiatenders.nic.in/nicgep/app",
    "CPCL": "https://cpcletenders.nic.in/nicgep/app",
    "Garden Reach Shipbuilders (GRSE)": "https://eprocuregrse.co.in/nicgep/app",
    "Goa Shipyard Limited": "https://eprocuregsl.nic.in/nicgep/app",
    "Hindustan Shipyard Limited": "https://eprocurehsl.nic.in/nicgep/app",
    "IOCL": "https://iocletenders.nic.in/nicgep/app",
    "Mazagon Dock Shipbuilders": "https://eprocuremdl.nic.in/nicgep/app",
    "MIDHANI": "https://eprocuremidhani.nic.in/nicgep/app",
    "NTPC Limited": "https://eprocurentpc.nic.in/nicgep/app",
    "Andaman": "https://eprocure.andamannicobar.gov.in/nicgep/app",
    "Arunachal": "https://arunachaltenders.gov.in/nicgep/app",
    "Assam": "https://assamtenders.gov.in/nicgep/app",
    "Chandigarh": "https://etenders.chd.nic.in/nicgep/app",
    "UT Nagar": "https://dnhtenders.gov.in/nicgep/app",
    "UT Daman": "https://ddtenders.gov.in/nicgep/app",
    "NCT Delhi": "https://govtprocurement.delhi.gov.in/nicgep/app",
    "Goa": "https://eprocure.goa.gov.in/nicgep/app",
    "Haryana": "https://etenders.hry.nic.in/nicgep/app",
    "Himachal": "https://hptenders.gov.in/nicgep/app",
    "Jammu": "https://jktenders.gov.in/nicgep/app",
    "Jharkhand": "https://jharkhandtenders.gov.in/nicgep/app",
    "Kerala": "https://etenders.kerala.gov.in/nicgep/app",
    "Lakshadweep": "https://tendersutl.gov.in/nicgep/app",
    "Maharashtra": "https://mahatenders.gov.in/nicgep/app",
    "MP": "https://mptenders.gov.in/nicgep/app",
    "Manipur": "https://manipurtenders.gov.in/nicgep/app",
    "Meghalaya": "https://meghalayatenders.gov.in/nicgep/app",
    "Mizoram": "https://mizoramtenders.gov.in/nicgep/app",
    "Nagaland": "https://nagalandtenders.gov.in/nicgep/app",
    "Odisha": "https://tendersodisha.gov.in/nicgep/app",
    "Puducherry": "https://pudutenders.gov.in/nicgep/app",
    "Punjab": "https://eproc.punjab.gov.in/nicgep/app",
    "Rajasthan": "https://eproc.rajasthan.gov.in/nicgep/app",
    "Sikkim": "https://sikkimtender.gov.in/nicgep/app",
    "Tamil Nadu": "https://tntenders.gov.in/nicgep/app",
    "Tripura": "https://tripuratenders.gov.in/nicgep/app",
    "Ladakh": "https://tenders.ladakh.gov.in/nicgep/app",
    "Uttarakhand": "https://uktenders.gov.in/nicgep/app",
    "Uttar Pradesh": "https://etender.up.nic.in/nicgep/app",
}

# ======================= AI FILTERING (GROQ) =======================

class IsolatedTitleChecker:
    """
    ✅ ISOLATED AI checker - each portal session gets its own instance.
    NO shared cache across portals to prevent data bleed.
    """
    
    def __init__(self, api_key: str, portal_name: str):
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set!")
        self.client = Groq(api_key=api_key)
        self.portal_name = portal_name
        # ✅ ISOLATED CACHE: Only for THIS portal session
        self.session_cache = {}
        logger.info(f"🔒 [{portal_name}] Created isolated AI checker with fresh cache")
    
    def is_title_meaningful(self, titles: List[str]) -> Dict[str, bool]:
        """
        Batch analyze titles to determine if they're meaningful.
        Uses ISOLATED session cache only.
        
        Args:
            titles: List of tender titles to analyze
            
        Returns:
            Dict mapping each title to True (meaningful) or False (not meaningful)
        """
        # Check ISOLATED cache first
        uncached_titles = [t for t in titles if t not in self.session_cache]
        
        if not uncached_titles:
            logger.debug(f"🔍 [{self.portal_name}] Using {len(titles)} cached AI results")
            return {t: self.session_cache[t] for t in titles}
        
        logger.info(f"🤖 [{self.portal_name}] Calling Groq API for {len(uncached_titles)} new titles")
        
        # Prepare prompt for batch analysis
        titles_list = "\n".join([f"{i+1}. {title}" for i, title in enumerate(uncached_titles)])
        
        prompt = f"""You are analyzing tender titles from government procurement websites. Your task is to identify which titles are MEANINGFUL vs UNMEANINGFUL.

MEANINGFUL titles:
- Contain clear English words/phrases describing what the tender is about
- Examples: "Supply of Medical Equipment", "Construction of School Building", "Road Maintenance Services"

UNMEANINGFUL titles:
- Only contain reference numbers, codes, brackets, dates, or IDs
- No clear description of what the tender is for
- Examples: "[18(NIeT)/PRDD (15CFC)/ZP/T/UtF)/GTA/2025-26]", "[2026_GTA_1002593_2]", "16/SE(Prog)/SD/KMDA OF 2025-2026"

Analyze these {len(uncached_titles)} tender titles:

{titles_list}

For each title, respond with ONLY a JSON object in this exact format (no other text):
{{"1": "meaningful", "2": "unmeaningful", "3": "meaningful", ...}}

Use "meaningful" if the title contains ANY descriptive English words about what the tender is for.
Use "unmeaningful" if it's ONLY codes, numbers, brackets, or reference IDs."""

        for attempt in range(3):
            try:
                chat_response = self.client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                    response_format={"type": "json_object"},
                )
                response_text = chat_response.choices[0].message.content.strip()

                # Extract JSON (handle potential markdown formatting)
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()

                results = json.loads(response_text)

                # Update ISOLATED session cache
                for i, title in enumerate(uncached_titles, 1):
                    self.session_cache[title] = results.get(str(i), "meaningful") == "meaningful"

                logger.info(f"✅ [{self.portal_name}] AI analysis complete, cache now has {len(self.session_cache)} titles")
                return {t: self.session_cache[t] for t in titles}

            except Exception as e:
                logger.error(f"❌ [{self.portal_name}] AI filtering error (attempt {attempt+1}/3): {e}")
                time.sleep(5 * (attempt + 1))  # back off on rate limits

        # All retries failed: use a simple rule so tenders are never silently dropped.
        # (Not cached, so a later batch can try the AI again.)
        logger.warning(f"⚠️ [{self.portal_name}] Using rule-based fallback for {len(uncached_titles)} titles")

        def rule(title: str) -> bool:
            good = 0
            for w in re.findall(r"[A-Za-z]+", title or ""):
                if len(w) < 4 or not re.search(r"[aeiouAEIOU]", w):
                    continue
                if w.islower() or (w[0].isupper() and w[1:].islower()) or (w.isupper() and len(w) >= 5):
                    good += 1
            return good >= 2

        return {t: rule(t) for t in titles}

# ======================= PHASE 2: WORK DESCRIPTION EXTRACTION =======================

def fetch_work_description(details_url: str, page, portal_name: str) -> str:
    """
    ✅ ISOLATED: Navigate to tender details page and extract Work Description.
    
    HTML Pattern (consistent across West Bengal portals):
    <tr>
      <td class="td_caption"><b>Work Description</b></td>
      <td class="td_field" colspan="5"><b>THE DESCRIPTION WE WANT</b></td>
    </tr>
    
    Args:
        details_url: URL to the tender details page
        page: Playwright page instance (browser already open)
        portal_name: Name of portal (for logging)
    
    Returns:
        Work Description text or error message
    """
    try:
        # Navigate to details page
        logger.debug(f"    📄 [{portal_name}] Fetching: {details_url[:80]}...")
        page.goto(details_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(PHASE_2_DELAY)  # Avoid overwhelming the server
        
        # Strategy: Find all table rows, look for "Work Description" in td_caption
        rows = page.query_selector_all("tbody tr")
        
        for row in rows:
            caption_cell = row.query_selector("td.td_caption")
            if caption_cell:
                caption_text = caption_cell.inner_text().strip()
                if "Work Description" in caption_text:
                    # Found the Work Description row, get the value cell
                    value_cell = row.query_selector("td.td_field")
                    if value_cell:
                        description = value_cell.inner_text().strip()
                        logger.debug(f"    ✅ [{portal_name}] Found: {description[:60]}...")
                        return description
        
        logger.warning(f"    ⚠️ [{portal_name}] Work Description field not found in page")
        return "WORK_DESCRIPTION_NOT_FOUND"
        
    except Exception as e:
        logger.warning(f"    ❌ [{portal_name}] Failed to fetch work description: {str(e)[:100]}")
        return f"FETCH_ERROR: {str(e)[:100]}"

# ======================= HELPERS =======================

def extract_tender_id(title: str) -> str:
    """Extract tender ID from title (last bracket content)"""
    if not title:
        return ""
    matches = re.findall(r"\[([^\]]+)\]", title)
    return matches[-1].strip() if matches else ""

def sha256(text: str) -> str:
    """Generate SHA256 hash"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def compute_identity_hash(tender_id: str) -> str:
    """Compute unique identity hash for deduplication"""
    return sha256(tender_id.strip())

# ======================= SINGLE PORTAL SCRAPER (FULLY ISOLATED) =======================

def scrape_portal_isolated(portal_name: str, base_url: str) -> dict:
    """
    ✅ FULLY ISOLATED portal scraping session with Phase 2.
    
    Phase 1: Extract listing data + AI filter
    Phase 2: For unmeaningful tenders, fetch Work Description
    
    Each session has:
    - ✅ Own browser instance
    - ✅ Own AI checker instance (if enabled)
    - ✅ Own deduplication set
    - ✅ Own results list
    - ✅ Own statistics
    - ✅ NO shared state with other portals
    
    Returns a dict with results and statistics.
    """
    logger.info(f"{'='*60}")
    logger.info(f"🔍 Starting ISOLATED scraping session: {portal_name}")
    logger.info(f"{'='*60}")
    
    # ✅ ISOLATED: Each portal gets its own data structures
    portal_results = []
    seen_hashes = set()
    pending_tenders = []
    
    # ✅ ISOLATED: Create AI checker ONLY for this portal session
    ai_checker = None
    if USE_AI_FILTERING and MISTRAL_API_KEY:
        try:
            ai_checker = IsolatedTitleChecker(MISTRAL_API_KEY, portal_name)
        except Exception as e:
            logger.warning(f"⚠️ [{portal_name}] Failed to create AI checker: {e}")
    
    stats = {
        'portal': portal_name,
        'total_extracted': 0,
        'total_filtered': 0,
        'phase_2_success': 0,
        'phase_2_failed': 0,
        'status': 'pending',
        'error': None
    }
    
    # Determine the correct URL pattern
    if "/eprocure/app" in base_url:
        list_url = f"{base_url}?page=FrontEndListTendersbyDate&service=page"
    else:
        list_url = f"{base_url}?page=FrontEndListTendersbyDate&service=page"
    
    # ✅ ISOLATED: Create playwright instance for this portal ONLY
    with sync_playwright() as p:
        browser = None
        try:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(30000)
            
            # ==================== PHASE 1: LISTING PAGE ====================
            
            # Navigate to list page
            for attempt in range(MAX_RETRIES):
                try:
                    logger.info(f"🌐 [{portal_name}] Navigating to portal (attempt {attempt+1}/{MAX_RETRIES})")
                    page.goto(list_url, wait_until="domcontentloaded", timeout=60000)
                    time.sleep(2)
                    break
                except Exception as nav_error:
                    logger.warning(f"⚠️ [{portal_name}] Navigation failed (attempt {attempt+1}): {nav_error}")
                    if attempt == MAX_RETRIES - 1:
                        raise
            
            # Check if table exists
            table_selector = "table#table"
            if not page.query_selector(table_selector):
                logger.warning(f"⚠️ [{portal_name}] No table found on page")
                stats['status'] = 'no_data'
                return {'results': [], 'stats': stats}
            
            # Extract table rows
            rows = page.query_selector_all(f"{table_selector} tbody tr")
            logger.info(f"📊 [{portal_name}] Found {len(rows)} tender rows")
            
            for row_index, row in enumerate(rows, 1):
                try:
                    # Extract tender data
                    cells = row.query_selector_all("td")
                    if len(cells) < 6:
                        continue
                    
                    # ✅ CORRECTED CELL MAPPING based on actual HTML:
                    # cells[0] = S.No.
                    # cells[1] = e-Published Date
                    # cells[2] = Bid Submission Closing Date
                    # cells[3] = Tender Opening Date
                    # cells[4] = Title and Ref.No./Tender ID
                    # cells[5] = Organisation Chain
                    
                    sn = cells[0].inner_text().strip()
                    publish_date = cells[1].inner_text().strip()
                    deadline = cells[2].inner_text().strip()
                    tender_opening_date = cells[3].inner_text().strip()
                    title_ref = cells[4].inner_text().strip()
                    org_chain = cells[5].inner_text().strip()
                    
                    # Get details link from title cell (cells[4])
                    link_elem = cells[4].query_selector("a")
                    if not link_elem:
                        continue
                    
                    details_url = link_elem.get_attribute("href")
                    if not details_url:
                        continue
                    
                    if not details_url.startswith("http"):
                        details_url = base_url.split("/app")[0] + details_url
                    
                    # Extract tender ID and compute hash
                    tender_id = extract_tender_id(title_ref)
                    if not tender_id:
                        tender_id = title_ref  # Use full title if no ID found
                    
                    id_hash = compute_identity_hash(tender_id)
                    
                    # ✅ ISOLATED: Deduplicate within THIS portal only
                    if id_hash in seen_hashes:
                        logger.debug(f"    ⏭️ [{portal_name}] Skipping duplicate: {tender_id}")
                        continue
                    
                    seen_hashes.add(id_hash)
                    stats['total_extracted'] += 1
                    
                    # Create tender record with CORRECTED fields
                    tender = {
                        "Portal Source": portal_name,
                        "S.No.": sn,
                        "Organisation Chain": org_chain,
                        "Title and Ref.No./Tender ID": title_ref,
                        "e-Published Date": publish_date,
                        "Bid Submission Closing Date": deadline,
                        "Tender Opening Date": tender_opening_date,
                        "Details URL": details_url,
                        "Identity Hash": id_hash,
                        "Run Date": RUN_DATE,
                        "Work Description": ""  # Will be filled in Phase 2
                    }
                    
                    # Add to batch for AI processing
                    pending_tenders.append(tender)
                    
                    # Process batch when it reaches AI_BATCH_SIZE
                    if ai_checker and len(pending_tenders) >= AI_BATCH_SIZE:
                        process_isolated_batch(pending_tenders, portal_results, stats, ai_checker, portal_name)
                        pending_tenders = []
                    elif not ai_checker:
                        # No AI filtering - add directly
                        portal_results.append(tender)
                    
                    if row_index % 50 == 0:
                        logger.info(f"    Progress: {row_index}/{len(rows)} rows processed")
                
                except Exception as row_error:
                    logger.error(f"❌ [{portal_name}] Row {row_index} error: {row_error}")
                    continue
            
            # Process remaining tenders in batch
            if pending_tenders:
                if ai_checker:
                    process_isolated_batch(pending_tenders, portal_results, stats, ai_checker, portal_name)
                else:
                    portal_results.extend(pending_tenders)
            
            logger.info(f"✅ [{portal_name}] Phase 1 complete: {stats['total_extracted']} extracted, {stats['total_filtered']} filtered, {len(portal_results)} kept")
            
            # ==================== PHASE 2: FETCH WORK DESCRIPTIONS ====================
            
            if ENABLE_PHASE_2 and portal_results:
                logger.info(f"{'='*60}")
                logger.info(f"📄 [{portal_name}] Starting Phase 2: Fetching Work Descriptions")
                logger.info(f"📄 [{portal_name}] Processing {len(portal_results)} unmeaningful tenders")
                logger.info(f"{'='*60}")
                
                for idx, tender in enumerate(portal_results, 1):
                    try:
                        # Fetch Work Description from details page
                        work_desc = fetch_work_description(
                            tender['Details URL'], 
                            page, 
                            portal_name
                        )
                        
                        tender['Work Description'] = work_desc
                        
                        # Track success/failure
                        if work_desc.startswith("FETCH_ERROR") or work_desc == "WORK_DESCRIPTION_NOT_FOUND":
                            stats['phase_2_failed'] += 1
                        else:
                            stats['phase_2_success'] += 1
                        
                        # Log progress every 10 tenders
                        if idx % 10 == 0:
                            logger.info(f"    📄 [{portal_name}] Progress: {idx}/{len(portal_results)} descriptions fetched")
                        
                    except Exception as e:
                        logger.error(f"    ❌ [{portal_name}] Failed to process tender {idx}: {e}")
                        tender['Work Description'] = f"PROCESSING_ERROR: {str(e)[:100]}"
                        stats['phase_2_failed'] += 1
                
                logger.info(f"✅ [{portal_name}] Phase 2 complete: {stats['phase_2_success']} success, {stats['phase_2_failed']} failed")
            elif not ENABLE_PHASE_2:
                logger.info(f"⏭️ [{portal_name}] Phase 2 skipped (ENABLE_PHASE_2 = False)")
            
            stats['status'] = 'success'
            logger.info(f"✅ [{portal_name}] All phases completed successfully")
        
        except Exception as e:
            logger.error(f"❌ [{portal_name}] Fatal error: {e}")
            stats['status'] = 'error'
            stats['error'] = str(e)
        
        finally:
            if browser:
                browser.close()
            # ✅ ISOLATED: AI checker goes out of scope and is garbage collected
            logger.info(f"🔒 [{portal_name}] Session cleanup complete - all memory isolated")
    
    return {
        'results': portal_results,
        'stats': stats
    }

def process_isolated_batch(pending_tenders: List[dict], portal_results: List[dict], 
                          stats: dict, ai_checker: IsolatedTitleChecker, portal_name: str):
    """
    ✅ ISOLATED: Process a batch of tenders using the portal's OWN AI checker.
    No shared cache, no cross-contamination.
    """
    # Extract titles
    titles = [t["Title and Ref.No./Tender ID"] for t in pending_tenders]
    
    # Get meaningfulness results from ISOLATED checker
    meaningfulness = ai_checker.is_title_meaningful(titles)
    
    # REVERSED LOGIC: Keep UNMEANINGFUL titles (codes/IDs only)
    for tender in pending_tenders:
        title = tender["Title and Ref.No./Tender ID"]
        is_meaningful = meaningfulness.get(title, False)
        
        if not is_meaningful:  # KEEP if unmeaningful
            portal_results.append(tender)
            logger.debug(f"    ✅ [{portal_name}] Kept unmeaningful: {title[:60]}...")
        else:  # FILTER OUT if meaningful
            stats['total_filtered'] += 1
            logger.debug(f"    🚫 [{portal_name}] Filtered meaningful: {title[:60]}...")

# ======================= PARALLEL ORCHESTRATION =======================

def run_parallel_scraping():
    """
    ✅ ISOLATED: Each portal runs in complete isolation.
    Results are merged AFTER completion, not during.
    """
    logger.info(f"🚀 Starting ISOLATED parallel tender scraping at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if USE_AI_FILTERING:
        logger.info(f"🤖 AI-based title filtering: ENABLED (Groq)")
        logger.info(f"🔒 Isolation mode: Each portal gets its own AI checker instance")
        logger.info(f"🎯 Strategy: KEEP tenders with code/ID-only titles (need investigation)")
        logger.info(f"🚫 Strategy: FILTER OUT tenders with clear descriptive titles")
        logger.info(f"📦 Batch size: {AI_BATCH_SIZE} titles per API call")
    else:
        logger.info(f"🤖 AI-based title filtering: DISABLED (all tenders will be included)")
    
    if ENABLE_PHASE_2:
        logger.info(f"📄 Phase 2 (Work Description extraction): ENABLED")
        logger.info(f"⏱️ Delay between detail pages: {PHASE_2_DELAY} seconds")
    else:
        logger.info(f"📄 Phase 2 (Work Description extraction): DISABLED")
    
    logger.info(f"🌐 Scanning {len(PORTALS)} portals")
    logger.info(f"⚡ Max concurrent sessions: {MAX_CONCURRENT_PORTALS}")
    logger.info(f"💾 RAM usage will be ~{MAX_CONCURRENT_PORTALS * 200}MB (approx)\n")
    
    # ✅ ISOLATED: Collect results AFTER all portals complete
    completed_results = {}
    results_lock = Lock()
    
    def scrape_with_timeout(portal_name, base_url):
        """Wrapper to add timeout and error handling"""
        try:
            result = scrape_portal_isolated(portal_name, base_url)
            with results_lock:
                completed_results[portal_name] = result
            return f"✅ {portal_name}"
        except Exception as e:
            logger.error(f"❌ {portal_name} failed: {e}")
            with results_lock:
                completed_results[portal_name] = {
                    'results': [],
                    'stats': {
                        'portal': portal_name,
                        'total_extracted': 0,
                        'total_filtered': 0,
                        'phase_2_success': 0,
                        'phase_2_failed': 0,
                        'status': 'error',
                        'error': str(e)
                    }
                }
            return f"❌ {portal_name}"
    
    # Execute in parallel with ISOLATED sessions
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_PORTALS) as executor:
        futures = {
            executor.submit(scrape_with_timeout, name, url): name
            for name, url in PORTALS.items()
        }
        
        for future in as_completed(futures, timeout=THREAD_TIMEOUT):
            portal = futures[future]
            try:
                result = future.result(timeout=THREAD_TIMEOUT)
                logger.info(result)
            except Exception as e:
                logger.error(f"❌ {portal} timeout or error: {e}")
    
    # ✅ ISOLATED: Merge results AFTER all sessions complete
    logger.info(f"\n🔄 Merging results from {len(completed_results)} completed sessions...")
    
    all_results = []
    all_stats = []
    
    for portal_name, portal_data in completed_results.items():
        all_results.extend(portal_data['results'])
        all_stats.append(portal_data['stats'])
    
    # ======================= SAVE RESULTS =======================
    
    logger.info(f"\n{'='*60}")
    logger.info("📊 FINAL SUMMARY")
    logger.info(f"{'='*60}")
    
    total_extracted = sum(s['total_extracted'] for s in all_stats)
    total_filtered = sum(s['total_filtered'] for s in all_stats)
    total_kept = len(all_results)
    phase_2_success = sum(s.get('phase_2_success', 0) for s in all_stats)
    phase_2_failed = sum(s.get('phase_2_failed', 0) for s in all_stats)
    
    logger.info(f"Total tenders extracted: {total_extracted}")
    logger.info(f"Total tenders filtered (meaningful): {total_filtered}")
    logger.info(f"Total tenders kept (unmeaningful): {total_kept}")
    
    if ENABLE_PHASE_2:
        logger.info(f"Phase 2 - Work Descriptions fetched: {phase_2_success}")
        logger.info(f"Phase 2 - Failed to fetch: {phase_2_failed}")
    
    logger.info(f"Portals succeeded: {sum(1 for s in all_stats if s['status'] == 'success')}/{len(PORTALS)}")
    logger.info(f"Portals failed: {sum(1 for s in all_stats if s['status'] == 'error')}")
    
    # Create DataFrame
    if all_results:
        df = pd.DataFrame(all_results)
        
        # Reorder columns for better readability (CORRECTED column names)
        column_order = [
            "Portal Source",
            "S.No.",
            "Organisation Chain",
            "Title and Ref.No./Tender ID",
            "Work Description",  # Phase 2 enrichment
            "e-Published Date",
            "Bid Submission Closing Date",
            "Tender Opening Date",
            "Details URL",
            "Identity Hash",
            "Run Date"
        ]
        
        # Only include columns that exist
        column_order = [col for col in column_order if col in df.columns]
        df = df[column_order]
        
        # Save to Excel
        try:
            df.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')
            logger.info(f"\n✅ Results saved to: {OUTPUT_FILE}")
            logger.info(f"📁 Total records: {len(df)}")
        except Exception as e:
            logger.error(f"❌ Failed to save Excel: {e}")
            # Fallback to CSV
            csv_file = OUTPUT_FILE.replace('.xlsx', '.csv')
            df.to_csv(csv_file, index=False)
            logger.info(f"✅ Saved to CSV instead: {csv_file}")
    else:
        logger.warning("⚠️ No results to save!")
    
    # Save stats
    stats_df = pd.DataFrame(all_stats)
    stats_file = f"scraping_stats_{RUN_DATE}.xlsx"
    stats_df.to_excel(stats_file, index=False, engine='openpyxl')
    logger.info(f"📊 Statistics saved to: {stats_file}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🏁 Scraping completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🔒 All sessions were completely isolated - zero data bleed")
    logger.info(f"{'='*60}\n")

# ======================= MAIN =======================

if __name__ == "__main__":
    run_parallel_scraping()