import asyncio
from playwright.async_api import async_playwright
import os

async def test_launch():
    print("Testing playwright launch...")
    async with async_playwright() as p:
        try:
            # Try to launch chrome
            browser = await p.chromium.launch(headless=True, channel="chrome")
            print("Successfully launched Chrome!")
            page = await browser.new_page()
            await page.goto("https://www.google.com")
            await page.screenshot(path="brain/test_playwright.png")
            print("Screenshot saved to brain/test_playwright.png")
            await browser.close()
        except Exception as e:
            print(f"Failed to launch Chrome: {e}")
            try:
                print("Trying fallback to bundled chromium...")
                browser = await p.chromium.launch(headless=True)
                print("Successfully launched bundled Chromium!")
                await browser.close()
            except Exception as e2:
                print(f"Failed to launch bundled Chromium: {e2}")

if __name__ == "__main__":
    asyncio.run(test_launch())
