from playwright.sync_api import sync_playwright
from pathlib import Path
from urllib.parse import unquote, urljoin
from datetime import datetime
import html as html_lib
import time
import re
import requests
import csv
import json

COMPANY = input("Company Name: ").strip()

# OUTPUT = Path("output")
# OUTPUT.mkdir(exist_ok=True)
BASE_OUTPUT = Path("output")
BASE_OUTPUT.mkdir(exist_ok=True)


def save_html(name, page, output_dir):

    file = output_dir / f"{name}.html"

    with open(file, "w", encoding="utf-8") as f:
        f.write(page.content())

    print(f"[SAVED] {file}")


MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12
}


def parse_date_score(text):

    text = unquote(
        html_lib.unescape(text or "")
    )

    candidates = []

    for day, month, year in re.findall(
        r"\b(\d{1,2})[-/ ]([A-Za-z]{3,9})[-/ ](20\d{2})\b",
        text,
        re.IGNORECASE
    ):

        month_no = MONTHS.get(month[:3].lower())

        if month_no:
            candidates.append(
                datetime(int(year), month_no, int(day))
            )

    for day, month, year in re.findall(
        r"\b(\d{1,2})[-/](\d{1,2})[-/](20\d{2})\b",
        text
    ):

        day_no = int(day)
        month_no = int(month)

        if 1 <= day_no <= 31 and 1 <= month_no <= 12:
            candidates.append(
                datetime(int(year), month_no, day_no)
            )

    for month, year in re.findall(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+(20\d{2})\b",
        text,
        re.IGNORECASE
    ):

        month_no = MONTHS.get(month[:3].lower())

        if month_no:
            candidates.append(
                datetime(int(year), month_no, 1)
            )

    return max(candidates) if candidates else datetime.min


def pick_latest_xbrl(page):

    links = []

    for i, anchor in enumerate(
        page.locator("a[href*='XBRLFILES']").all()
    ):

        href = anchor.get_attribute("href")

        if not href:
            continue

        row_text = ""

        try:
            row_text = anchor.evaluate(
                """(e) => {
                    const row = e.closest('tr');
                    return row ? row.innerText : e.innerText;
                }"""
            )
        except Exception:
            row_text = anchor.inner_text()

        url = urljoin(
            "https://www.bseindia.com",
            href
        )

        score = parse_date_score(
            f"{row_text} {url}"
        )

        links.append(
            {
                "url": url,
                "row_text": row_text,
                "score": score,
                "index": i
            }
        )

    if not links:
        return None, []

    links.sort(
        key=lambda x: (
            x["score"],
            -x["index"]
        ),
        reverse=True
    )

    return links[0], links


def latest_quarter_label(page):

    html = page.content()

    labels = sorted(
        set(
            re.findall(
                r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+20\d{2}\b",
                html,
                re.IGNORECASE
            )
        ),
        key=parse_date_score,
        reverse=True
    )

    return labels[0] if labels else None


def save_latest_xbrl(page, name, output_dir):

    try:

        selected, matches = pick_latest_xbrl(page)

        print(f"{name}: Found {len(matches)} XBRL URLs")

        if not selected:
            return

        xbrl_url = selected["url"]

        print(f"\n{name} XBRL URL:")
        print(xbrl_url)
        print(f"{name} XBRL source row: {selected['row_text']}")

        xbrl_page = page.context.new_page()

        xbrl_page.goto(
            xbrl_url,
            wait_until="networkidle"
        )

        time.sleep(3)

        save_html(
            f"{name}_xbrl",
            xbrl_page,
            output_dir
        )

        xbrl_page.close()

    except Exception as e:

        print(
            f"{name} XBRL Error:",
            e
        )

    try:

        x = page.locator(
            "text=XBRL"
        ).first

        print(f"\n{name} XBRL HTML:")

        print(
            x.evaluate(
                "(e) => e.outerHTML"
            )
        )

    except Exception as e:

        print(
            f"{name} XBRL HTML Error:",
            e
        )


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    context = browser.new_context()

    page = context.new_page()

    # --------------------------------------------------
    # HOME
    # --------------------------------------------------

    page.goto(
        "https://www.bseindia.com",
        wait_until="networkidle"
    )

    time.sleep(3)

    try:
        page.keyboard.press("Escape")
    except Exception as e:
        print("Popup close skipped:", e)

    # --------------------------------------------------
    # SEARCH COMPANY
    # --------------------------------------------------

    search_box = page.get_by_placeholder(
        "Enter Security Name / Code / ID / ISIN"
    )

    search_box.click()

    search_box.fill(COMPANY)

    time.sleep(1)

    page.keyboard.press("ArrowDown")

    time.sleep(1)

    page.keyboard.press("Enter")

    page.wait_for_url(
        "**/stock-share-price/**",
        timeout=30000
    )

    company_url = page.url

    print("\nCompany URL:")
    print(company_url)

    safe_company_name = re.sub(
    r'[<>:"/\\|?*]',
    "_",
    COMPANY.strip()
    )

    company_folder = BASE_OUTPUT / safe_company_name

    company_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    print(f"\nOutput Folder: {company_folder}")
    # --------------------------------------------------
    # FINANCE
    # --------------------------------------------------

    try:

        page.goto(
            company_url +
            "/integrated-filing-finance",
            wait_until="networkidle"
        )

        time.sleep(3)

        save_html(
            "finance_listing",
            page,
            company_folder
        )

        save_latest_xbrl(
            page,
            "finance",
            company_folder
        )

    except Exception as e:

        print(
            "Finance Error:",
            e
        )

    # --------------------------------------------------
    # GOVERNANCE
    # --------------------------------------------------

    try:

        page.goto(
            company_url +
            "/flag/7/corporate-governance",
            wait_until="networkidle"
        )

        time.sleep(5)

        save_html(
            "governance_listing",
            page,
            company_folder
        )

        print("\nOpening latest governance quarter...")

        quarter = latest_quarter_label(page)

        if not quarter:
            raise RuntimeError(
                "No governance quarter label found on listing page"
            )

        print(f"Latest governance quarter: {quarter}")

        page.get_by_text(
            quarter,
            exact=True
        ).first.click()

        page.wait_for_load_state(
            "networkidle"
        )

        time.sleep(3)

        print(
            "\nGovernance Detail URL:"
        )

        print(page.url)

        save_html(
            "governance_detail",
            page,
            company_folder
        )

    except Exception as e:

        print(
            "Governance Error:",
            e
        )

    # --------------------------------------------------
    # RETURN TO COMPANY PAGE
    # --------------------------------------------------

    try:

        page.goto(
            company_url,
            wait_until="networkidle"
        )

        time.sleep(2)

    except Exception as e:
        print("Return to company page before shareholding failed:", e)

    # --------------------------------------------------
    # SHAREHOLDING
    # --------------------------------------------------

    try:

        page.get_by_role(
            "link",
            name="Shareholding Pattern",
            exact=True
        ).click()

        time.sleep(3)

        save_html(
            "shareholding_listing",
            page,
            company_folder  
        )

        save_latest_xbrl(
            page,
            "shareholding",
            company_folder
        )

    except Exception as e:

        print(
            "Shareholding Error:",
            e
        )

    # --------------------------------------------------
    # RETURN TO COMPANY PAGE
    # --------------------------------------------------

    try:

        page.goto(
            company_url,
            wait_until="networkidle"
        )

        time.sleep(2)

    except Exception as e:
        print("Return to company page before BRSR failed:", e)

    # --------------------------------------------------
    # BRSR
    # --------------------------------------------------

    try:

        page.get_by_text(
            "BRSR",
            exact=False
        ).click()

        time.sleep(3)

        save_html(
            "brsr_listing",
            page,
            company_folder
        )

        save_latest_xbrl(
            page,
            "brsr",
            company_folder
        )

    except Exception as e:

        print(
            "BRSR Error:",
            e
        )

    # --------------------------------------------------
    # CRA
    # --------------------------------------------------

    try:

        page.goto(
            company_url +
            "/disclosures-intermediaries-ratingaction",
            wait_until="networkidle"
        )

        time.sleep(3)

        save_html(
            "cra_table",
            page,
            company_folder
        )

    except Exception as e:

        print(
            "CRA Error:",
            e
        )

    # --------------------------------------------------
    # ERP
    # --------------------------------------------------

    try:

        page.goto(
            company_url +
            "/intermediaries-erp",
            wait_until="networkidle"
        )

        time.sleep(3)

        save_html(
            "erp_table",
            page,
            company_folder
        )

    except Exception as e:

        print(
            "ERP Error:",
            e
        )

 # --------------------------------------------------
# CREDIT RATING DETAILS
# --------------------------------------------------

    try:

        # Return to company page
        page.goto(
            company_url,
            wait_until="networkidle"
        )

        time.sleep(2)

        # Open "Centralised Database"
        page.locator("a[data-bs-target='#centralisedDatabase']").click()

        time.sleep(1)

        # Click "Credit Rating Details"
        page.locator(
            "a[data-page='Centralizeddb-Creditratingdetails']"
        ).click()

        page.wait_for_load_state("networkidle")

        time.sleep(2)

       # Save page
        save_html(
        "credit_rating_page",
        page,
        company_folder
    )

    # ----------------------------
    # Download CSV
    # ----------------------------

        download_link = page.locator(
        "a[aria-label='Download file']"
    )

        if download_link.count() == 0:

            print("No download button found.")

        else:

            href = download_link.get_attribute("href")

            print("\nDownload URL:")
            print(href)

            if href.startswith("/"):

                href = "https://www.bseindia.com" + href

            response = page.context.request.get(
            href,
            headers={
                "Referer": "https://www.bseindia.com/",
                "Accept": "text/csv,*/*"
                    }
                )

        

            csv_path = company_folder / "credit_rating.csv"

            with open(csv_path, "wb") as f:
                f.write(response.body())

            print(f"[SAVED] {csv_path}")


            json_path = company_folder / "credit_rating.json"

            with open(csv_path, newline="", encoding="utf-8-sig") as f:
               rows = list(csv.DictReader(f))

            if len(rows) == 0:

                credit_rating = {
                "status": "empty",
                "records": []
            }

            else:

                credit_rating = {
             "status": "success",
                "records": rows
            }

            with open(json_path, "w", encoding="utf-8") as f:

                json.dump(
                credit_rating,
                f,
                indent=4,
                ensure_ascii=False
            )

            print(f"[SAVED] {json_path}")
        
    except Exception as e:

        print("Credit Rating Error:", e)
        
    print(
        """
Expected files:

finance_listing.html
finance_xbrl.html

governance_listing.html
governance_detail.html

shareholding_listing.html
shareholding_xbrl.html

brsr_listing.html
brsr_xbrl.html

cra_table.html
erp_table.html

credit_rating.csv
credit_rating.json
"""
    )

    input(
        "\nPress Enter to close..."
    )

    browser.close()
