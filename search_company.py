from playwright.sync_api import sync_playwright
import time

COMPANY = "RELIANCE"

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page()

    page.goto(
        "https://www.bseindia.com",
        wait_until="networkidle"
    )

    time.sleep(1)

    # Close popup
    page.keyboard.press("Escape")

    time.sleep(1)

    # Search company
    search_box = page.get_by_placeholder(
        "Enter Security Name / Code / ID / ISIN"
    )

    search_box.click()
    search_box.fill(COMPANY)

    time.sleep(1)

    # Select first suggestion
    page.keyboard.press("ArrowDown")

    time.sleep(1)

    page.keyboard.press("Enter")

    # Wait for navigation to company page
    page.wait_for_url(
        "**/stock-share-price/**",
        timeout=30000
    )

    print("\nCompany page opened!")
    print("URL:", page.url)

    input("\nPress Enter to close...")

    browser.close()