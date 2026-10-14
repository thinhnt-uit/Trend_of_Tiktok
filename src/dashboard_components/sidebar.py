"""
Sidebar navigation, interactive filters, and data export widgets.
"""

from datetime import datetime
import pandas as pd
import streamlit as st
from src.dashboard_components.data import convert_df_to_excel


def render_sidebar(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Render sidebar filters and export button, returning the filtered DataFrame."""
    st.sidebar.markdown(
        """
    <div style='text-align: center; margin-bottom: 1.5rem;'>
        <img src='https://img.icons8.com/color/96/tiktok.png' width='55'/>
        <h3 style='margin-top: 0.5rem; font-weight: 700; color: #fff;'>Trend Command Center</h3>
        <p style='color: #8E8E93; font-size: 0.85rem;'>TikTok Explore Trend Insights</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>For:</span>
        Content teams, creators, and analysts who want to understand what is trending, why it is trending, and which content patterns are worth replicating.
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Date filter
    dates = sorted(df_raw["crawled_date"].unique())
    selected_dates = st.sidebar.multiselect("Select Crawl Dates", options=dates, default=[])
    df = df_raw[df_raw["crawled_date"].isin(selected_dates)] if selected_dates else df_raw.copy()

    # Category filter
    categories = sorted(df["category_name"].dropna().unique())
    selected_cats = st.sidebar.multiselect("Select Category", options=categories, default=[])
    if selected_cats:
        df = df[df["category_name"].isin(selected_cats)]

    # Creator Account Filters
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Creator Profiling Filters**")

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
        ["All Accounts", "Verified Only ✓", "Unverified Only"],
    )
    if verified_filter == "Verified Only ✓":
        df = df[df["author_verified"] == True]
    elif verified_filter == "Unverified Only":
        df = df[df["author_verified"] == False]

    # Ads Filter
    if "is_ad" not in df.columns:
        df["is_ad"] = False

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

    # Excel Export
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Data Export**")
    try:
        if not df.empty:
            excel_bytes = convert_df_to_excel(df)
            today_str = datetime.now().strftime("%Y%m%d")
            st.sidebar.download_button(
                label="📥 Download Excel (Formatted)",
                data=excel_bytes,
                file_name=f"TikTok_Explore_Analytics_{today_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        else:
            st.sidebar.info("No data available to export.")
    except Exception as excel_err:
        st.sidebar.error(f"Error generating Excel: {excel_err}")

    return df
