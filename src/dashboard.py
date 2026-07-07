"""
TikTok Explore — Professional Creator Insights Dashboard
Interactive Streamlit dashboard designed for content creators and marketers to extract high-value viral trends, audio performance, and format insights.
"""

import os
import re
import sys
import warnings

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.db import get_db_connection

# ──────────────────────────────────────────────────────────────────────────────
# 1. PAGE CONFIG & PREMIUM STYLING
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TikTok Explore — Professional Creator Insights",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dark theme custom stylesheet
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Overrides */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Background dark color */
    .stApp {
        background-color: #0c0c0e;
    }
    
    /* Header Gradient */
    .header-container {
        padding: 1.5rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 2rem;
    }
    .title-gradient {
        background: linear-gradient(135deg, #FE2C55 0%, #25F4EE 50%, #FFD700 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .subtitle-muted {
        color: #8E8E93;
        font-size: 1.1rem;
        margin-top: 0.2rem;
    }
    
    /* Metric Cards */
    .metric-card {
        background: #16161a;
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: left;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(254, 44, 85, 0.25);
        box-shadow: 0 8px 30px rgba(254, 44, 85, 0.08);
    }
    .metric-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: #FE2C55;
    }
    .metric-card.views::before { background: #25F4EE; }
    .metric-card.engagement::before { background: #FFD93D; }
    .metric-card.creator::before { background: #9B59B6; }

    .metric-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #8E8E93;
        text-transform: uppercase;
        letter-spacing: 1.2px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #ffffff;
        margin-top: 0.5rem;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.4rem;
        font-weight: 700;
        color: #ffffff;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Custom info boxes */
    .insight-box {
        background: rgba(37, 244, 238, 0.03);
        border: 1px dashed rgba(37, 244, 238, 0.2);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        color: #E5E5EA;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    .insight-icon {
        color: #25F4EE;
        font-weight: bold;
        margin-right: 6px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# 2. DATA FETCH & PREPROCESSING
# ──────────────────────────────────────────────────────────────────────────────


@st.cache_data(ttl=30)
def fetch_data():
    """Fetch joined dim + fact data from the analytics layer."""
    conn = get_db_connection()

    # Check if the analytics tables exist
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
                dv.category_id,
                dv.category_name,
                dv.created_at,
                dv.video_duration,
                dv.video_cover_url,
                dv.video_play_url,
                dv.video_download_url,
                dv.video_width,
                dv.video_height,
                dv.music_title,
                dv.music_author,
                dv.hashtag_list,
                dv.author_followers,
                dv.author_verified,
                dv.is_ad,
                dv.music_play_url,
                dv.stickers,
                dv.raw_item,
                fp.crawled_date,
                fp.play_count,
                fp.like_count,
                fp.comment_count,
                fp.share_count,
                fp.collect_count
            FROM public_analytics.dim_videos dv
            JOIN public_analytics.fact_video_performance fp
              ON dv.video_id = fp.video_id
            ORDER BY fp.crawled_date DESC, fp.play_count DESC;
        """
    else:
        # Fallback: read directly from staging
        query = """
            SELECT
                id              as video_id,
                video_desc,
                author_username,
                author_nickname,
                category_id,
                category_name,
                to_timestamp(create_time) as created_at,
                cast(video_info->>'duration' as integer) as video_duration,
                video_info->>'cover'       as video_cover_url,
                video_info->>'playAddr'    as video_play_url,
                video_info->>'downloadAddr' as video_download_url,
                cast(video_info->>'width' as integer)  as video_width,
                cast(video_info->>'height' as integer) as video_height,
                music_info->>'title'       as music_title,
                music_info->>'authorName'  as music_author,
                hashtags                   as hashtag_list,
                author_followers,
                author_verified,
                is_ad,
                music_play_url,
                stickers,
                raw_item,
                crawled_date,
                play_count,
                like_count,
                comment_count,
                share_count,
                collect_count
            FROM stg_tiktok_explore_videos
            ORDER BY crawled_date DESC, play_count DESC;
        """

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="pandas only supports SQLAlchemy connectable",
            category=UserWarning,
        )
        df = pd.read_sql(query, conn)
    conn.close()

    # Data Cleaning and Enhancement
    df["play_count"] = df["play_count"].fillna(0).astype(int)
    df["like_count"] = df["like_count"].fillna(0).astype(int)
    df["comment_count"] = df["comment_count"].fillna(0).astype(int)
    df["share_count"] = df["share_count"].fillna(0).astype(int)
    df["collect_count"] = df["collect_count"].fillna(0).astype(int)
    df["video_duration"] = df["video_duration"].fillna(0).astype(int)

    # Clean new attributes
    df["author_followers"] = df["author_followers"].fillna(0).astype(int)
    df["author_verified"] = df["author_verified"].fillna(False).astype(bool)
    df["is_ad"] = df["is_ad"].fillna(False).astype(bool)

    # Calculate Engagement Rate: Total engagement (likes + comments + shares + collects) / plays
    # Expressed as a percentage
    df["total_interactions"] = (
        df["like_count"] + df["comment_count"] + df["share_count"] + df["collect_count"]
    )
    df["engagement_rate"] = df.apply(
        lambda r: (
            (r["total_interactions"] / r["play_count"] * 100)
            if r["play_count"] > 0
            else 0.0
        ),
        axis=1,
    ).round(2)

    return df


try:
    df_raw = fetch_data()
except Exception as e:
    st.error(f"Connection to the data warehouse failed: {e}")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# 3. SIDEBAR CREATOR FILTERS
# ──────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    """
<div style='text-align: center; margin-bottom: 1.5rem;'>
    <img src='https://img.icons8.com/color/96/tiktok.png' width='55'/>
    <h3 style='margin-top: 0.5rem; font-weight: 700; color: #fff;'>Creator Console</h3>
    <p style='color: #8E8E93; font-size: 0.85rem;'>TikTok Explore Trend Insights</p>
</div>
""",
    unsafe_allow_html=True,
)

# Date filter
dates = sorted(df_raw["crawled_date"].unique())
selected_dates = st.sidebar.multiselect(
    "Select Crawl Dates", options=dates, default=[]
)
df = (
    df_raw[df_raw["crawled_date"].isin(selected_dates)]
    if selected_dates
    else df_raw.copy()
)

# Category filter
categories = sorted(df["category_name"].dropna().unique())
selected_cats = st.sidebar.multiselect(
    "Select Category", options=categories, default=[]
)
if selected_cats:
    df = df[df["category_name"].isin(selected_cats)]

# Creator Account Filters
st.sidebar.markdown("---")
st.sidebar.markdown("**Creator Profiling Filters**")

# Min Followers
max_followers = (
    int(df["author_followers"].max())
    if not df.empty and pd.notna(df["author_followers"].max())
    else 10_000_000
)
min_fols = st.sidebar.number_input(
    "Min Creator Followers",
    min_value=0,
    max_value=max_followers,
    value=0,
    step=50_000,
)
df = df[df["author_followers"] >= min_fols]

# Verification status
verified_filter = st.sidebar.selectbox(
    "Verification Badge",
    ["All Accounts", "Verified Only (Tích xanh)", "Unverified Only"],
)
if verified_filter == "Verified Only (Tích xanh)":
    df = df[df["author_verified"] == True]
elif verified_filter == "Unverified Only":
    df = df[df["author_verified"] == False]

# Ads Filter
ad_filter = st.sidebar.selectbox(
    "Video Type", ["All Content", "Organic Content Only", "Sponsored Ads Only"]
)
if ad_filter == "Organic Content Only":
    df = df[df["is_ad"] == False]
elif ad_filter == "Sponsored Ads Only":
    df = df[df["is_ad"] == True]

# Minimum Engagement Rate Filter
min_eng_rate = st.sidebar.slider(
    "Min Engagement Rate (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5
)
df = df[df["engagement_rate"] >= min_eng_rate]

# Min views
max_plays = (
    int(df["play_count"].max())
    if not df.empty and pd.notna(df["play_count"].max())
    else 1_000_000
)
min_plays = st.sidebar.number_input(
    "Minimum Views", min_value=0, max_value=max_plays, value=0, step=50_000
)
df = df[df["play_count"] >= min_plays]

# Search Bar
search = st.sidebar.text_input("Search Description / Creator")
if search:
    df = df[
        df["video_desc"].str.contains(search, case=False, na=False)
        | df["author_username"].str.contains(search, case=False, na=False)
        | df["author_nickname"].str.contains(search, case=False, na=False)
    ]

# ──────────────────────────────────────────────────────────────────────────────
# EXCEL EXPORT
# ──────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("**Data Export**")


@st.cache_data
def convert_df_to_excel(df_to_export):
    import io
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter

    val = io.BytesIO()
    # Drop nested and heavy columns
    cols_to_export = [
        c for c in df_to_export.columns if c not in ["raw_item", "stickers"]
    ]
    df_clean = df_to_export[cols_to_export].copy()

    # Convert timezone-aware datetimes to timezone-unaware for Excel compatibility
    for col in df_clean.columns:
        if pd.api.types.is_datetime64_any_dtype(df_clean[col]):
            if df_clean[col].dt.tz is not None:
                df_clean[col] = df_clean[col].dt.tz_localize(None)

    # Write to Excel with styling
    with pd.ExcelWriter(val, engine="openpyxl") as writer:
        df_clean.to_excel(writer, index=False, sheet_name="TikTok Explore Data")

        workbook = writer.book
        worksheet = writer.sheets["TikTok Explore Data"]

        # Enable grid lines explicitly
        worksheet.views.sheetView[0].showGridLines = True

        # Styles definition
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(
            start_color="FE2C55", end_color="FE2C55", fill_type="solid"
        )  # TikTok Pink!
        center_alignment = Alignment(horizontal="center", vertical="center")
        left_alignment = Alignment(horizontal="left", vertical="center")
        right_alignment = Alignment(horizontal="right", vertical="center")

        thin_side = Side(border_style="thin", color="D3D3D3")
        thin_border = Border(
            left=thin_side, right=thin_side, top=thin_side, bottom=thin_side
        )

        # Style header row
        for col_idx in range(1, len(df_clean.columns) + 1):
            cell = worksheet.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment
            cell.border = thin_border

        # Style data rows and format numbers
        for row_idx in range(2, len(df_clean) + 2):
            for col_idx in range(1, len(df_clean.columns) + 1):
                cell = worksheet.cell(row=row_idx, column=col_idx)
                cell.border = thin_border
                col_name = df_clean.columns[col_idx - 1]

                if col_name in [
                    "play_count",
                    "like_count",
                    "comment_count",
                    "share_count",
                    "collect_count",
                    "author_followers",
                ]:
                    cell.number_format = "#,##0"
                    cell.alignment = right_alignment
                elif col_name in ["video_duration", "category_id"]:
                    cell.number_format = "#,##0"
                    cell.alignment = center_alignment
                elif col_name in ["author_verified", "is_ad"]:
                    cell.alignment = center_alignment
                else:
                    cell.alignment = left_alignment

        # Auto-adjust column widths
        for col in worksheet.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = len(val_str)
            worksheet.column_dimensions[col_letter].width = min(
                max(max_len + 3, 10), 40
            )

    return val.getvalue()


try:
    if not df.empty:
        excel_data = convert_df_to_excel(df)
        st.sidebar.download_button(
            label="Export Current View to Excel",
            data=excel_data,
            file_name=f"tiktok_trends_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.sidebar.info("No data available to export.")
except Exception as excel_err:
    st.sidebar.error(f"Error generating Excel: {excel_err}")


# ──────────────────────────────────────────────────────────────────────────────
# 4. MAIN BANNER & KPI CARDS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class='header-container'>
    <div class='title-gradient'>TikTok Explore Trend Analytics</div>
    <div class='subtitle-muted'>Data-driven video performance metrics and algorithmic trend forecasting</div>
</div>
""",
    unsafe_allow_html=True,
)

if df.empty:
    st.warning(
        "No trending videos match the selected filters. Please adjust the sidebar controls."
    )
    st.stop()

# Use all filtered data (filtered by sidebar controls including date selection)
df_latest = df

total_videos = df_latest["video_id"].nunique()
total_views = df_latest["play_count"].sum()
avg_engagement = df_latest["engagement_rate"].mean() if not df_latest.empty else 0.0

# Top category based on views
top_cat_series = (
    df_latest.groupby("category_name")["play_count"].sum().sort_values(ascending=False)
)
top_category = top_cat_series.index[0] if not top_cat_series.empty else "N/A"

# Draw KPIs
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f"""
        <div class='metric-card'>
            <div class='metric-label'>Trending Videos</div>
            <div class='metric-value'>{total_videos:,}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""
        <div class='metric-card views'>
            <div class='metric-label'>Cumulative Views</div>
            <div class='metric-value'>{total_views:,}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"""
        <div class='metric-card engagement'>
            <div class='metric-label'>Avg Engagement Rate</div>
            <div class='metric-value'>{avg_engagement:.2f}%</div>
        </div>
    """,
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        f"""
        <div class='metric-card creator'>
            <div class='metric-label'>Hot Category</div>
            <div class='metric-value' style='font-size: 1.25rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{top_category}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────────────────────────────────────────
# 5. TABS DEFINITION
# ──────────────────────────────────────────────────────────────────────────────
(
    tab_system,
    tab_overview,
    tab_growth,
    tab_creator,
    tab_format,
    tab_audio,
    tab_hashtag,
    tab_player,
    tab_ml,
) = st.tabs(
    [
        "System Overview",
        "Viral Leaderboard",
        "Historical Growth Trends",
        "Creator & Verified Analytics",
        "Format & Duration Sweet Spot",
        "Audio & Soundtrack Trends",
        "Hashtags & Content Themes",
        "Video Auditing Tool",
        "ML Trend Predictor",
    ]
)

# Plotly theme configuration
PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans", size=12),
)

CATEGORY_COLORS = {
    "All": "#E0E0E0",
    "Singing & Dancing": "#FF6B81",
    "Comedy": "#FFD93D",
    "Sports": "#6BCB77",
    "Anime & Comics": "#9B59B6",
    "Relationship": "#FF6348",
    "Shows": "#1E90FF",
    "Daily Life": "#00D2D3",
    "Unknown": "#636e72",
}

# ── TAB 0:📊 SYSTEM OVERVIEW ────────────────────────────────────────
with tab_system:
    st.markdown(
        "<div class='section-header'>📊 Thông tin hệ thống (Crawl Statistics)</div>",
        unsafe_allow_html=True,
    )
    
    st.markdown(
        """
        <div class='insight-box'>
            <span class='insight-icon'>Hệ thống thu thập:</span> 
            Tổng quan số lượng ngày đã cào dữ liệu và phân bổ số lượng video theo từng ngày.
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Calculate stats
    total_days = df_raw["crawled_date"].nunique()
    videos_per_day = df_raw.groupby("crawled_date")["video_id"].nunique().reset_index()
    videos_per_day.columns = ["Ngày cào", "Số lượng video"]
    
    col_sys1, col_sys2 = st.columns([1, 2])
    with col_sys1:
        st.markdown(
            f"""
            <div class='metric-card' style='margin-bottom: 1rem;'>
                <div class='metric-label'>Tổng số ngày Crawl</div>
                <div class='metric-value'>{total_days}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.dataframe(videos_per_day, use_container_width=True, hide_index=True)
        
    with col_sys2:
        if not videos_per_day.empty:
            fig_sys = px.bar(
                videos_per_day, 
                x="Ngày cào", 
                y="Số lượng video", 
                text="Số lượng video",
                title="Số lượng video thu thập mỗi ngày",
                color_discrete_sequence=["#25F4EE"]
            )
            fig_sys.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig_sys, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu cào.")

# ── TAB 1:🏆 VIRAL LEADERBOARD ──────────────────────────────────────
with tab_overview:
    st.markdown(
        "<div class='section-header'>Video thịnh hành nổi bật (Tất cả dữ liệu đã chọn)</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>Phân tích chiến lược:</span> 
        Sử dụng các cột bên dưới để sắp xếp theo <strong>Tỷ lệ tương tác (Engagement %)</strong>. Hãy chú ý đến những video có tỷ lệ tương tác cao nhưng số lượt xem còn thấp. 
        Đây là các <strong>nội dung ngách được quan tâm lớn</strong>. Việc học hỏi cấu trúc, âm thanh hoặc hashtag của các video này sẽ giúp bạn dễ dàng tối ưu hóa và lên xu hướng hơn.
    </div>
    """,
        unsafe_allow_html=True,
    )

    df_lb = df_latest.copy().sort_values(by="play_count", ascending=False)

    display_cols = {
        "video_cover_url": "Cover",
        "category_name": "Category",
        "video_desc": "Description",
        "author_nickname": "Creator",
        "author_followers": "Followers",
        "play_count": "Views",
        "engagement_rate": "Engagement %",
        "author_verified": "Tích Xanh",
        "is_ad": "Ads",
        "video_duration": "Duration (s)",
        "video_play_url": "Watch",
    }
    df_disp = df_lb[list(display_cols.keys())].rename(columns=display_cols)

    st.dataframe(
        df_disp,
        column_config={
            "Cover": st.column_config.ImageColumn("Cover", width="small"),
            "Watch": st.column_config.LinkColumn("Watch", display_text="▶ Play"),
            "Followers": st.column_config.NumberColumn(format="%d 👥"),
            "Views": st.column_config.NumberColumn(format="%d 👀"),
            "Engagement %": st.column_config.NumberColumn(format="%.2f%% 🔥"),
            "Tích Xanh": st.column_config.CheckboxColumn("Tích Xanh"),
            "Ads": st.column_config.CheckboxColumn("Ads"),
        },
        use_container_width=True,
        hide_index=True,
    )


# ── TAB 2:📈 HISTORICAL GROWTH TRENDS ───────────────────────────────
with tab_growth:
    st.markdown(
        "<div class='section-header'>📈 Lịch sử tăng trưởng lượt xem theo danh mục</div>",
        unsafe_allow_html=True,
    )

    # Check if there are multiple dates in the database
    all_dates = sorted(df_raw["crawled_date"].unique())
    if len(all_dates) < 2:
        st.info(
            "💡 Hệ thống hiện tại mới chỉ cào dữ liệu của 1 ngày. Biểu đồ tăng trưởng lịch sử sẽ tự động hiển thị khi bạn chạy cào dữ liệu trong các ngày tiếp theo."
        )
    else:
        st.markdown(
            """
        <div class='insight-box'>
            <span class='insight-icon'>📊 Nguyên lý lũy kế:</span> 
            Số liệu lượt xem trên TikTok được cộng dồn theo thời gian. Biểu đồ dưới đây thể hiện **tổng lượt xem tích lũy** 
            của từng danh mục qua các ngày cào dữ liệu, giúp xác định danh mục nào đang có tốc độ bứt phá lớn nhất.
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Line chart: category growth over time
        df_growth_cat = (
            df_raw.groupby(["crawled_date", "category_name"])["play_count"]
            .sum()
            .reset_index()
        )
        fig_line_growth = px.line(
            df_growth_cat,
            x="crawled_date",
            y="play_count",
            color="category_name",
            title="Xu hướng tăng trưởng lượt xem lũy kế theo Danh mục",
            labels={"crawled_date": "Ngày cào dữ liệu", "play_count": "Tổng lượt xem"},
            markers=True,
            color_discrete_map=CATEGORY_COLORS,
        )
        fig_line_growth.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_line_growth, use_container_width=True)

        # Line chart: top videos view growth rate
        st.markdown(
            "<div class='section-header'>📈 Tốc độ tăng trưởng của các video Viral nổi bật</div>",
            unsafe_allow_html=True,
        )

        # Select top 5 videos from the latest crawl
        top_vids = (
            df_latest.sort_values(by="play_count", ascending=False)
            .head(5)["video_id"]
            .tolist()
        )
        df_top_hist = df_raw[df_raw["video_id"].isin(top_vids)].sort_values(
            "crawled_date"
        )

        if not df_top_hist.empty:
            df_top_hist = df_top_hist.copy()
            df_top_hist["video_label"] = (
                df_top_hist["author_nickname"]
                + ": "
                + df_top_hist["video_desc"].str.slice(0, 30)
                + "..."
            )
            fig_vid_growth = px.line(
                df_top_hist,
                x="crawled_date",
                y="play_count",
                color="video_label",
                title="Tốc độ tăng trưởng lượt xem của Top 5 video hot nhất",
                labels={
                    "crawled_date": "Ngày cào dữ liệu",
                    "play_count": "Số lượt xem",
                },
                markers=True,
            )
            fig_vid_growth.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig_vid_growth, use_container_width=True)


# ── TAB 3: CREATOR & VERIFIED ANALYTICS ──────────────────────────────────
with tab_creator:
    st.markdown(
        "<div class='section-header'>Phân tích quy mô kênh và trạng thái xác thực</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>Nguyên lý thuật toán:</span> 
        So sánh lượng Follower và số lượt xem ở biểu đồ bên dưới. Nếu lượt xem phân bố ngẫu nhiên không phụ thuộc vào lượng follower, 
        điều đó chứng minh rằng <strong>thuật toán TikTok phân phối lượt xem dựa trên chất lượng video chứ không phải độ lớn của kênh</strong>. 
        Kênh nhỏ vẫn có cơ hội lên xu hướng ngang bằng với các kênh hàng triệu follower.
    </div>
    """,
        unsafe_allow_html=True,
    )

    col_cr1, col_cr2 = st.columns([3, 2])

    with col_cr1:
        # Scatter plot Follower count vs Views
        fig_fols = px.scatter(
            df_latest,
            x="author_followers",
            y="play_count",
            color="category_name",
            size="engagement_rate",
            log_x=True,
            hover_name="author_nickname",
            hover_data=[
                "author_followers",
                "play_count",
                "engagement_rate",
                "author_verified",
            ],
            title="Tương quan giữa lượt xem và lượng Follower (Kích thước bóng đại diện cho Tỷ lệ tương tác)",
            labels={
                "author_followers": "Lượng Follower của Creator (Thang Log)",
                "play_count": "Lượt xem",
            },
            color_discrete_map=CATEGORY_COLORS,
        )
        fig_fols.update_layout(**PLOTLY_LAYOUT)
        st.plotly_chart(fig_fols, use_container_width=True)

    with col_cr2:
        # Verified vs Unverified averages
        df_ver = (
            df_latest.groupby("author_verified")
            .agg(
                avg_views=("play_count", "mean"),
                avg_eng=("engagement_rate", "mean"),
                count=("video_id", "count"),
            )
            .reset_index()
        )
        df_ver["Verification"] = df_ver["author_verified"].map(
            {True: "Tích xanh (Verified)", False: "Tài khoản thường (Unverified)"}
        )

        fig_ver = px.bar(
            df_ver,
            x="Verification",
            y="avg_views",
            color="avg_eng",
            color_continuous_scale="Bluered",
            title="Lượt xem trung bình: Tài khoản tích xanh vs Tài khoản thường",
            labels={"avg_views": "Lượt xem trung bình", "Verification": "Loại tài khoản"},
            text="count",
        )
        fig_ver.update_layout(**PLOTLY_LAYOUT)
        fig_ver.update_traces(texttemplate="Số video: %{text}", textposition="outside")
        st.plotly_chart(fig_ver, use_container_width=True)

    # Top creator table
    st.markdown(
        "<div class='section-header'>Danh sách Creator nổi bật nhất</div>",
        unsafe_allow_html=True,
    )
    df_creators = (
        df_latest.groupby(
            [
                "author_username",
                "author_nickname",
                "author_followers",
                "author_verified",
            ]
        )
        .agg(
            video_count=("video_id", "count"),
            total_views=("play_count", "sum"),
            avg_engagement=("engagement_rate", "mean"),
        )
        .reset_index()
        .sort_values(by="total_views", ascending=False)
        .head(15)
    )

    st.dataframe(
        df_creators.rename(
            columns={
                "author_username": "Username",
                "author_nickname": "Nickname",
                "author_followers": "Followers",
                "author_verified": "Verified",
                "video_count": "Trending Videos",
                "total_views": "Total Views",
                "avg_engagement": "Avg Engagement %",
            }
        ),
        column_config={
            "Followers": st.column_config.NumberColumn(format="%d 👥"),
            "Total Views": st.column_config.NumberColumn(format="%d 👀"),
            "Avg Engagement %": st.column_config.NumberColumn(format="%.2f%% 🔥"),
            "Verified": st.column_config.CheckboxColumn("Verified"),
        },
        use_container_width=True,
        hide_index=True,
    )


# ── TAB 3: FORMAT & DURATION SWEET SPOT ───────────────────────────────
with tab_format:
    st.markdown(
        "<div class='section-header'>Phân tích thời lượng video tối ưu</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>Phân tích định dạng:</span> 
        Các video ngắn (<15 giây) còn chiếm ưu thế hay TikTok đang chuyển dịch sang nội dung dài hơn? 
        Hãy quan sát biểu đồ bên dưới để xác định **khoảng thời lượng tối ưu** giúp đạt lượt xem và tương tác cao nhất cho danh mục của bạn.
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Filter zero duration
    df_duration = df_latest[df_latest["video_duration"] > 0].copy()

    if not df_duration.empty:
        col_f1, col_f2 = st.columns([3, 2])

        with col_f1:
            fig_scat = px.scatter(
                df_duration,
                x="video_duration",
                y="play_count",
                size="engagement_rate",
                color="category_name",
                color_discrete_map=CATEGORY_COLORS,
                hover_name="author_nickname",
                hover_data=["engagement_rate", "like_count"],
                title="Ma trận thời lượng video tối ưu (Thời lượng vs Lượt xem)",
                labels={
                    "video_duration": "Thời lượng video (giây)",
                    "play_count": "Lượt xem",
                },
            )
            fig_scat.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig_scat, use_container_width=True)

        with col_f2:
            # Group duration into bins: Short (<15s), Medium (15s-30s), Long (30s-60s), Super Long (>60s)
            def bin_duration(d):
                if d <= 15:
                    return "Ngắn (<15 giây)"
                elif d <= 30:
                    return "Trung bình (15s-30s)"
                elif d <= 60:
                    return "Dài (30s-60s)"
                else:
                    return "Rất dài (>60 giây)"

            df_duration["duration_bin"] = df_duration["video_duration"].apply(
                bin_duration
            )
            df_duration_agg = (
                df_duration.groupby("duration_bin")
                .agg(
                    avg_views=("play_count", "mean"),
                    avg_eng=("engagement_rate", "mean"),
                    video_count=("video_id", "count"),
                )
                .reset_index()
                .sort_values("avg_views", ascending=False)
            )

            fig_bin = px.bar(
                df_duration_agg,
                x="duration_bin",
                y="avg_views",
                color="avg_eng",
                color_continuous_scale="Viridis",
                title="Lượt xem & Tương tác trung bình theo nhóm thời lượng",
                labels={"duration_bin": "Nhóm thời lượng", "avg_views": "Lượt xem trung bình"},
                text="video_count",
            )
            fig_bin.update_layout(**PLOTLY_LAYOUT)
            fig_bin.update_traces(texttemplate="Số video: %{text}", textposition="outside")
            st.plotly_chart(fig_bin, use_container_width=True)

        # Resolution distribution (Vertical vs Landscape)
        st.markdown(
            "<div class='section-header'>Đánh giá tỷ lệ khung hình</div>",
            unsafe_allow_html=True,
        )

        def calculate_aspect_ratio(row):
            w, h = row["video_width"], row["video_height"]
            if pd.isna(w) or pd.isna(h) or w == 0 or h == 0:
                return "Unknown"
            ratio = h / w
            if ratio > 1.2:
                return "Dọc (Chuẩn 9:16)"
            elif ratio < 0.8:
                return "Ngang (Landscape)"
            else:
                return "Vuông (1:1)"

        df_latest = df_latest.copy()
        df_latest["orientation"] = df_latest.apply(calculate_aspect_ratio, axis=1)
        df_orient = (
            df_latest.groupby("orientation")
            .agg(
                count=("video_id", "count"),
                avg_views=("play_count", "mean"),
                avg_eng=("engagement_rate", "mean"),
            )
            .reset_index()
        )

        col_res1, col_res2 = st.columns(2)
        with col_res1:
            fig_orient_pie = px.pie(
                df_orient,
                names="orientation",
                values="count",
                title="Phân bổ tỷ lệ khung hình (Trang Explore)",
                color="orientation",
                color_discrete_map={
                    "Dọc (Chuẩn 9:16)": "#FE2C55",
                    "Ngang (Landscape)": "#1E90FF",
                    "Vuông (1:1)": "#FFD93D",
                    "Unknown": "#636e72",
                },
                hole=0.4,
            )
            fig_orient_pie.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig_orient_pie, use_container_width=True)

        with col_res2:
            fig_orient_bar = px.bar(
                df_orient,
                x="orientation",
                y="avg_views",
                color="avg_eng",
                color_continuous_scale="Magenta",
                title="Lượt xem trung bình theo tỷ lệ khung hình",
                labels={"orientation": "Tỷ lệ khung hình", "avg_views": "Lượt xem trung bình"},
            )
            fig_orient_bar.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig_orient_bar, use_container_width=True)

        # ── Interactive: Video list by aspect ratio ──
        st.markdown(
            "<div class='section-header'>📋 Danh sách video theo tỷ lệ khung hình</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div class='insight-box'>
            <span class='insight-icon'>Hướng dẫn:</span>
            Chọn một tỷ lệ khung hình bên dưới để xem danh sách tất cả video thuộc loại đó.
            Bạn có thể sắp xếp theo lượt xem hoặc tỷ lệ tương tác để tìm ra định dạng tối ưu cho nội dung của mình.
        </div>
        """,
            unsafe_allow_html=True,
        )

        orientation_options = sorted(df_latest["orientation"].dropna().unique().tolist())
        if orientation_options:
            # Build label with video count for each option
            orient_labels = {
                o: f"{o}  ({len(df_latest[df_latest['orientation'] == o])} video)"
                for o in orientation_options
            }
            selected_orient_label = st.selectbox(
                "Chọn tỷ lệ khung hình để xem danh sách video:",
                options=list(orient_labels.values()),
                index=0,
                key="orient_select",
            )
            # Map label back to original orientation value
            selected_orient = [
                k for k, v in orient_labels.items() if v == selected_orient_label
            ][0]

            df_orient_vids = (
                df_latest[df_latest["orientation"] == selected_orient]
                .copy()
                .sort_values("play_count", ascending=False)
            )

            if not df_orient_vids.empty:
                st.markdown(
                    f"**Tìm thấy {len(df_orient_vids)} video** thuộc khung hình **{selected_orient}**"
                )

                orient_display_cols = {
                    "video_cover_url": "Cover",
                    "category_name": "Danh mục",
                    "video_desc": "Mô tả",
                    "author_nickname": "Creator",
                    "author_followers": "Followers",
                    "play_count": "Lượt xem",
                    "like_count": "Lượt thích",
                    "engagement_rate": "Tương tác %",
                    "video_duration": "Thời lượng (s)",
                    "video_width": "Chiều rộng",
                    "video_height": "Chiều cao",
                    "video_play_url": "Xem video",
                }
                df_orient_disp = df_orient_vids[
                    list(orient_display_cols.keys())
                ].rename(columns=orient_display_cols)

                st.dataframe(
                    df_orient_disp,
                    column_config={
                        "Cover": st.column_config.ImageColumn("Cover", width="small"),
                        "Xem video": st.column_config.LinkColumn(
                            "Xem video", display_text="▶ Play"
                        ),
                        "Followers": st.column_config.NumberColumn(format="%d 👥"),
                        "Lượt xem": st.column_config.NumberColumn(format="%d 👀"),
                        "Lượt thích": st.column_config.NumberColumn(format="%d ❤️"),
                        "Tương tác %": st.column_config.NumberColumn(
                            format="%.2f%% 🔥"
                        ),
                    },
                    use_container_width=True,
                    hide_index=True,
                    height=500,
                )
            else:
                st.info("Không tìm thấy video nào thuộc khung hình này.")
    else:
        st.info("Không có dữ liệu thời lượng video trong khoảng thời gian đã chọn.")


# ── TAB 4: AUDIO & SOUNDTRACK TRENDS ──────────────────────────────────
with tab_audio:
    st.markdown(
        "<div class='section-header'>Phân tích hiệu suất âm thanh (Soundtrack)</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>Trình nghe nhạc tích hợp:</span> 
        Sử dụng danh sách bên dưới để **nghe trực tiếp các đoạn nhạc xu hướng** được cào thời gian thực từ TikTok API. 
        Việc sử dụng các bản nhạc đang hot này sẽ giúp video của bạn dễ tiếp cận thuật toán tìm kiếm và trang FYP (Dành cho bạn) hơn.
    </div>
    """,
        unsafe_allow_html=True,
    )

    df_audio = df_latest[
        df_latest["music_title"].notna() & (df_latest["music_title"] != "")
    ].copy()

    if not df_audio.empty:
        df_audio_agg = (
            df_audio.groupby(["music_title", "music_author", "music_play_url"])
            .agg(
                videos_using_sound=("video_id", "count"),
                total_views=("play_count", "sum"),
                total_likes=("like_count", "sum"),
                avg_engagement_rate=("engagement_rate", "mean"),
            )
            .reset_index()
            .sort_values(by="total_views", ascending=False)
        )

        # Audio Auditing Player
        st.markdown("### Trình nghe thử âm thanh xu hướng")
        selected_song = st.selectbox(
            "Chọn đoạn nhạc để nghe thử:",
            options=df_audio_agg["music_title"].head(15).tolist(),
        )
        song_row = df_audio_agg[df_audio_agg["music_title"] == selected_song].iloc[0]
        st.markdown(
            f"**Nghệ sĩ:** {song_row['music_author']} | **Lượt xem trên Explore:** {int(song_row['total_views']):,} lượt xem"
        )
        if song_row["music_play_url"] and song_row["music_play_url"].startswith("http"):
            st.audio(song_row["music_play_url"])
        else:
            st.warning("Liên kết nghe thử không khả dụng hoặc đã hết hạn.")

        st.markdown("---")
        # Format table
        df_audio_disp = df_audio_agg.head(20).copy()
        df_audio_disp = df_audio_disp.rename(
            columns={
                "music_title": "Tên bài hát",
                "music_author": "Nghệ sĩ",
                "videos_using_sound": "Số lượng video",
                "total_views": "Tổng lượt xem",
                "total_likes": "Tổng lượt thích",
                "avg_engagement_rate": "Tỷ lệ tương tác TB %",
            }
        )

        # Split into chart and table
        col_aud1, col_aud2 = st.columns([1, 1])

        with col_aud1:
            fig_audio = px.bar(
                df_audio_agg.head(10),
                x="total_views",
                y="music_title",
                orientation="h",
                color="videos_using_sound",
                color_continuous_scale="Tealgrn",
                title="Top 10 âm thanh theo tổng lượt xem",
                labels={"total_views": "Tổng lượt xem", "music_title": "Tên bài hát"},
                hover_data=["music_author", "avg_engagement_rate"],
            )
            fig_audio.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig_audio, use_container_width=True)

        with col_aud2:
            st.markdown("**Bảng xếp hạng âm thanh hot**")
            st.dataframe(
                df_audio_disp[
                    [
                        "Tên bài hát",
                        "Nghệ sĩ",
                        "Số lượng video",
                        "Tổng lượt xem",
                        "Tỷ lệ tương tác TB %",
                    ]
                ],
                column_config={
                    "Tổng lượt xem": st.column_config.NumberColumn(format="%d lượt xem"),
                    "Tỷ lệ tương tác TB %": st.column_config.NumberColumn(
                        format="%.2f%%"
                    ),
                },
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("Không tìm thấy siêu dữ liệu âm thanh trong cơ sở dữ liệu.")


# ── TAB 5: HASHTAGS & CONTENT THEMES ──────────────────────────────────
with tab_hashtag:
    st.markdown(
        "<div class='section-header'>Phân tích Hashtag và chủ đề nội dung</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>Phân tích chủ đề:</span> 
        Hashtag là các từ khóa phân loại nội dung mà thuật toán TikTok sử dụng để phân phối video đến đúng đối tượng. 
        Biểu đồ bên dưới thể hiện <strong>khối lượng lượt xem và mức độ tương tác trung bình</strong> của từng hashtag đang xuất hiện trên trang Explore.
    </div>
    """,
        unsafe_allow_html=True,
    )

    hashtags_list = []
    for _, row in df_latest.iterrows():
        desc = row["video_desc"] or ""
        plays = row["play_count"] or 0
        likes = row["like_count"] or 0
        eng = row["engagement_rate"] or 0.0

        # Extract hashtags from description
        found = re.findall(r"#([a-zA-Z0-9_\u00C0-\u024F\u1E00-\u1EFF]+)", desc)
        for h in found:
            hashtags_list.append(
                {
                    "hashtag": f"#{h.lower()}",
                    "views": plays,
                    "likes": likes,
                    "engagement": eng,
                }
            )

        # Extract from JSONB hashtag_list field
        ht_list = row.get("hashtag_list")
        if isinstance(ht_list, list):
            for h in ht_list:
                if isinstance(h, str) and h.strip():
                    tag = f"#{h.lower()}"
                    hashtags_list.append(
                        {
                            "hashtag": tag,
                            "views": plays,
                            "likes": likes,
                            "engagement": eng,
                        }
                    )

    if hashtags_list:
        df_hash = pd.DataFrame(hashtags_list)
        df_hash = df_hash.drop_duplicates()
        df_hash_agg = (
            df_hash.groupby("hashtag")
            .agg(
                total_views=("views", "sum"),
                total_likes=("likes", "sum"),
                avg_engagement=("engagement", "mean"),
                hashtag_count=("hashtag", "count"),
            )
            .reset_index()
        )

        col_h1, col_h2 = st.columns(2)
        with col_h1:
            top_by_views = df_hash_agg.sort_values("total_views", ascending=True).tail(
                15
            )
            fig_hv = px.bar(
                top_by_views,
                y="hashtag",
                x="total_views",
                orientation="h",
                title="Top 15 Hashtag theo tổng lượt xem",
                labels={"total_views": "Tổng lượt xem", "hashtag": "Hashtag"},
                color="avg_engagement",
                color_continuous_scale="Viridis",
            )
            fig_hv.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig_hv, use_container_width=True)

        with col_h2:
            top_by_likes = df_hash_agg.sort_values("total_likes", ascending=True).tail(
                15
            )
            fig_hl = px.bar(
                top_by_likes,
                y="hashtag",
                x="total_likes",
                orientation="h",
                title="Top 15 Hashtag theo tổng lượt thích",
                labels={"total_likes": "Tổng lượt thích", "hashtag": "Hashtag"},
                color="hashtag_count",
                color_continuous_scale="Sunsetdark",
            )
            fig_hl.update_layout(**PLOTLY_LAYOUT)
            st.plotly_chart(fig_hl, use_container_width=True)

        # Topic Matrix table
        st.markdown(
            "<div class='section-header'>Bảng phân tích toàn bộ Hashtag</div>",
            unsafe_allow_html=True,
        )
        st.dataframe(
            df_hash_agg.sort_values(by="total_views", ascending=False).rename(
                columns={
                    "hashtag": "Hashtag",
                    "total_views": "Tổng lượt xem",
                    "total_likes": "Tổng lượt thích",
                    "avg_engagement": "Tỷ lệ tương tác TB %",
                    "hashtag_count": "Số lần xuất hiện trên Explore",
                }
            ),
            column_config={
                "Tổng lượt xem": st.column_config.NumberColumn(format="%d lượt xem"),
                "Tổng lượt thích": st.column_config.NumberColumn(format="%d lượt thích"),
                "Tỷ lệ tương tác TB %": st.column_config.NumberColumn(format="%.2f%%"),
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Không tìm thấy hashtag nào trong mô tả của các video đã chọn.")


# ── TAB 6: VIDEO AUDITING TOOL ─────────────────────────────────
with tab_player:
    st.markdown(
        "<div class='section-header'>Công cụ kiểm tra video & So sánh theo danh mục</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>Hướng dẫn sử dụng:</span>
        Chọn một video từ danh sách bên dưới để xem chi tiết hiệu suất và so sánh với <strong>mức trung bình của danh mục</strong>. 
        Hệ thống sẽ tự động tính toán xem video đó đang <strong>vượt trội hay kém hơn</strong> so với benchmark của nhóm nội dung tương ứng.
    </div>
    """,
        unsafe_allow_html=True,
    )

    if not df_latest.empty:
        df_latest["select_label"] = (
            df_latest["category_name"].fillna("N/A")
            + " — @"
            + df_latest["author_username"].fillna("Unknown")
            + " — "
            + df_latest["video_desc"].str.slice(0, 50).fillna("")
            + " ("
            + df_latest["video_id"].astype(str)
            + ")"
        )

        selected = st.selectbox(
            "Chọn video để kiểm tra:", options=df_latest["select_label"].tolist()
        )
        row = df_latest[df_latest["select_label"] == selected].iloc[0]

        # Calculate category benchmarks
        cat_name = row["category_name"]
        df_cat_subset = df_latest[df_latest["category_name"] == cat_name]

        avg_cat_views = (
            df_cat_subset["play_count"].mean() if not df_cat_subset.empty else 1.0
        )
        avg_cat_eng = (
            df_cat_subset["engagement_rate"].mean() if not df_cat_subset.empty else 1.0
        )

        view_perf_ratio = (
            row["play_count"] / avg_cat_views if avg_cat_views > 0 else 1.0
        )
        eng_perf_ratio = (
            row["engagement_rate"] / avg_cat_eng if avg_cat_eng > 0 else 1.0
        )

        col_v, col_d = st.columns([3, 2])

        with col_v:
            video_url = row.get("video_play_url") or row.get("video_download_url")
            if isinstance(video_url, str) and video_url.strip().startswith("http"):
                st.video(video_url)
            else:
                st.warning(
                    "Liên kết video trực tiếp đã hết hạn (TikTok URL có thời hạn 24 giờ). Hiển thị ảnh bìa thay thế:"
                )
                cover = row.get("video_cover_url")
                if isinstance(cover, str) and cover.strip().startswith("http"):
                    st.image(cover, caption="Ảnh bìa video")

        with col_d:
            st.markdown(f"### {row.get('video_desc', 'N/A')}")
            st.markdown(
                f"**Creator:** @{row.get('author_username', 'N/A')} ({row.get('author_nickname', '')})"
            )

            # Creator detail
            verification_str = (
                "Tài khoản Tích Xanh (Verified)" if row["author_verified"] else "Tài khoản thường (Chưa xác thực)"
            )
            st.markdown(
                f"**Số lượng Follower:** {row['author_followers']:,} | **Trạng thái:** {verification_str}"
            )

            # Benchmarks
            st.markdown("#### So sánh với mức trung bình của danh mục")

            # View indicator
            if view_perf_ratio >= 1.0:
                st.success(
                    f"Lượt xem: **{view_perf_ratio:.2f}x** CAO HƠN mức trung bình danh mục `{cat_name}`."
                )
            else:
                st.warning(
                    f"Lượt xem: **{view_perf_ratio:.2f}x** THẤP HƠN mức trung bình danh mục `{cat_name}`."
                )

            # Engagement indicator
            if eng_perf_ratio >= 1.0:
                st.success(
                    f"Tỷ lệ tương tác: **{eng_perf_ratio:.2f}x** CAO HƠN mức trung bình danh mục `{cat_name}`."
                )
            else:
                st.warning(
                    f"Tỷ lệ tương tác: **{eng_perf_ratio:.2f}x** THẤP HƠN mức trung bình danh mục `{cat_name}`."
                )

            st.markdown("---")
            # Metrics grid
            md_c1, md_c2 = st.columns(2)
            with md_c1:
                st.markdown(f"**Danh mục:** {row.get('category_name', 'N/A')}")
                st.markdown(f"**Thời lượng:** {row.get('video_duration', 'N/A')} giây")
                w, h = row.get("video_width"), row.get("video_height")
                res = f"{int(w)}×{int(h)}" if pd.notna(w) and pd.notna(h) else "N/A"
                st.markdown(f"**Độ phân giải:** {res}")
            with md_c2:
                st.markdown(f"**Tỷ lệ tương tác:** `{row['engagement_rate']:.2f}%`")
                st.markdown(f"**Nhạc nền:** {row.get('music_title', 'N/A')}")
                st.markdown(f"**Nghệ sĩ:** {row.get('music_author', '')}")

            st.markdown("---")
            st.markdown("**Chỉ số tương tác của khán giả**")

            # Stats display
            st.markdown(
                f"**Lượt xem:** {int(row['play_count']):,}"
                if pd.notna(row["play_count"])
                else "Lượt xem: N/A"
            )
            st.markdown(
                f"**Lượt thích:** {int(row['like_count']):,}"
                if pd.notna(row["like_count"])
                else "Lượt thích: N/A"
            )
            st.markdown(
                f"**Bình luận:** {int(row['comment_count']):,}"
                if pd.notna(row["comment_count"])
                else "Bình luận: N/A"
            )
            st.markdown(
                f"**Chia sẻ:** {int(row['share_count']):,}"
                if pd.notna(row["share_count"])
                else "Chia sẻ: N/A"
            )
            st.markdown(
                f"**Lưu video:** {int(row['collect_count']):,}"
                if pd.notna(row["collect_count"])
                else "Lưu video: N/A"
            )

            # Historical trend chart
            vid = row["video_id"]
            df_hist = df_raw[df_raw["video_id"] == vid].sort_values("crawled_date")
            if len(df_hist) > 1:
                st.markdown("---")
                st.markdown("**Biểu đồ tăng trưởng theo thời gian:**")
                fig_h = go.Figure()
                fig_h.add_trace(
                    go.Scatter(
                        x=df_hist["crawled_date"],
                        y=df_hist["play_count"],
                        mode="lines+markers",
                        name="Lượt xem",
                        line=dict(color="#25F4EE", width=2),
                    )
                )
                fig_h.add_trace(
                    go.Scatter(
                        x=df_hist["crawled_date"],
                        y=df_hist["like_count"],
                        mode="lines+markers",
                        name="Lượt thích",
                        line=dict(color="#FE2C55", width=2),
                    )
                )
                fig_h.update_layout(
                    height=200, margin=dict(l=0, r=0, t=10, b=0), **PLOTLY_LAYOUT
                )
                st.plotly_chart(fig_h, use_container_width=True)
            else:
                st.info("Video này mới được cào một lần. Chưa có dữ liệu lịch sử.")
    else:
        st.info("Không tìm thấy video nào.")


# ── TAB 8: ML TREND PREDICTOR ──────────────────────────────────────
with tab_ml:
    st.markdown(
        "<div class='section-header'>ML Trend Predictor</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>Model Overview:</span> 
        Hệ thống sử dụng mô hình học máy <strong>Random Forest Regressor</strong> phân tích mối tương quan giữa các đặc trưng: 
        thời lượng, lượng follower của tác giả, tích xanh, quảng cáo, danh mục và số lượng hashtag để dự đoán 
        số lượt xem tiềm năng của video mới.
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 1. Prepare ML dataset
    df_ml = df.copy()

    # Helper to safely parse hashtag count
    def parse_hashtag_count(x):
        if isinstance(x, list):
            return len(x)
        if isinstance(x, str):
            try:
                import json

                parsed = json.loads(x)
                if isinstance(parsed, list):
                    return len(parsed)
            except Exception:
                pass
        return 0

    # Clean and parse features
    df_ml["hashtag_count"] = df_ml["hashtag_list"].apply(parse_hashtag_count)
    df_ml = df_ml.dropna(
        subset=["play_count", "video_duration", "author_followers", "category_name"]
    )

    # We only train on videos with positive views and duration
    df_ml = df_ml[(df_ml["play_count"] > 0) & (df_ml["video_duration"] > 0)]

    if len(df_ml) < 10:
        st.warning(
            "Không đủ dữ liệu để huấn luyện mô hình Machine Learning. Cần tối thiểu 10 bản ghi video."
        )
    else:
        # Preprocessing & Model Training
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import mean_absolute_error, r2_score
        from sklearn.model_selection import train_test_split

        # Categorical encoding (One-Hot) for categories
        all_cats = sorted(df["category_name"].dropna().unique())

        # Features and target
        features = [
            "video_duration",
            "author_followers",
            "author_verified",
            "is_ad",
            "hashtag_count",
        ]

        # Build features DataFrame
        X = df_ml[features].copy()

        # One-hot encode category
        for cat in all_cats:
            X[f"cat_{cat}"] = (df_ml["category_name"] == cat).astype(int)

        y = df_ml["play_count"]

        # Train model
        @st.cache_resource
        def train_ml_model(X_data, y_data):
            X_train, X_test, y_train, y_test = train_test_split(
                X_data, y_data, test_size=0.2, random_state=42
            )

            # Train RF Regressor
            model = RandomForestRegressor(
                n_estimators=100, random_state=42, max_depth=10
            )
            model.fit(X_train, y_train)

            # Predict & Score
            preds = model.predict(X_test)
            r2 = r2_score(y_test, preds)
            mae = mean_absolute_error(y_test, preds)

            # Feature importances
            importances = model.feature_importances_
            feat_imp_df = pd.DataFrame(
                {"Feature": X_data.columns, "Importance": importances}
            ).sort_values(by="Importance", ascending=False)

            return model, r2, mae, feat_imp_df

        with st.spinner(
            "Đang huấn luyện mô hình Random Forest trên dữ liệu hiện tại..."
        ):
            model, r2, mae, feat_imp_df = train_ml_model(X, y)

        # Display Metrics
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown(
                f"""
            <div style='background: #16161a; padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);'>
                <h4 style='margin-top:0; color:#25F4EE;'>Model Performance Metrics</h4>
                <p><strong>Mô hình:</strong> Random Forest Regressor</p>
                <p><strong>Độ chính xác (R² Score):</strong> <code>{r2:.2f}</code></p>
                <p><strong>Sai số tuyệt đối trung bình (MAE):</strong> <code>{int(mae):,} views</code></p>
                <small style='color:#8E8E93;'>* R² Score nằm trong khoảng từ 0 đến 1, đo mức độ tương quan của mô hình với dữ liệu thực tế.</small>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col_m2:
            feat_imp_df_disp = feat_imp_df.copy()
            feat_imp_df_disp["Feature"] = feat_imp_df_disp["Feature"].apply(
                lambda name: name.replace("cat_", "Category: ")
                .replace("video_duration", "Duration (seconds)")
                .replace("author_followers", "Followers Count")
                .replace("author_verified", "Is Verified Account")
                .replace("is_ad", "Is Sponsored/Ad")
                .replace("hashtag_count", "Hashtags Count")
            )

            fig_imp = px.bar(
                feat_imp_df_disp.head(8).sort_values(by="Importance", ascending=True),
                x="Importance",
                y="Feature",
                orientation="h",
                title="Feature Importance",
                color="Importance",
                color_continuous_scale="Mint",
            )
            fig_imp.update_layout(
                height=230, margin=dict(l=0, r=0, t=30, b=0), **PLOTLY_LAYOUT
            )
            st.plotly_chart(fig_imp, use_container_width=True)

        # ──────────────────────────────────────────────────────────────
        # ML SECTION 1: Best Video Duration Recommendation
        # ──────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown(
            "<div class='section-header'>⏱️ Best Video Duration Recommendation</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div class='insight-box'>
            <span class='insight-icon'>Phân tích thời lượng tối ưu:</span>
            Biểu đồ dưới đây phân tích mối quan hệ giữa <strong>thời lượng video</strong> và <strong>tỷ lệ tương tác (engagement rate)</strong>.
            Khoảng thời lượng được đánh dấu là vùng có engagement cao nhất, giúp bạn xác định độ dài video lý tưởng cho nội dung của mình.
        </div>
        """,
            unsafe_allow_html=True,
        )

        df_dur_ml = df_ml[df_ml["video_duration"] > 0].copy()

        if not df_dur_ml.empty:
            # Create fine-grained duration bins (every 5 seconds)
            import numpy as np

            max_dur = min(int(df_dur_ml["video_duration"].quantile(0.95)), 180)
            bins = list(range(0, max_dur + 5, 5))
            labels = [f"{b}-{b+5}s" for b in bins[:-1]]
            df_dur_ml["dur_bin"] = pd.cut(
                df_dur_ml["video_duration"].clip(upper=max_dur),
                bins=bins,
                labels=labels,
                include_lowest=True,
            )

            df_dur_agg = (
                df_dur_ml.groupby("dur_bin", observed=True)
                .agg(
                    avg_engagement=("engagement_rate", "mean"),
                    avg_views=("play_count", "mean"),
                    video_count=("video_id", "count"),
                )
                .reset_index()
            )
            df_dur_agg = df_dur_agg[df_dur_agg["video_count"] >= 2]  # min samples

            if not df_dur_agg.empty:
                # Find the best bin
                best_bin = df_dur_agg.loc[df_dur_agg["avg_engagement"].idxmax()]

                col_dur1, col_dur2 = st.columns([3, 1])

                with col_dur1:
                    # Color bars: highlight the best bin
                    colors = [
                        "#FE2C55" if row["dur_bin"] == best_bin["dur_bin"] else "#25F4EE"
                        for _, row in df_dur_agg.iterrows()
                    ]

                    fig_dur_rec = go.Figure()
                    fig_dur_rec.add_trace(
                        go.Bar(
                            x=df_dur_agg["dur_bin"].astype(str),
                            y=df_dur_agg["avg_engagement"],
                            marker_color=colors,
                            text=df_dur_agg["video_count"].apply(lambda v: f"{v} video"),
                            textposition="outside",
                            hovertemplate=(
                                "<b>%{x}</b><br>"
                                "Engagement TB: %{y:.2f}%<br>"
                                "Lượt xem TB: %{customdata:,.0f}<br>"
                                "<extra></extra>"
                            ),
                            customdata=df_dur_agg["avg_views"],
                        )
                    )
                    fig_dur_rec.update_layout(
                        title="Tỷ lệ tương tác trung bình theo khoảng thời lượng video",
                        xaxis_title="Khoảng thời lượng",
                        yaxis_title="Engagement Rate TB (%)",
                        **PLOTLY_LAYOUT,
                    )
                    st.plotly_chart(fig_dur_rec, use_container_width=True)

                with col_dur2:
                    st.markdown(
                        f"""
                    <div style='background: linear-gradient(135deg, rgba(254, 44, 85, 0.12) 0%, rgba(37, 244, 238, 0.12) 100%);
                                padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08); text-align: center;'>
                        <div style='font-size: 0.85rem; color: #8E8E93; text-transform: uppercase; letter-spacing: 1.5px;'>Thời lượng tối ưu</div>
                        <div style='font-size: 2.2rem; font-weight: 800; color: #FE2C55; margin: 0.8rem 0;'>{best_bin['dur_bin']}</div>
                        <div style='font-size: 0.95rem; color: #E5E5EA;'>Engagement TB: <strong>{best_bin['avg_engagement']:.2f}%</strong></div>
                        <div style='font-size: 0.85rem; color: #8E8E93; margin-top: 0.5rem;'>{int(best_bin['video_count'])} video phân tích</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Also show top 3 duration ranges
                    st.markdown("")
                    top3_dur = df_dur_agg.nlargest(3, "avg_engagement")
                    st.markdown("**Top 3 khoảng thời lượng:**")
                    for i, (_, r) in enumerate(top3_dur.iterrows()):
                        medal = ["🥇", "🥈", "🥉"][i]
                        st.markdown(
                            f"{medal} **{r['dur_bin']}** — {r['avg_engagement']:.2f}% engagement"
                        )

        # ──────────────────────────────────────────────────────────────
        # ML SECTION 2: Best Posting Time Prediction
        # ──────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown(
            "<div class='section-header'>🕐 Best Posting Time Prediction</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div class='insight-box'>
            <span class='insight-icon'>Phân tích thời gian đăng tải:</span>
            Dựa trên thời gian tạo video (<code>created_at</code>) của các video thịnh hành trên Explore,
            hệ thống phân tích <strong>khung giờ và ngày trong tuần</strong> nào có tỷ lệ tương tác cao nhất.
            Đây là gợi ý để bạn lên lịch đăng video tối ưu nhất.
        </div>
        """,
            unsafe_allow_html=True,
        )

        df_time_ml = df_ml.copy()
        df_time_ml["created_at"] = pd.to_datetime(df_time_ml["created_at"], errors="coerce")
        df_time_ml = df_time_ml.dropna(subset=["created_at"])

        if not df_time_ml.empty:
            df_time_ml["post_hour"] = df_time_ml["created_at"].dt.hour
            df_time_ml["post_dayofweek"] = df_time_ml["created_at"].dt.dayofweek  # 0=Mon
            day_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
            df_time_ml["post_day_name"] = df_time_ml["post_dayofweek"].map(
                {i: d for i, d in enumerate(day_names)}
            )

            col_time1, col_time2 = st.columns([3, 1])

            with col_time1:
                # Heatmap: day of week x hour
                df_heatmap = (
                    df_time_ml.groupby(["post_day_name", "post_dayofweek", "post_hour"])
                    .agg(
                        avg_engagement=("engagement_rate", "mean"),
                        video_count=("video_id", "count"),
                    )
                    .reset_index()
                    .sort_values(["post_dayofweek", "post_hour"])
                )

                # Pivot for heatmap
                heatmap_pivot = df_heatmap.pivot_table(
                    index="post_day_name",
                    columns="post_hour",
                    values="avg_engagement",
                    aggfunc="mean",
                )
                # Reorder days
                heatmap_pivot = heatmap_pivot.reindex(day_names)

                fig_heatmap = go.Figure(
                    data=go.Heatmap(
                        z=heatmap_pivot.values,
                        x=[f"{h}:00" for h in heatmap_pivot.columns],
                        y=heatmap_pivot.index,
                        colorscale=[
                            [0, "#0c0c0e"],
                            [0.25, "#1a1a2e"],
                            [0.5, "#16213e"],
                            [0.75, "#FE2C55"],
                            [1, "#FFD93D"],
                        ],
                        hovertemplate=(
                            "<b>%{y} - %{x}</b><br>"
                            "Engagement TB: %{z:.2f}%<br>"
                            "<extra></extra>"
                        ),
                    )
                )
                fig_heatmap.update_layout(
                    title="Heatmap tỷ lệ tương tác theo Ngày × Giờ đăng",
                    xaxis_title="Giờ đăng video",
                    yaxis_title="Ngày trong tuần",
                    **PLOTLY_LAYOUT,
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)

            with col_time2:
                # Find best hour and best day
                hour_agg = (
                    df_time_ml.groupby("post_hour")
                    .agg(avg_eng=("engagement_rate", "mean"), count=("video_id", "count"))
                    .reset_index()
                )
                hour_agg = hour_agg[hour_agg["count"] >= 2]
                best_hour = hour_agg.loc[hour_agg["avg_eng"].idxmax()] if not hour_agg.empty else None

                day_agg = (
                    df_time_ml.groupby(["post_day_name", "post_dayofweek"])
                    .agg(avg_eng=("engagement_rate", "mean"), count=("video_id", "count"))
                    .reset_index()
                    .sort_values("post_dayofweek")
                )
                day_agg = day_agg[day_agg["count"] >= 2]
                best_day = day_agg.loc[day_agg["avg_eng"].idxmax()] if not day_agg.empty else None

                if best_hour is not None and best_day is not None:
                    st.markdown(
                        f"""
                    <div style='background: linear-gradient(135deg, rgba(254, 44, 85, 0.12) 0%, rgba(37, 244, 238, 0.12) 100%);
                                padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08); text-align: center;'>
                        <div style='font-size: 0.85rem; color: #8E8E93; text-transform: uppercase; letter-spacing: 1.5px;'>Khung giờ vàng</div>
                        <div style='font-size: 2.2rem; font-weight: 800; color: #25F4EE; margin: 0.5rem 0;'>{int(best_hour['post_hour'])}:00 - {int(best_hour['post_hour'])+1}:00</div>
                        <div style='font-size: 0.95rem; color: #E5E5EA;'>Engagement TB: <strong>{best_hour['avg_eng']:.2f}%</strong></div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                    st.markdown("")
                    st.markdown(
                        f"""
                    <div style='background: linear-gradient(135deg, rgba(255, 217, 61, 0.12) 0%, rgba(155, 89, 182, 0.12) 100%);
                                padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08); text-align: center;'>
                        <div style='font-size: 0.85rem; color: #8E8E93; text-transform: uppercase; letter-spacing: 1.5px;'>Ngày tối ưu</div>
                        <div style='font-size: 2.2rem; font-weight: 800; color: #FFD93D; margin: 0.5rem 0;'>{best_day['post_day_name']}</div>
                        <div style='font-size: 0.95rem; color: #E5E5EA;'>Engagement TB: <strong>{best_day['avg_eng']:.2f}%</strong></div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Top 3 time slots
                    st.markdown("")
                    st.markdown("**Top 3 khung giờ:**")
                    top3_hours = hour_agg.nlargest(3, "avg_eng")
                    for i, (_, r) in enumerate(top3_hours.iterrows()):
                        medal = ["🥇", "🥈", "🥉"][i]
                        st.markdown(
                            f"{medal} **{int(r['post_hour'])}:00** — {r['avg_eng']:.2f}%"
                        )
        else:
            st.info("Không có dữ liệu thời gian đăng video để phân tích.")

        # ──────────────────────────────────────────────────────────────
        # ML SECTION 3: Recommended Hashtag Count
        # ──────────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown(
            "<div class='section-header'># Recommended Hashtag Count</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div class='insight-box'>
            <span class='insight-icon'>Phân tích Hashtag tối ưu:</span>
            Số lượng hashtag ảnh hưởng đến khả năng tiếp cận thuật toán TikTok.
            Quá ít hashtag khiến video khó được phân loại, quá nhiều bị coi là spam.
            Biểu đồ dưới đây cho thấy <strong>số lượng hashtag tối ưu</strong> dựa trên dữ liệu thực tế từ các video thịnh hành.
        </div>
        """,
            unsafe_allow_html=True,
        )

        df_hash_ml = df_ml.copy()

        if not df_hash_ml.empty and df_hash_ml["hashtag_count"].max() > 0:
            # Cap hashtag count at 15 for cleaner visualization
            df_hash_ml["hashtag_count_capped"] = df_hash_ml["hashtag_count"].clip(upper=15)

            df_hash_agg = (
                df_hash_ml.groupby("hashtag_count_capped")
                .agg(
                    avg_engagement=("engagement_rate", "mean"),
                    avg_views=("play_count", "mean"),
                    video_count=("video_id", "count"),
                )
                .reset_index()
                .rename(columns={"hashtag_count_capped": "hashtag_count"})
            )
            df_hash_agg = df_hash_agg[df_hash_agg["video_count"] >= 2]

            if not df_hash_agg.empty:
                best_hash = df_hash_agg.loc[df_hash_agg["avg_engagement"].idxmax()]

                col_hash1, col_hash2 = st.columns([3, 1])

                with col_hash1:
                    # Dual axis: engagement rate (bar) + avg views (line)
                    fig_hash = go.Figure()

                    # Bars for engagement
                    hash_colors = [
                        "#FE2C55" if r["hashtag_count"] == best_hash["hashtag_count"] else "#25F4EE"
                        for _, r in df_hash_agg.iterrows()
                    ]
                    fig_hash.add_trace(
                        go.Bar(
                            x=df_hash_agg["hashtag_count"],
                            y=df_hash_agg["avg_engagement"],
                            name="Engagement TB (%)",
                            marker_color=hash_colors,
                            text=df_hash_agg["video_count"].apply(lambda v: f"{v}"),
                            textposition="outside",
                            hovertemplate=(
                                "<b>%{x} hashtag(s)</b><br>"
                                "Engagement TB: %{y:.2f}%<br>"
                                "Số video: %{text}<br>"
                                "<extra></extra>"
                            ),
                        )
                    )

                    # Line for avg views on secondary axis
                    fig_hash.add_trace(
                        go.Scatter(
                            x=df_hash_agg["hashtag_count"],
                            y=df_hash_agg["avg_views"],
                            name="Lượt xem TB",
                            mode="lines+markers",
                            line=dict(color="#FFD93D", width=2),
                            marker=dict(size=8),
                            yaxis="y2",
                            hovertemplate=(
                                "<b>%{x} hashtag(s)</b><br>"
                                "Lượt xem TB: %{y:,.0f}<br>"
                                "<extra></extra>"
                            ),
                        )
                    )

                    fig_hash.update_layout(
                        title="Tỷ lệ tương tác & Lượt xem theo số lượng Hashtag",
                        xaxis_title="Số lượng Hashtag",
                        yaxis=dict(title="Engagement Rate TB (%)", side="left"),
                        yaxis2=dict(
                            title="Lượt xem trung bình",
                            side="right",
                            overlaying="y",
                            showgrid=False,
                        ),
                        legend=dict(x=0.5, y=1.15, orientation="h", xanchor="center"),
                        **PLOTLY_LAYOUT,
                    )
                    st.plotly_chart(fig_hash, use_container_width=True)

                with col_hash2:
                    st.markdown(
                        f"""
                    <div style='background: linear-gradient(135deg, rgba(254, 44, 85, 0.12) 0%, rgba(37, 244, 238, 0.12) 100%);
                                padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08); text-align: center;'>
                        <div style='font-size: 0.85rem; color: #8E8E93; text-transform: uppercase; letter-spacing: 1.5px;'>Số hashtag tối ưu</div>
                        <div style='font-size: 3rem; font-weight: 800; color: #FE2C55; margin: 0.5rem 0;'>{int(best_hash['hashtag_count'])}</div>
                        <div style='font-size: 0.95rem; color: #E5E5EA;'>Engagement TB: <strong>{best_hash['avg_engagement']:.2f}%</strong></div>
                        <div style='font-size: 0.85rem; color: #8E8E93; margin-top: 0.3rem;'>Lượt xem TB: {int(best_hash['avg_views']):,}</div>
                        <div style='font-size: 0.8rem; color: #636e72; margin-top: 0.3rem;'>{int(best_hash['video_count'])} video phân tích</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    st.markdown("")
                    st.markdown("**Top 3 số hashtag hiệu quả:**")
                    top3_hash = df_hash_agg.nlargest(3, "avg_engagement")
                    for i, (_, r) in enumerate(top3_hash.iterrows()):
                        medal = ["🥇", "🥈", "🥉"][i]
                        st.markdown(
                            f"{medal} **{int(r['hashtag_count'])} hashtag** — {r['avg_engagement']:.2f}%"
                        )

                    # Practical recommendation
                    st.markdown("")
                    optimal_range = df_hash_agg.nlargest(3, "avg_engagement")["hashtag_count"]
                    low, high = int(optimal_range.min()), int(optimal_range.max())
                    st.markdown(
                        f"""
                    <div style='background: rgba(37, 244, 238, 0.05); border: 1px dashed rgba(37, 244, 238, 0.3);
                                border-radius: 10px; padding: 0.8rem; font-size: 0.9rem; color: #E5E5EA;'>
                        💡 <strong>Gợi ý:</strong> Sử dụng từ <strong>{low}</strong> đến <strong>{high}</strong> hashtag
                        cho mỗi video để tối ưu tỷ lệ tương tác trên Explore.
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
        else:
            st.info("Không có dữ liệu hashtag để phân tích.")
