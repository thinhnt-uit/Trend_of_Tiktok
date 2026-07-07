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

        captured_data = []

        def handle_response(response: Response):
            url = response.url
            if "api/explore/item_list" in url:
                print(f"[API FOUND] Status: {response.status} | URL: {url[:100]}...")
                try:
                    data = response.json()
                    captured_data.append(data)
                    print("Parse success!")
                except Exception as e:
                    print(f"Failed to parse JSON: {e}")

        page.on("response", handle_response)

        target_url = "https://www.tiktok.com/explore"
        print(f"Navigating to {target_url}...")
        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            print("Page loaded, waiting for responses...")
        except Exception as e:
            print(f"Navigation failed: {e}")

        # Scroll down a few times to get more API responses
        for i in range(3):
            print(f"Scrolling down {i+1}...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)

        print(f"\nCaptured {len(captured_data)} explore API responses.")

        if captured_data:
            # Let's inspect the first response
            first_resp = captured_data[0]
            print(f"Response root keys: {list(first_resp.keys())}")

            # Usually TikTok items are under "itemList" or similar
            items = first_resp.get("itemList") or first_resp.get("items") or []
            print(f"Number of items in first response: {len(items)}")

            if items:
                print(f"\nKeys of the first video item: {list(items[0].keys())}")
                print("\nSample item detail structure (first item):")
                # Save the full sample item to a JSON file to inspect
                with open("sample_item.json", "w", encoding="utf-8") as f:
                    json.dump(items[0], f, ensure_ascii=False, indent=2)
                print("Saved first item to sample_item.json")

                # Check for video, stats, desc, and challenge (hashtags)
                item = items[0]
                print(f"ID: {item.get('id') or item.get('desc')}")
                print(f"Description: {item.get('desc')}")

                # Stats
                stats = item.get("stats", {})
                print(f"Stats: {stats}")

                # Video details
                video = item.get("video", {})
                print(f"Video Keys: {list(video.keys())}")
                print(f"Video Duration: {video.get('duration')}")
                print(f"Video Cover: {video.get('cover')}")

                # Author
                author = item.get("author", {})
                print(f"Author: {author.get('uniqueId')} ({author.get('nickname')})")

                # Challenges (hashtags)
                challenges = item.get("challenges", [])
                print(f"Challenges (hashtags count): {len(challenges)}")
                if challenges:
                    print(f"First challenge: {challenges[0]}")

        browser.close()


if __name__ == "__main__":
    run()
