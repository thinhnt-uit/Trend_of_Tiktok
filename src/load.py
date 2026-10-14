"""
Load raw TikTok Explore JSON into PostgreSQL staging table.
Reads from S3/MinIO (with local fallback) and performs UPSERT.
"""

import argparse
import io
import json
import os
import sys
from datetime import datetime

import psycopg2
from psycopg2.extras import Json, execute_values

# Fix Windows console encoding for Unicode output
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.db import get_db_connection


def create_staging_table(conn):
    """Create the staging table if it does not exist."""
    create_sql = """
    CREATE TABLE IF NOT EXISTS stg_tiktok_explore_videos (
        id              VARCHAR(50),
        crawled_date    DATE,
        video_desc      TEXT,
        author_id       VARCHAR(50),
        author_username VARCHAR(100),
        author_nickname VARCHAR(200),
        category_id     INT,
        category_name   VARCHAR(100),
        play_count      BIGINT,
        like_count      BIGINT,
        comment_count   BIGINT,
        share_count     BIGINT,
        collect_count   BIGINT,
        create_time     BIGINT,
        video_info      JSONB,
        music_info      JSONB,
        hashtags        JSONB,
        crawled_at      TIMESTAMP WITH TIME ZONE,
        loaded_at       TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        author_followers BIGINT,
        author_verified  BOOLEAN,
        is_ad            BOOLEAN,
        music_play_url   TEXT,
        stickers         JSONB,
        raw_item         JSONB,
        PRIMARY KEY (id, crawled_date)
    );
    """
    with conn.cursor() as cur:
        cur.execute(create_sql)
    conn.commit()
    print("[INFO] `stg_tiktok_explore_videos` table is ready.")


def read_validated_json(date_str: str):
    """Read validated JSON from S3/MinIO, falling back to local disk."""
    s3_key = f"tiktok_explore/{date_str}/validated_explore_{date_str}.json"

    try:
        from src.utils.s3 import read_json_from_s3

        print(f"[INFO] Reading from S3: s3://tiktok-explore-raw/{s3_key}")
        data = read_json_from_s3(s3_key)
        print("[SUCCESS] Read validated data from S3/MinIO.")
        return data
    except Exception as e:
        print(f"[WARNING] Cannot read from S3: {e}")

    # Fallback to local file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.abspath(
        os.path.join(
            current_dir,
            f"../data/raw/tiktok_explore/{date_str}/validated_explore_{date_str}.json",
        )
    )
    if not os.path.exists(file_path):
        print(f"[ERROR] Local validated file not found: {file_path}")
        return None

    print(f"[INFO] Fallback: reading local file {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_raw_to_staging(date_str: str):
    """Load validated JSON items into the PostgreSQL staging table using bulk UPSERT."""
    raw_data = read_validated_json(date_str)
    if not raw_data:
        raise ValueError(f"No validated data found to load for date {date_str}.")

    items = raw_data.get("item_list", [])
    if not items:
        raise ValueError("No items found in validated data.")

    crawled_at_str = raw_data.get("crawled_at")
    try:
        crawled_at_dt = datetime.strptime(crawled_at_str, "%Y-%m-%d %H:%M:%S")
        crawled_date = crawled_at_dt.date()
    except Exception:
        crawled_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        crawled_at_dt = datetime.now()

    print(f"[INFO] Preparing {len(items)} videos for bulk load into Postgres ...")
    conn = get_db_connection()

    try:
        create_staging_table(conn)

        upsert_sql = """
        INSERT INTO stg_tiktok_explore_videos (
            id, crawled_date, video_desc, author_id, author_username,
            author_nickname, category_id, category_name,
            play_count, like_count, comment_count, share_count, collect_count,
            create_time, video_info, music_info, hashtags, crawled_at,
            author_followers, author_verified, is_ad, music_play_url, stickers, raw_item
        ) VALUES %s
        ON CONFLICT (id, crawled_date)
        DO UPDATE SET
            video_desc      = EXCLUDED.video_desc,
            author_id       = EXCLUDED.author_id,
            author_username = EXCLUDED.author_username,
            author_nickname = EXCLUDED.author_nickname,
            category_id     = EXCLUDED.category_id,
            category_name   = EXCLUDED.category_name,
            play_count      = EXCLUDED.play_count,
            like_count      = EXCLUDED.like_count,
            comment_count   = EXCLUDED.comment_count,
            share_count     = EXCLUDED.share_count,
            collect_count   = EXCLUDED.collect_count,
            create_time     = EXCLUDED.create_time,
            video_info      = EXCLUDED.video_info,
            music_info      = EXCLUDED.music_info,
            hashtags        = EXCLUDED.hashtags,
            crawled_at      = EXCLUDED.crawled_at,
            author_followers = EXCLUDED.author_followers,
            author_verified  = EXCLUDED.author_verified,
            is_ad            = EXCLUDED.is_ad,
            music_play_url   = EXCLUDED.music_play_url,
            stickers         = EXCLUDED.stickers,
            raw_item         = EXCLUDED.raw_item,
            loaded_at       = CURRENT_TIMESTAMP;
        """

        records = []
        for item in items:
            vid = item.get("id")
            if not vid:
                continue

            stats = item.get("stats", {})
            author = item.get("author", {})
            author_stats = item.get("authorStats", {})
            video = item.get("video", {})
            music = item.get("music", {})
            challenges = item.get("challenges", [])
            hashtag_titles = [c.get("title") for c in challenges if c.get("title")]
            effect_stickers = item.get("effectStickers", [])

            records.append(
                (
                    str(vid),
                    crawled_date,
                    item.get("desc"),
                    author.get("id"),
                    author.get("uniqueId"),
                    author.get("nickname"),
                    item.get("_category_id"),
                    item.get("_category_name"),
                    stats.get("playCount"),
                    stats.get("diggCount"),
                    stats.get("commentCount"),
                    stats.get("shareCount"),
                    stats.get("collectCount"),
                    item.get("createTime") or (int(vid) >> 32 if str(vid).isdigit() else None),
                    Json(
                        {
                            "duration": video.get("duration"),
                            "cover": video.get("cover"),
                            "playAddr": video.get("playAddr"),
                            "downloadAddr": video.get("downloadAddr"),
                            "width": video.get("width"),
                            "height": video.get("height"),
                            "ratio": video.get("ratio"),
                            "videoID": video.get("videoID"),
                        }
                    ),
                    Json(
                        {
                            "id": music.get("id"),
                            "title": music.get("title"),
                            "authorName": music.get("authorName"),
                            "duration": music.get("duration"),
                            "original": music.get("original"),
                        }
                    ),
                    Json(hashtag_titles),
                    crawled_at_dt,
                    author_stats.get("followerCount", 0),
                    author.get("verified", False),
                    item.get("isAd", False),
                    music.get("playUrl"),
                    Json(effect_stickers),
                    Json(item),
                )
            )

        if records:
            with conn.cursor() as cur:
                execute_values(cur, upsert_sql, records, page_size=1000)
            conn.commit()
            print(
                f"[SUCCESS] Bulk UPSERTED {len(records)}/{len(items)} videos into `stg_tiktok_explore_videos`."
            )
        else:
            print("[INFO] No valid records found to load.")

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Error loading data: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load TikTok Explore raw JSON to PostgreSQL"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Date of data to load (YYYY-MM-DD)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print(f"ETL Load Step: raw JSON → Postgres Staging ({args.date})")
    print("=" * 60)

    load_raw_to_staging(args.date)
    print("=" * 60)
