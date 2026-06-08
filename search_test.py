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

    page.keyboard.press("Escape")

    print("Popup closed")

    time.sleep(2)

    page.pause()

    input("Browser paused. Open Inspector and find search box. Press Enter when done.")

    browser.close()