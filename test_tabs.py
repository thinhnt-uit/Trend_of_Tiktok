import json
import time

from playwright.sync_api import Response, sync_playwright


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        category_calls = {}

        def handle_response(response: Response):
            url = response.url
            if "api/explore/item_list" in url:
                try:
                    import urllib.parse as urlparse

                    parsed = urlparse.urlparse(url)
                    params = urlparse.parse_qs(parsed.query)
                    cat_type = params.get("categoryType", [None])[0]
                    if cat_type:
                        print(
                            f"   [API] categoryType={cat_type} for URL: {url[:80]}..."
                        )
                except Exception as e:
                    pass

        page.on("response", handle_response)

        target_url = "https://www.tiktok.com/explore"
        print(f"Navigating to {target_url}...")
        page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)

        tabs = [
            "All",
            "Singing & Dancing",
            "Comedy",
            "Sports",
            "Anime & Comics",
            "Relationship",
            "Shows",
            "Lipsync",
            "Daily Life",
        ]

        for tab in tabs:
            print(f"\nAttempting click tab: '{tab}'...")
            try:
                # Use force=True to bypass hit interceptors
                locator = page.locator(f"text='{tab}'").first
                if locator.is_visible():
                    locator.click(force=True)
                    print(f"Clicked tab '{tab}' successfully!")
                    time.sleep(5)
                else:
                    print(
                        f"Tab '{tab}' is not visible. Let's try matching case-insensitive."
                    )
                    # Try text case-insensitive or regex
                    locator = page.locator(f"text={tab}").first
                    if locator.is_visible():
                        locator.click(force=True)
                        print(f"Clicked tab '{tab}' successfully!")
                        time.sleep(5)
                    else:
                        print(f"Tab '{tab}' not found or not visible.")
            except Exception as e:
                print(f"Error clicking tab '{tab}': {e}")

        browser.close()


if __name__ == "__main__":
    run()
