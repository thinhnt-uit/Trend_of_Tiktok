"""
Train Machine Learning Trend Predictor (Random Forest) offline.
Extracts features from DWH or raw JSON snapshots, trains the model,
evaluates R2 and MAE metrics, and saves the serialized model bundle to `models/trend_predictor.joblib`.
"""

import argparse
import glob
import io
import json
import os
import sys
import warnings
from datetime import datetime
from typing import Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

# Fix Windows console encoding for Unicode output
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DEFAULT_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "trend_predictor.joblib")


import ast
import re


def parse_hashtag_count(x, desc: str = "") -> int:
    """Safely parse hashtag count from list, JSON string, Python repr, or text description."""
    if isinstance(x, list):
        return len(x)
    if isinstance(x, str) and x.strip():
        s = x.strip()
        # 1. JSON parsing
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return len(parsed)
        except Exception:
            pass
        # 2. Python list literal representation (e.g. "['tag1', 'tag2']")
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, (list, tuple, set)):
                return len(parsed)
        except Exception:
            pass
        # 3. Quoted strings inside brackets
        tags = re.findall(r"['\"]([^'\"]+)['\"]", s)
        if tags:
            return len(tags)

    if isinstance(desc, str) and "#" in desc:
        desc_tags = re.findall(r"#([a-zA-Z0-9_\u00C0-\u024F\u1E00-\u1EFF]+)", desc)
        if desc_tags:
            return len(desc_tags)

    return 0


def fetch_training_data_from_db() -> Optional[pd.DataFrame]:
    """Fetch analytics dataset from PostgreSQL."""
    try:
        from src.utils.db import get_db_connection
        conn = get_db_connection()
        query = """
            SELECT
                dv.video_id,
                dv.category_name,
                dv.video_duration,
                dv.author_followers,
                dv.author_verified,
                dv.is_ad,
                dv.hashtag_list,
                fp.play_count,
                fp.like_count,
                fp.comment_count,
                fp.share_count,
                fp.collect_count,
                fp.crawled_date
            FROM public_analytics.dim_videos dv
            JOIN public_analytics.fact_video_performance fp
              ON dv.video_id = fp.video_id
            WHERE fp.play_count > 0 AND dv.video_duration > 0;
        """
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            df = pd.read_sql(query, conn)
        conn.close()
        if not df.empty:
            print(f"[INFO] Loaded {len(df)} records from PostgreSQL DWH.")
            return df
    except Exception as e:
        print(f"[WARNING] Could not fetch data from database: {e}")
    return None


def fetch_training_data_from_files() -> pd.DataFrame:
    """Fallback: read from validated or raw JSON files on disk."""
    raw_pattern = os.path.join(PROJECT_ROOT, "data", "raw", "tiktok_explore", "*", "*.json")
    files = glob.glob(raw_pattern)
    records = []

    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = json.load(f)
                items = content.get("item_list", [])
                for item in items:
                    stats = item.get("stats", {})
                    video = item.get("video", {})
                    author_stats = item.get("authorStats", {})
                    author = item.get("author", {})
                    challenges = item.get("challenges", [])
                    hashtag_titles = [c.get("title") for c in challenges if c.get("title")]

                    play_count = int(stats.get("playCount") or 0)
                    duration = int(video.get("duration") or 0)
                    if play_count > 0 and duration > 0:
                        records.append({
                            "video_id": item.get("id"),
                            "category_name": item.get("_category_name") or "Unknown",
                            "video_duration": duration,
                            "author_followers": int(author_stats.get("followerCount") or 0),
                            "author_verified": bool(author.get("verified") or False),
                            "is_ad": bool(item.get("isAd") or False),
                            "hashtag_list": hashtag_titles,
                            "play_count": play_count,
                        })
        except Exception as e:
            print(f"[WARNING] Error reading {fpath}: {e}")

    df = pd.DataFrame(records)
    if not df.empty:
        df = df.drop_duplicates(subset=["video_id"])
        print(f"[INFO] Loaded {len(df)} records from local JSON files fallback.")
    return df


def prepare_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, list]:
    """Clean features and perform one-hot encoding for category."""
    df_clean = df.copy()
    df_clean["hashtag_count"] = df_clean.apply(
        lambda r: parse_hashtag_count(r.get("hashtag_list"), r.get("video_desc", "")), axis=1
    )
    df_clean["author_followers"] = df_clean["author_followers"].fillna(0).astype(int)
    df_clean["video_duration"] = df_clean["video_duration"].fillna(0).astype(int)
    df_clean["author_verified"] = df_clean["author_verified"].fillna(False).astype(int)
    if "is_ad" not in df_clean.columns:
        df_clean["is_ad"] = 0
    df_clean["is_ad"] = df_clean["is_ad"].fillna(False).astype(int)
    df_clean["category_name"] = df_clean["category_name"].fillna("Unknown")

    # Base numerical/boolean features
    base_features = [
        "video_duration",
        "author_followers",
        "author_verified",
        "is_ad",
        "hashtag_count",
    ]
    X = df_clean[base_features].copy()

    # One-hot encode category
    all_cats = sorted(df_clean["category_name"].unique())
    for cat in all_cats:
        X[f"cat_{cat}"] = (df_clean["category_name"] == cat).astype(int)

    y = df_clean["play_count"].astype(float)
    return X, y, all_cats


def train_and_save_model(
    df: Optional[pd.DataFrame] = None,
    output_path: str = DEFAULT_MODEL_PATH,
) -> Optional[dict]:
    """Train Random Forest Regressor and save the bundle to disk."""
    if df is None:
        df = fetch_training_data_from_db()
        if df is None or df.empty:
            df = fetch_training_data_from_files()

    if df.empty or len(df) < 10:
        print("[WARNING] Insufficient data to train model (minimum 10 samples required).")
        return None

    X, y, all_cats = prepare_dataset(df)

    test_size = 0.2 if len(X) >= 20 else 0.1
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )

    print(f"[INFO] Training RandomForestRegressor on {len(X_train)} samples...")
    model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    r2 = float(r2_score(y_test, preds))
    mae = float(mean_absolute_error(y_test, preds))

    importances = model.feature_importances_
    feat_imp = pd.DataFrame(
        {"Feature": X.columns, "Importance": importances}
    ).sort_values(by="Importance", ascending=False)

    bundle = {
        "model": model,
        "feature_columns": list(X.columns),
        "categories": all_cats,
        "r2_score": r2,
        "mae": mae,
        "feature_importances": feat_imp.to_dict(orient="records"),
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_samples": len(X),
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    joblib.dump(bundle, output_path)
    print(f"[SUCCESS] Model bundle saved to {output_path}")
    print(f"[INFO] Model Evaluation: R² Score = {r2:.3f}, MAE = {mae:,.0f} views")
    return bundle


def main():
    parser = argparse.ArgumentParser(description="Train TikTok Trend Prediction Model")
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_MODEL_PATH,
        help="Path to save the joblib model bundle",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("TikTok Explore Trend — ML Training Pipeline")
    print("=" * 60)
    train_and_save_model(output_path=args.output)


if __name__ == "__main__":
    main()
