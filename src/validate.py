"""
Data validation layer for crawled TikTok Explore records.
Reads raw JSON, validates records using Pydantic, logs metrics, and saves the validated output.
"""

import argparse
import io
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

# Fix Windows console encoding for Unicode output
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Define Pydantic models for validation and normalization

class StatsModel(BaseModel):
    playCount: int = Field(default=0, ge=0)
    diggCount: int = Field(default=0, ge=0)
    commentCount: int = Field(default=0, ge=0)
    shareCount: int = Field(default=0, ge=0)
    collectCount: int = Field(default=0, ge=0)
    repostCount: Optional[int] = Field(default=0, ge=0)


class AuthorModel(BaseModel):
    id: str = Field(min_length=1)
    uniqueId: str = Field(min_length=1)
    nickname: Optional[str] = ""
    verified: Optional[bool] = False


class AuthorStatsModel(BaseModel):
    followerCount: Optional[int] = Field(default=0, ge=0)
    heartCount: Optional[int] = Field(default=0, ge=0)
    videoCount: Optional[int] = Field(default=0, ge=0)


class VideoModel(BaseModel):
    duration: Union[int, float] = Field(default=0, ge=0)
    cover: str = Field(default="", min_length=1)
    playAddr: str = Field(default="", min_length=1)
    downloadAddr: Optional[str] = ""
    width: Optional[int] = Field(default=None, ge=0)
    height: Optional[int] = Field(default=None, ge=0)
    ratio: Optional[str] = ""
    videoID: Optional[str] = ""


class MusicModel(BaseModel):
    id: Optional[str] = ""
    title: Optional[str] = ""
    authorName: Optional[str] = ""
    duration: Optional[int] = Field(default=0, ge=0)
    original: Optional[bool] = False
    playUrl: Optional[str] = ""
    is_commerce_music: Optional[bool] = False


class ChallengeModel(BaseModel):
    id: Optional[str] = ""
    title: Optional[str] = ""


class TikTokItemModel(BaseModel):
    id: str = Field(min_length=1)
    desc: Optional[str] = ""
    stats: StatsModel
    statsV2: Optional[dict] = Field(default_factory=dict)
    author: AuthorModel
    authorStats: Optional[AuthorStatsModel] = Field(default_factory=AuthorStatsModel)
    video: VideoModel
    music: Optional[MusicModel] = Field(default_factory=MusicModel)
    challenges: Optional[List[ChallengeModel]] = Field(default_factory=list)
    effectStickers: Optional[List[Any]] = Field(default_factory=list)
    isAd: Optional[bool] = False
    ShowAIGC: Optional[bool] = False
    textLanguage: Optional[str] = ""
    category_id: Optional[int] = Field(default=None, alias="_category_id")
    category_name: Optional[str] = Field(default=None, alias="_category_name")
    createTime: Optional[int] = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def populate_repost_and_metadata(cls, values: Any) -> Any:
        if isinstance(values, dict):
            stats = values.get("stats")
            stats_v2 = values.get("statsV2") or {}
            if isinstance(stats, dict) and "repostCount" not in stats:
                repost_count = stats_v2.get("repostCount", 0)
                try:
                    stats["repostCount"] = int(repost_count)
                except (ValueError, TypeError):
                    stats["repostCount"] = 0

            # Ensure createTime exists or fallback to TikTok Snowflake ID (id >> 32)
            ct = values.get("createTime")
            if not ct or not str(ct).isdigit() or int(ct) <= 0:
                vid = values.get("id")
                if vid and str(vid).isdigit():
                    try:
                        values["createTime"] = int(vid) >> 32
                    except Exception:
                        pass
        return values

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id_to_str(cls, v: Any) -> str:
        if v is None:
            raise ValueError("ID cannot be None")
        return str(v).strip()

    @field_validator("authorStats", mode="before")
    @classmethod
    def validate_author_stats(cls, v: Any) -> AuthorStatsModel:
        if not isinstance(v, dict):
            return AuthorStatsModel()
        try:
            return AuthorStatsModel(**v)
        except Exception:
            return AuthorStatsModel()

    @field_validator("music", mode="before")
    @classmethod
    def validate_music(cls, v: Any) -> MusicModel:
        if not isinstance(v, dict):
            return MusicModel()
        try:
            # Clean duration if malformed
            duration = v.get("duration")
            if duration is not None:
                try:
                    v["duration"] = max(0, int(duration))
                except Exception:
                    v["duration"] = 0
            return MusicModel(**v)
        except Exception:
            return MusicModel()

    @field_validator("challenges", mode="before")
    @classmethod
    def validate_challenges(cls, v: Any) -> List[ChallengeModel]:
        if not isinstance(v, list):
            return []
        valid_challenges = []
        for ch in v:
            if isinstance(ch, dict):
                try:
                    valid_challenges.append(ChallengeModel(**ch))
                except Exception:
                    pass
        return valid_challenges

    @field_validator("effectStickers", mode="before")
    @classmethod
    def validate_effect_stickers(cls, v: Any) -> List[Any]:
        if not isinstance(v, list):
            return []
        return v


def read_raw_json(date_str: str) -> Optional[dict]:
    """Read raw JSON from S3/MinIO, falling back to local file system."""
    s3_key = f"tiktok_explore/{date_str}/raw_explore_{date_str}.json"
    
    try:
        from src.utils.s3 import read_json_from_s3
        print(f"[INFO] Reading raw data from S3: s3://tiktok-explore-raw/{s3_key}")
        data = read_json_from_s3(s3_key)
        print("[SUCCESS] Loaded raw data from S3.")
        return data
    except Exception as e:
        print(f"[WARNING] S3 load failed: {e}. Trying local fallback.")

    # Local fallback
    local_path = os.path.abspath(
        os.path.join(PROJECT_ROOT, f"data/raw/tiktok_explore/{date_str}/raw_explore_{date_str}.json")
    )
    if os.path.exists(local_path):
        print(f"[INFO] Reading raw data from local file: {local_path}")
        with open(local_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        print(f"[ERROR] Raw data not found locally or on S3 for date {date_str}.")
        return None


def write_validated_json(date_str: str, data: dict) -> str:
    """Save validated JSON data to S3/MinIO and local file system."""
    # Write local fallback copy first
    local_dir = os.path.abspath(
        os.path.join(PROJECT_ROOT, f"data/raw/tiktok_explore/{date_str}")
    )
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, f"validated_explore_{date_str}.json")
    
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Validated local copy saved: {local_path}")

    # Write S3
    s3_key = f"tiktok_explore/{date_str}/validated_explore_{date_str}.json"
    try:
        from src.utils.s3 import upload_json_to_s3
        upload_json_to_s3(s3_key, data)
        print("[SUCCESS] Validated data uploaded to S3.")
    except Exception as e:
        print(f"[WARNING] S3 upload failed: {e}")

    return local_path


def write_rejected_json(date_str: str, rejected_data: dict) -> Optional[str]:
    """Save rejected/invalid records to local Dead Letter Queue (DLQ) and S3/MinIO."""
    if not rejected_data.get("rejected_list"):
        return None

    local_dir = os.path.abspath(
        os.path.join(PROJECT_ROOT, f"data/rejected/tiktok_explore/{date_str}")
    )
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, f"rejected_explore_{date_str}.json")

    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(rejected_data, f, ensure_ascii=False, indent=2)
    print(f"[INFO] DLQ: Saved {len(rejected_data['rejected_list'])} rejected records to {local_path}")

    # Write S3 DLQ
    s3_key = f"tiktok_explore/{date_str}/rejected_explore_{date_str}.json"
    try:
        from src.utils.s3 import upload_json_to_s3
        upload_json_to_s3(s3_key, rejected_data)
        print("[SUCCESS] DLQ data uploaded to S3/MinIO.")
    except Exception as e:
        print(f"[WARNING] S3 DLQ upload failed: {e}")

    return local_path


def validate_records(raw_data: dict) -> dict:
    """Validate each item, keeping track of stats, skip invalid items, and capture DLQ."""
    start_time = datetime.now()
    items = raw_data.get("item_list", [])
    
    discovered_count = len(items)
    valid_items = []
    invalid_items = []
    invalid_count = 0
    ad_count = 0
    errors = []

    for index, item in enumerate(items):
        try:
            # Run Pydantic validation
            validated_item = TikTokItemModel(**item)
            # Dump to dict for output JSON structure (using mode='json' to serialize objects nicely)
            validated_dict = validated_item.model_dump(by_alias=True)
            valid_items.append(validated_dict)

            # Count ad videos (will be filtered out downstream in dbt staging)
            if validated_dict.get("isAd", False):
                ad_count += 1

        except Exception as ve:
            invalid_count += 1
            item_id = item.get("id", f"index_{index}")
            err_msg = f"Item ID {item_id} validation failed: {ve}"
            errors.append(err_msg)
            invalid_items.append(
                {
                    "item_id": str(item_id),
                    "error": str(ve),
                    "rejected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "raw_record": item,
                }
            )
            print(f"[WARNING] {err_msg}")

    # Deduplicate cross-category duplicates: keep the record with the
    # highest playCount per video_id so downstream layers receive clean,
    # non-redundant data.
    seen: dict[str, dict] = {}
    for item in valid_items:
        vid = item.get("id")
        if not vid:
            continue
        existing = seen.get(vid)
        if existing is None:
            seen[vid] = item
        else:
            current_plays = item.get("stats", {}).get("playCount", 0)
            existing_plays = existing.get("stats", {}).get("playCount", 0)
            if current_plays > existing_plays:
                seen[vid] = item
    duplicate_count = len(valid_items) - len(seen)
    valid_items = list(seen.values())

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Log metrics summary
    print("\n" + "=" * 60)
    print("VALIDATION METRICS SUMMARY")
    print("-" * 60)
    print(f"Crawl Date Range/Time : {raw_data.get('crawled_at')}")
    print(f"Categories Crawled    : {raw_data.get('categories_crawled', 'Unknown')}")
    print(f"Discovered Records    : {discovered_count}")
    print(f"Valid Records         : {len(valid_items)}")
    print(f"  ├─ Organic (creator): {len(valid_items) - ad_count}")
    print(f"  └─ Ad/Sponsored      : {ad_count}  ← filtered out at dbt staging")
    print(f"Cross-category dups   : {duplicate_count}  ← removed at validation")
    print(f"Invalid Records (DLQ) : {invalid_count}")
    print(f"Duration (seconds)    : {duration:.2f}s")
    if errors:
        print(f"Errors encountered    : {len(errors)}")
    print("=" * 60 + "\n")

    return {
        "crawled_at": raw_data.get("crawled_at"),
        "categories_crawled": raw_data.get("categories_crawled"),
        "total_discovered": discovered_count,
        "total_videos": len(valid_items),
        "total_ads": ad_count,
        "total_duplicates": duplicate_count,
        "total_invalid": invalid_count,
        "validation_duration_seconds": duration,
        "item_list": valid_items,
        "rejected_list": invalid_items,
    }


def main():
    parser = argparse.ArgumentParser(description="TikTok Explore Data Validation Step")
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Date of data to validate (YYYY-MM-DD)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print(f"Starting Data Validation: {args.date}")
    print("=" * 60)

    raw_data = read_raw_json(args.date)
    if not raw_data:
        print(f"[ERROR] No raw data available for {args.date}. Validation aborted.")
        sys.exit(1)

    validated_data = validate_records(raw_data)
    
    # Save the valid output
    write_validated_json(args.date, validated_data)

    # Save Dead Letter Queue (DLQ) if any invalid items found
    if validated_data.get("rejected_list"):
        rejected_payload = {
            "crawled_at": raw_data.get("crawled_at"),
            "date": args.date,
            "total_rejected": len(validated_data["rejected_list"]),
            "rejected_list": validated_data["rejected_list"],
        }
        write_rejected_json(args.date, rejected_payload)

    print("[SUCCESS] Validation process complete.")


if __name__ == "__main__":
    main()
