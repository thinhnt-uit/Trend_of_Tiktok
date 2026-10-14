"""
Tab 2 - Viral Leaderboard (enhanced).
Sortable table with virality_velocity, video_age_hours, engagement, tier.
"""

import pandas as pd
import streamlit as st


def render_tab_leaderboard(df_latest: pd.DataFrame):
    """Render Tab 2: Viral Leaderboard - enhanced sortable table."""
    st.markdown(
        """
        <div class='insight-box'>
            <span class='insight-icon'>Strategic insight:</span>
            Sort by <strong>Engagement %</strong> to find niche gems, or by <strong>Views/hr</strong>
            to see what is spreading fastest right now.
            Videos with high engagement but modest views are
            <strong>high-quality underexposed content</strong> worth studying.
        </div>
        """,
        unsafe_allow_html=True,
    )

    sort_col = st.selectbox(
        "Sort leaderboard by:",
        options=["Views", "Engagement %", "Views/hr", "Likes", "Comments", "Shares"],
        index=0,
        key="lb_sort",
    )
    sort_map = {
        "Views": "play_count",
        "Engagement %": "engagement_rate",
        "Views/hr": "virality_velocity",
        "Likes": "like_count",
        "Comments": "comment_count",
        "Shares": "share_count",
    }
    sort_field = sort_map[sort_col]
    if sort_field in df_latest.columns:
        df_lb = df_latest.copy().sort_values(by=sort_field, ascending=False)
    else:
        df_lb = df_latest.copy().sort_values(by="play_count", ascending=False)

    display_cols = {
        "video_cover_url":   "Cover",
        "category_name":     "Category",
        "video_desc":        "Description",
        "author_nickname":   "Creator",
        "creator_tier":      "Tier",
        "author_followers":  "Followers",
        "play_count":        "Views",
        "virality_velocity": "Views/hr",
        "video_age_hours":   "Age (hrs)",
        "engagement_rate":   "Engagement %",
        "like_count":        "Likes",
        "comment_count":     "Comments",
        "share_count":       "Shares",
        "repost_count":      "Reposts",
        "author_verified":   "Verified",
        "is_ad":             "Ad",
        "video_play_url":    "Watch",
    }
    valid_cols = [c for c in display_cols if c in df_lb.columns]
    df_disp = df_lb[valid_cols].rename(columns={c: display_cols[c] for c in valid_cols})

    col_cfg = {
        "Cover":        st.column_config.ImageColumn("Cover", width="small"),
        "Watch":        st.column_config.LinkColumn("Watch", display_text="Play"),
        "Tier":         st.column_config.TextColumn("Tier"),
        "Followers":    st.column_config.NumberColumn(format="%d"),
        "Views":        st.column_config.NumberColumn(format="%d"),
        "Views/hr":     st.column_config.NumberColumn(format="%d"),
        "Age (hrs)":    st.column_config.NumberColumn(format="%.1f"),
        "Engagement %": st.column_config.NumberColumn(format="%.2f%%"),
        "Likes":        st.column_config.NumberColumn(format="%d"),
        "Comments":     st.column_config.NumberColumn(format="%d"),
        "Shares":       st.column_config.NumberColumn(format="%d"),
        "Reposts":      st.column_config.NumberColumn(format="%d"),
        "Verified":     st.column_config.CheckboxColumn("Verified"),
        "Ad":           st.column_config.CheckboxColumn("Ad"),
    }
    st.dataframe(df_disp, column_config=col_cfg, use_container_width=True, hide_index=True)

    total_v = len(df_lb)
    hot_count = 0
    if "virality_velocity" in df_lb.columns:
        med = df_lb["virality_velocity"].median()
        hot_count = int((df_lb["virality_velocity"] > med).sum())

    top_tier = "N/A"
    if "creator_tier" in df_lb.columns and not df_lb.empty:
        vc = df_lb["creator_tier"].value_counts()
        if not vc.empty:
            top_tier = vc.index[0]

    s1, s2, s3 = st.columns(3)
    s1.metric("Total Videos", f"{total_v:,}")
    s2.metric("Above Median Velocity", f"{hot_count:,}")
    s3.metric("Most Common Tier", top_tier)
