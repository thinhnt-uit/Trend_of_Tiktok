"""
Crawler for TikTok Explore trending videos.
Navigates to tiktok.com/explore, clicks through category tabs,
intercepts the internal API responses, and saves raw JSON.
"""

import argparse
import io
import json
import os
import sys
import time
from datetime import datetime

from playwright.sync_api import Response, sync_playwright

# Fix Windows console encoding for Unicode output
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Category tab name → TikTok internal categoryType ID
CATEGORIES = {
    "All": 123,
    "Singing & Dancing": 120,
    "Comedy": 119,
    "Sports": 104,
    "Anime & Comics": 112,
    "Relationship": 100,
    "Shows": 107,
    "Daily Life": 105,
}


def crawl_explore(categories: list[str] | None = None, scroll_rounds: int = 3) -> dict:
    """
    Launch a headless browser, visit tiktok.com/explore,
    click each category tab, scroll to load more videos,
    and collect all intercepted API items.
    """
    if categories is None:
        categories = list(CATEGORIES.keys())

    collected_items = []
    video_ids_seen = set()
    all_api_responses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        def handle_response(response: Response):
            url = response.url
            if "api/explore/item_list" not in url:
                return
            try:
                from urllib.parse import parse_qs, urlparse

                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                url_cat_ids = query_params.get("categoryType") or query_params.get(
                    "categorytype"
                )

                data = response.json()
                all_api_responses.append(data)
                items = data.get("itemList", [])
                for item in items:
                    vid = item.get("id")
                    if vid and vid not in video_ids_seen:
                        video_ids_seen.add(vid)

                        # Determine category: prioritize URL query parameter, fallback to item CategoryType
                        cat_id = None
                        if url_cat_ids:
                            try:
                                cat_id = int(url_cat_ids[0])
                            except ValueError:
                                pass
                        if cat_id is None:
                            cat_id = item.get("CategoryType")

                        cat_name = None
                        for name, cid in CATEGORIES.items():
                            if cid == cat_id:
                                cat_name = name
                                break
                        item["_category_name"] = cat_name or "Unknown"
                        item["_category_id"] = cat_id
                        collected_items.append(item)
            except Exception:
                pass

        page.on("response", handle_response)

        print("[INFO] Navigating to https://www.tiktok.com/explore ...")
        page.goto(
            "https://www.tiktok.com/explore",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        time.sleep(8)

        for cat_name in categories:
            if cat_name not in CATEGORIES:
                print(f"[WARNING] Unknown category '{cat_name}', skipping.")
                continue

            # Scroll back to top so category tabs are in viewport
            page.evaluate("window.scrollTo(0, 0);")
            time.sleep(1)

            print(f"\n[INFO] Clicking category tab: '{cat_name}' ...")
            try:
                locator = page.locator(f"text='{cat_name}'").first
                locator.scroll_into_view_if_needed()
                time.sleep(0.5)
                locator.click(force=True)
                time.sleep(5)
            except Exception as e:
                print(f"[WARNING] Could not click tab '{cat_name}': {e}")
                continue

            # Scroll to trigger lazy loading of more videos
            for i in range(scroll_rounds):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)

            print(f"[INFO] Videos collected so far: {len(collected_items)}")

        browser.close()

    print(f"\n[INFO] Total unique videos collected: {len(collected_items)}")

    result = {
        "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "categories_crawled": categories,
        "total_videos": len(collected_items),
        "item_list": collected_items,
    }
    return result


def write_raw_json(raw_dir: str, today_str: str, raw_data: dict) -> str:
    """Write crawled data to a local JSON file."""
    os.makedirs(raw_dir, exist_ok=True)
    output_file = os.path.join(raw_dir, f"raw_explore_{today_str}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    return output_file


def upload_raw_json(s3_key: str, raw_data: dict):
    """Upload raw JSON to S3 / MinIO."""
    try:
        from src.utils.s3 import upload_json_to_s3

        upload_json_to_s3(s3_key, raw_data)
    except Exception as e:
        print(f"[WARNING] Cannot upload to S3: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="TikTok Explore Trending Video Crawler"
    )
    parser.add_argument(
        "--categories",
        type=str,
        default=None,
        help="Comma-separated category names to crawl (default: all)",
    )
    parser.add_argument(
        "--scroll-rounds",
        type=int,
        default=3,
        help="Number of scroll-down rounds per category tab (default: 3)",
    )
    args = parser.parse_args()

    cats = None
    if args.categories:
        cats = [c.strip() for c in args.categories.split(",") if c.strip()]

    today_str = datetime.now().strftime("%Y-%m-%d")
    raw_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), f"../data/raw/tiktok_explore/{today_str}"
        )
    )

    print("=" * 60)
    print(f"TikTok Explore Crawler — {today_str}")
    print(f"Categories: {cats or 'ALL'}")
    print("=" * 60)

    raw_data = crawl_explore(categories=cats, scroll_rounds=args.scroll_rounds)

    # Save locally
    output_file = write_raw_json(raw_dir, today_str, raw_data)
    print(f"[INFO] Raw JSON saved: {output_file}")

    # Upload to S3
    s3_key = f"tiktok_explore/{today_str}/raw_explore_{today_str}.json"
    upload_raw_json(s3_key, raw_data)

    # Summary
    print("\n" + "=" * 60)
    print(f"Total videos: {raw_data['total_videos']}")
    items = raw_data.get("item_list", [])
    for item in items[:3]:
        vid = item.get("id", "N/A")
        desc = (item.get("desc") or "")[:50]
        cat = item.get("_category_name", "N/A")
        plays = item.get("stats", {}).get("playCount", 0)
        print(f"  [{cat}] id={vid} | plays={plays:,} | {desc}")
    print("=" * 60)


if __name__ == "__main__":
    main()
