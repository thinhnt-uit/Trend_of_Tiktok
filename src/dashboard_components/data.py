"""
Data fetching, caching, preprocessing, and Excel export utilities.
"""

import io
import os
import sys
import warnings
import pandas as pd
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.db import get_db_connection


@st.cache_data(ttl=30)
def fetch_data() -> pd.DataFrame:
    """Fetch joined dim + fact data from the PostgreSQL warehouse."""
    conn = get_db_connection()

    # Check if the analytics schema & dim_videos table exist
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public_analytics'
                AND table_name = 'dim_videos'
            );
        """)
        has_analytics = cur.fetchone()[0]

    if has_analytics:
        query = """
            SELECT
                dv.video_id,
                dv.video_desc,
                dv.author_username,
                dv.author_nickname,
                dv.category_name,
                coalesce(dv.created_at, to_timestamp(case when dv.video_id ~ '^[0-9]+$' then (dv.video_id::bigint >> 32) else null end)) as created_at,
                dv.video_duration,
                dv.video_cover_url,
                dv.video_play_url,
                dv.video_width,
                dv.video_height,
                dv.music_title,
                dv.music_author,
                dv.music_play_url,
                dv.music_is_original,
                dv.music_is_commerce,
                dv.hashtag_list,
                dv.author_followers,
                dv.author_verified,
                dv.is_ad,
                dv.author_heart_count,
                dv.author_video_count,
                dv.video_age_hours,
                dv.creator_tier,
                dv.video_format,
                dv.is_aigc,
                dv.caption_language,
                fp.crawled_date,
                fp.play_count,
                fp.like_count,
                fp.comment_count,
                fp.share_count,
                fp.collect_count,
                fp.repost_count,
                fp.total_interactions,
                fp.engagement_rate,
                fp.virality_velocity
            FROM public_analytics.dim_videos dv
            JOIN public_analytics.fact_video_performance fp
              ON dv.video_id = fp.video_id
            ORDER BY fp.crawled_date DESC, fp.play_count DESC;
        """
    else:
        # Fallback: read directly from staging table
        query = """
            SELECT
                id              as video_id,
                video_desc,
                author_username,
                author_nickname,
                category_name,
                to_timestamp(coalesce(nullif(create_time, 0), case when id ~ '^[0-9]+$' then (id::bigint >> 32) else null end)) as created_at,
                cast(video_info->>'duration' as integer) as video_duration,
                video_info->>'cover'       as video_cover_url,
                video_info->>'playAddr'    as video_play_url,
                cast(video_info->>'width' as integer)  as video_width,
                cast(video_info->>'height' as integer) as video_height,
                music_info->>'title'       as music_title,
                music_info->>'authorName'  as music_author,
                music_info->>'playUrl'     as music_play_url,
                cast(music_info->>'original' as boolean) as music_is_original,
                cast(coalesce(raw_item->'music'->>'is_commerce_music', 'false') as boolean) as music_is_commerce,
                hashtags                   as hashtag_list,
                author_followers,
                author_verified,
                false                      as is_ad,
                cast(coalesce(raw_item->'authorStats'->>'heartCount', '0') as bigint) as author_heart_count,
                cast(coalesce(raw_item->'authorStats'->>'videoCount', '0') as integer) as author_video_count,
                round(cast(extract(epoch from (crawled_at - to_timestamp(create_time))) / 3600.0 as numeric), 1) as video_age_hours,
                case
                    when author_followers >= 1000000 then 'Mega (1M+)'
                    when author_followers >= 100000 then 'Macro (100k-1M)'
                    when author_followers >= 10000 then 'Micro (10k-100k)'
                    else 'Nano (<10k)'
                end as creator_tier,
                case
                    when lower(coalesce(video_desc, '')) ~* '(#review|#danhgia|review|đánh giá)' then 'Review'
                    when lower(coalesce(video_desc, '')) ~* '(#tutorial|#huongdan|#tips|#meo|hướng dẫn|cách làm)' then 'Tutorial'
                    when lower(coalesce(video_desc, '')) ~* '(#vlog|#daily|#cuocsong|vlog|daily life)' then 'Vlog'
                    when lower(coalesce(video_desc, '')) ~* '(#pov|pov)' then 'POV'
                    when lower(coalesce(video_desc, '')) ~* '(#dance|#nhay|nhảy|vũ đạo)' then 'Dance'
                    else 'General / Entertainment'
                end as video_format,
                cast(coalesce(raw_item->>'ShowAIGC', 'false') as boolean) as is_aigc,
                coalesce(nullif(raw_item->>'textLanguage', ''), 'unknown') as caption_language,
                crawled_date,
                play_count,
                like_count,
                comment_count,
                share_count,
                collect_count,
                cast(coalesce(raw_item->'statsV2'->>'repostCount', raw_item->'stats'->>'repostCount', '0') as integer) as repost_count,
                (like_count + comment_count + share_count + collect_count + cast(coalesce(raw_item->'statsV2'->>'repostCount', raw_item->'stats'->>'repostCount', '0') as integer)) as total_interactions,
                case
                    when play_count > 0 then round(cast((like_count + comment_count + share_count + collect_count + cast(coalesce(raw_item->'statsV2'->>'repostCount', raw_item->'stats'->>'repostCount', '0') as integer)) * 100.0 / play_count as numeric), 2)
                    else 0.0
                end as engagement_rate,
                case
                    when extract(epoch from (crawled_at - to_timestamp(create_time))) > 0
                    then round(cast(play_count / (extract(epoch from (crawled_at - to_timestamp(create_time))) / 3600.0) as numeric), 1)
                    else play_count
                end as virality_velocity
            FROM stg_tiktok_explore_videos
            WHERE coalesce(is_ad, false) = false
            ORDER BY crawled_date DESC, play_count DESC;
        """

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        df = pd.read_sql(query, conn)
    conn.close()

    # Data Cleaning and Enhancement
    df["play_count"] = df["play_count"].fillna(0).astype(int)
    df["like_count"] = df["like_count"].fillna(0).astype(int)
    df["comment_count"] = df["comment_count"].fillna(0).astype(int)
    df["share_count"] = df["share_count"].fillna(0).astype(int)
    df["collect_count"] = df["collect_count"].fillna(0).astype(int)
    df["repost_count"] = df["repost_count"].fillna(0).astype(int)
    df["video_duration"] = df["video_duration"].fillna(0).astype(int)

    df["author_followers"] = df["author_followers"].fillna(0).astype(int)
    df["author_heart_count"] = df["author_heart_count"].fillna(0).astype(int)
    df["author_video_count"] = df["author_video_count"].fillna(0).astype(int)
    df["author_verified"] = df["author_verified"].fillna(False).astype(bool)
    df["is_ad"] = df["is_ad"].fillna(False).astype(bool)
    df["is_aigc"] = df["is_aigc"].fillna(False).astype(bool)

    if "total_interactions" not in df.columns or df["total_interactions"].isnull().any():
        df["total_interactions"] = (
            df["like_count"] + df["comment_count"] + df["share_count"] + df["collect_count"] + df["repost_count"]
        )

    if "engagement_rate" not in df.columns or df["engagement_rate"].isnull().any():
        df["engagement_rate"] = df.apply(
            lambda r: (
                (r["total_interactions"] / r["play_count"] * 100)
                if r["play_count"] > 0
                else 0.0
            ),
            axis=1,
        ).round(2)

    df["virality_velocity"] = df["virality_velocity"].fillna(0.0).astype(float)
    df["video_age_hours"] = df["video_age_hours"].fillna(0.0).astype(float)

    # Ensure created_at is valid datetime with snowflake fallback
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        missing_mask = df["created_at"].isna()
        if missing_mask.any() and "video_id" in df.columns:
            def _extract_snowflake_ts(v):
                try:
                    s = str(v).strip()
                    if s.isdigit():
                        return pd.to_datetime(int(s) >> 32, unit="s", utc=True)
                except Exception:
                    pass
                return pd.NaT
            df.loc[missing_mask, "created_at"] = df.loc[missing_mask, "video_id"].apply(_extract_snowflake_ts)

    # Ensure unhashable columns are strings for Streamlit caching
    if "hashtag_list" in df.columns:
        df["hashtag_list"] = df["hashtag_list"].astype(str)

    return df


def deduplicate_latest(df: pd.DataFrame) -> pd.DataFrame:
    """Return a deduplicated DataFrame with one row per video_id.

    When a video appears on multiple crawl dates (it stayed trending for
    several days), this keeps only the **latest** snapshot so that analysis
    tabs (leaderboard, category, creator, etc.) don't double-count videos.

    The full multi-day DataFrame should still be used for time-series and
    system health views.
    """
    if df.empty:
        return df

    if "crawled_date" in df.columns and "video_id" in df.columns:
        df_sorted = df.sort_values("crawled_date", ascending=False)
        return df_sorted.drop_duplicates(subset=["video_id"], keep="first").reset_index(drop=True)

    return df


@st.cache_data
def convert_df_to_excel(df_to_export: pd.DataFrame) -> io.BytesIO:
    """Export formatted Excel workbook with styling, borders, and auto-width columns."""
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter

    val = io.BytesIO()
    cols_to_export = [
        c for c in df_to_export.columns if c not in ["raw_item", "stickers"]
    ]
    df_clean = df_to_export[cols_to_export].copy()

    # Convert timezone-aware datetimes for openpyxl compatibility
    for col in df_clean.columns:
        if pd.api.types.is_datetime64_any_dtype(df_clean[col]):
            if df_clean[col].dt.tz is not None:
                df_clean[col] = df_clean[col].dt.tz_localize(None)

    # Sanitize strings to remove illegal XML control characters that crash openpyxl
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

    def clean_illegal_chars(v):
        if isinstance(v, str):
            return ILLEGAL_CHARACTERS_RE.sub("", v)
        return v

    df_clean = df_clean.map(clean_illegal_chars)

    with pd.ExcelWriter(val, engine="openpyxl") as writer:
        df_clean.to_excel(writer, index=False, sheet_name="TikTok Explore Data")
        worksheet = writer.sheets["TikTok Explore Data"]
        worksheet.views.sheetView[0].showGridLines = True

        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="FE2C55", end_color="FE2C55", fill_type="solid")
        center_alignment = Alignment(horizontal="center", vertical="center")
        thin_side = Side(border_style="thin", color="D3D3D3")
        thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        for col_idx in range(1, len(df_clean.columns) + 1):
            cell = worksheet.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment
            cell.border = thin_border

        # Auto-adjust column widths
        for col_idx, col_name in enumerate(df_clean.columns, 1):
            col_letter = get_column_letter(col_idx)
            max_len = max(len(str(col_name)), 10)
            worksheet.column_dimensions[col_letter].width = min(max_len + 4, 50)

    val.seek(0)
    return val
