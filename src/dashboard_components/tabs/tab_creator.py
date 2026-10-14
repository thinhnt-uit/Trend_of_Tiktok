"""
Tab 3: Creator & Verified Analytics.
"""

import pandas as pd
import plotly.express as px
import streamlit as st


def render_tab_creator(
    df_latest: pd.DataFrame,
    category_colors: dict,
    layout_config: dict,
):
    """Render Creator & Verified Analytics tab with Tier segmentation and channel metrics."""
    st.markdown(
        "<div class='section-header'>Channel Size & Verification Status Analysis</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>Algorithm principle:</span> 
        Compare follower counts vs. view counts in the scatter chart below. If views are distributed randomly regardless of follower size, 
        it confirms that <strong>TikTok's algorithm distributes views based on video quality, not channel size</strong>. 
        Small channels still have an equal chance of trending alongside accounts with millions of followers.
    </div>
    """,
        unsafe_allow_html=True,
    )

    col_cr1, col_cr2 = st.columns([3, 2])

    with col_cr1:
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
            title="Views vs. Followers Correlation (Bubble size = Engagement Rate)",
            labels={
                "author_followers": "Creator Followers (Log Scale)",
                "play_count": "Views",
            },
            color_discrete_map=category_colors,
        )
        fig_fols.update_layout(**layout_config)
        st.plotly_chart(fig_fols, use_container_width=True)

    with col_cr2:
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
            {True: "Verified ✓", False: "Unverified"}
        )

        fig_ver = px.bar(
            df_ver,
            x="Verification",
            y="avg_views",
            color="avg_eng",
            color_continuous_scale="Bluered",
            title="Avg Views: Verified vs. Unverified Accounts",
            labels={"avg_views": "Average Views", "Verification": "Account Type"},
            text="count",
        )
        fig_ver.update_layout(**layout_config)
        fig_ver.update_traces(texttemplate="Videos: %{text}", textposition="outside")
        st.plotly_chart(fig_ver, use_container_width=True)

    # ──────────────────────────────────────────────────────────────
    # Creator Tier Segmentation Analysis
    # ──────────────────────────────────────────────────────────────
    if "creator_tier" in df_latest.columns:
        st.markdown(
            "<div class='section-header'>Creator Tier Distribution (Explore Penetration)</div>",
            unsafe_allow_html=True,
        )

        tier_order = ["Nano (<10k)", "Micro (10k-100k)", "Macro (100k-1M)", "Mega (1M+)"]
        df_tier = (
            df_latest.groupby("creator_tier")
            .agg(
                video_count=("video_id", "count"),
                avg_views=("play_count", "mean"),
                avg_engagement=("engagement_rate", "mean"),
            )
            .reindex(tier_order)
            .dropna(how="all")
            .reset_index()
        )

        tier_col1, tier_col2 = st.columns(2)
        with tier_col1:
            fig_tier_pie = px.pie(
                df_tier,
                names="creator_tier",
                values="video_count",
                title="Share of Trending Videos by Creator Tier",
                color="creator_tier",
                color_discrete_map={
                    "Nano (<10k)": "#25F4EE",
                    "Micro (10k-100k)": "#FFD93D",
                    "Macro (100k-1M)": "#FE2C55",
                    "Mega (1M+)": "#9B59B6",
                },
                hole=0.4,
            )
            fig_tier_pie.update_layout(**layout_config)
            st.plotly_chart(fig_tier_pie, use_container_width=True)

        with tier_col2:
            fig_tier_bar = px.bar(
                df_tier,
                x="creator_tier",
                y="avg_engagement",
                color="creator_tier",
                color_discrete_map={
                    "Nano (<10k)": "#25F4EE",
                    "Micro (10k-100k)": "#FFD93D",
                    "Macro (100k-1M)": "#FE2C55",
                    "Mega (1M+)": "#9B59B6",
                },
                title="Average Engagement Rate by Creator Tier",
                labels={"creator_tier": "Creator Tier", "avg_engagement": "Avg Engagement %"},
                text="avg_engagement",
            )
            fig_tier_bar.update_layout(**layout_config, showlegend=False)
            fig_tier_bar.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
            st.plotly_chart(fig_tier_bar, use_container_width=True)

    # ──────────────────────────────────────────────────────────────
    # Top Performing Creators Leaderboard
    # ──────────────────────────────────────────────────────────────
    st.markdown(
        "<div class='section-header'>Top Performing Creators & Channel Power</div>",
        unsafe_allow_html=True,
    )
    st.caption("Includes overall channel authority: Total Channel Hearts, Total Channel Videos, and Average Hearts per Video.")

    group_cols = [
        "author_username",
        "author_nickname",
        "author_verified",
    ]
    if "creator_tier" in df_latest.columns:
        group_cols.append("creator_tier")

    df_creators = (
        df_latest.groupby(group_cols)
        .agg(
            followers=("author_followers", "max"),
            total_hearts=("author_heart_count", "max"),
            channel_videos=("author_video_count", "max"),
            trending_videos=("video_id", "count"),
            total_views=("play_count", "sum"),
            avg_engagement=("engagement_rate", "mean"),
        )
        .reset_index()
    )

    df_creators["hearts_per_video"] = (
        df_creators["total_hearts"] / df_creators["channel_videos"].replace(0, 1)
    ).round(0).astype(int)

    df_creators = df_creators.sort_values(by="total_views", ascending=False).head(20)

    disp_rename = {
        "author_username": "Username",
        "author_nickname": "Nickname",
        "creator_tier": "Tier",
        "followers": "Followers",
        "total_hearts": "Total Channel Hearts",
        "channel_videos": "Total Videos",
        "hearts_per_video": "Avg Hearts/Video",
        "trending_videos": "Trending on Explore",
        "total_views": "Explore Views",
        "avg_engagement": "Avg Engagement %",
        "author_verified": "Verified",
    }

    st.dataframe(
        df_creators.rename(columns=disp_rename),
        column_config={
            "Followers": st.column_config.NumberColumn(format="%d 👥"),
            "Total Channel Hearts": st.column_config.NumberColumn(format="%d ❤️"),
            "Total Videos": st.column_config.NumberColumn(format="%d 🎬"),
            "Avg Hearts/Video": st.column_config.NumberColumn(format="%d 💖/🎬"),
            "Trending on Explore": st.column_config.NumberColumn(format="%d 🔥"),
            "Explore Views": st.column_config.NumberColumn(format="%d 👀"),
            "Avg Engagement %": st.column_config.NumberColumn(format="%.2f%%"),
            "Verified": st.column_config.CheckboxColumn("Verified ✓"),
        },
        use_container_width=True,
        hide_index=True,
    )
