from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page()

    page.goto(
        "https://www.bseindia.com",
        wait_until="networkidle"
    )

    print("BSE loaded")

    time.sleep(1)

    print("Pressing ESC...")

    page.keyboard.press("Escape")

    time.sleep(1)

    input("Press Enter to close...")

    browser.close()