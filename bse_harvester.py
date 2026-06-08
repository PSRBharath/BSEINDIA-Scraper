from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import re

COMPANY = input("Company Name: ").strip()

OUTPUT = Path("output")
OUTPUT.mkdir(exist_ok=True)


def save_html(name, page):

    file = OUTPUT / f"{name}.html"

    with open(file, "w", encoding="utf-8") as f:
        f.write(page.content())

    print(f"[SAVED] {file}")


def save_latest_xbrl(page, name):

    try:

        html = page.content()

        matches = re.findall(
            r'href="([^"]*XBRLFILES[^"]*)"',
            html,
            re.IGNORECASE
        )

        print(f"{name}: Found {len(matches)} XBRL URLs")

        if not matches:
            return

        xbrl_url = matches[0]

        if xbrl_url.startswith("/"):
            xbrl_url = (
                "https://www.bseindia.com"
                + xbrl_url
            )

        print(f"\n{name} XBRL URL:")
        print(xbrl_url)

        xbrl_page = page.context.new_page()

        xbrl_page.goto(
            xbrl_url,
            wait_until="networkidle"
        )

        time.sleep(3)

        save_html(
            f"{name}_xbrl",
            xbrl_page
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
    except:
        pass

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
            page
        )

        save_latest_xbrl(
            page,
            "finance"
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
            page
        )

        print("\nOpening latest governance quarter...")

        page.get_by_text(
            "Mar 2026"
        ).click()

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
            page
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

    except:
        pass

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
            page
        )

        save_latest_xbrl(
            page,
            "shareholding"
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

    except:
        pass

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
            page
        )

        save_latest_xbrl(
            page,
            "brsr"
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
            page
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
            page
        )

    except Exception as e:

        print(
            "ERP Error:",
            e
        )

    print("\nDONE")

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
"""
    )

    input(
        "\nPress Enter to close..."
    )

    browser.close()