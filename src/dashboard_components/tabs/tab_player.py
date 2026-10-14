"""
Tab 7: Video Auditing Tool and Category Benchmarking.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_tab_player(
    df_latest: pd.DataFrame,
    df_raw: pd.DataFrame,
    layout_config: dict,
):
    """Render Video Auditing Tool tab."""
    st.markdown(
        "<div class='section-header'>Video Auditing Tool & Category Benchmarking</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>How to use:</span>
        Select a video from the list below to view detailed performance metrics and compare it against the 
        <strong>category average benchmark</strong>. 
        The system will automatically calculate whether that video is <strong>outperforming or underperforming</strong> 
        relative to others in the same content group.
    </div>
    """,
        unsafe_allow_html=True,
    )

    if not df_latest.empty:
        df_player = df_latest.copy()
        df_player["select_label"] = (
            df_player["category_name"].fillna("N/A")
            + " — @"
            + df_player["author_username"].fillna("Unknown")
            + " — "
            + df_player["video_desc"].str.slice(0, 50).fillna("")
            + " ("
            + df_player["video_id"].astype(str)
            + ")"
        )

        selected = st.selectbox(
            "Select a video to audit:", options=df_player["select_label"].tolist()
        )
        row = df_player[df_player["select_label"] == selected].iloc[0]

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
                    "Direct video link has expired (TikTok URLs are valid for 24 hours only). Showing cover image instead:"
                )
                cover = row.get("video_cover_url")
                if isinstance(cover, str) and cover.strip().startswith("http"):
                    st.image(cover, caption="Video Cover")

        with col_d:
            st.markdown(f"### {row.get('video_desc', 'N/A')}")
            st.markdown(
                f"**Creator:** @{row.get('author_username', 'N/A')} ({row.get('author_nickname', '')})"
            )

            verification_str = (
                "Verified Account ✓"
                if row["author_verified"]
                else "Unverified Account"
            )
            st.markdown(
                f"**Followers:** {row['author_followers']:,} | **Status:** {verification_str}"
            )

            st.markdown("#### Comparison vs. Category Average")

            if view_perf_ratio >= 1.0:
                st.success(
                    f"Views: **{view_perf_ratio:.2f}x** ABOVE the `{cat_name}` category average."
                )
            else:
                st.warning(
                    f"Views: **{view_perf_ratio:.2f}x** BELOW the `{cat_name}` category average."
                )

            if eng_perf_ratio >= 1.0:
                st.success(
                    f"Engagement Rate: **{eng_perf_ratio:.2f}x** ABOVE the `{cat_name}` category average."
                )
            else:
                st.warning(
                    f"Engagement Rate: **{eng_perf_ratio:.2f}x** BELOW the `{cat_name}` category average."
                )

            st.markdown("---")
            md_c1, md_c2 = st.columns(2)
            with md_c1:
                st.markdown(f"**Category:** {row.get('category_name', 'N/A')}")
                st.markdown(f"**Duration:** {row.get('video_duration', 'N/A')} seconds")
                w, h = row.get("video_width"), row.get("video_height")
                res = f"{int(w)}×{int(h)}" if pd.notna(w) and pd.notna(h) else "N/A"
                st.markdown(f"**Resolution:** {res}")
            with md_c2:
                st.markdown(f"**Engagement Rate:** `{row['engagement_rate']:.2f}%`")
                st.markdown(f"**Background Music:** {row.get('music_title', 'N/A')}")
                st.markdown(f"**Artist:** {row.get('music_author', '')}")

            st.markdown("---")
            st.markdown("**Audience Engagement Metrics**")
            st.markdown(
                f"**Views:** {int(row['play_count']):,}"
                if pd.notna(row["play_count"])
                else "Views: N/A"
            )
            st.markdown(
                f"**Likes:** {int(row['like_count']):,}"
                if pd.notna(row["like_count"])
                else "Likes: N/A"
            )
            st.markdown(
                f"**Comments:** {int(row['comment_count']):,}"
                if pd.notna(row["comment_count"])
                else "Comments: N/A"
            )
            st.markdown(
                f"**Shares:** {int(row['share_count']):,}"
                if pd.notna(row["share_count"])
                else "Shares: N/A"
            )
            st.markdown(
                f"**Saves:** {int(row['collect_count']):,}"
                if pd.notna(row["collect_count"])
                else "Saves: N/A"
            )

            # Historical trend chart
            vid = row["video_id"]
            df_hist = df_raw[df_raw["video_id"] == vid].sort_values("crawled_date")
            if len(df_hist) > 1:
                st.markdown("---")
                st.markdown("**Historical Growth Chart:**")
                fig_h = go.Figure()
                fig_h.add_trace(
                    go.Scatter(
                        x=df_hist["crawled_date"],
                        y=df_hist["play_count"],
                        mode="lines+markers",
                        name="Views",
                        line=dict(color="#25F4EE", width=2),
                    )
                )
                fig_h.add_trace(
                    go.Scatter(
                        x=df_hist["crawled_date"],
                        y=df_hist["like_count"],
                        mode="lines+markers",
                        name="Likes",
                        line=dict(color="#FE2C55", width=2),
                    )
                )
                fig_h.update_layout(height=200, margin=dict(l=0, r=0, t=10, b=0), **layout_config)
                st.plotly_chart(fig_h, use_container_width=True)
            else:
                st.info("This video was only crawled once. No historical data available yet.")
    else:
        st.info("No videos found.")
