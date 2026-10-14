"""
Tab 6: Hashtags & Content Themes.
"""

import re
import json
import pandas as pd
import plotly.express as px
import streamlit as st


def render_tab_hashtag(df_latest: pd.DataFrame, layout_config: dict):
    """Render Hashtags & Content Themes tab."""
    st.markdown(
        "<div class='section-header'>Hashtag & Content Theme Analysis</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>Theme analysis:</span> 
        Hashtags are keyword classifiers that TikTok's algorithm uses to distribute videos to the right audience. 
        The charts below show the <strong>view volume and average engagement rate</strong> for each hashtag currently appearing on the Explore page.
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
        if isinstance(ht_list, str):
            try:
                parsed = json.loads(ht_list)
                if isinstance(parsed, list):
                    ht_list = parsed
            except Exception:
                pass

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
        df_hash = pd.DataFrame(hashtags_list).drop_duplicates()
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
            top_by_views = df_hash_agg.sort_values("total_views", ascending=True).tail(15)
            fig_hv = px.bar(
                top_by_views,
                y="hashtag",
                x="total_views",
                orientation="h",
                title="Top 15 Hashtags by Total Views",
                labels={"total_views": "Total Views", "hashtag": "Hashtag"},
                color="avg_engagement",
                color_continuous_scale="Viridis",
            )
            fig_hv.update_layout(**layout_config)
            st.plotly_chart(fig_hv, use_container_width=True)

        with col_h2:
            top_by_likes = df_hash_agg.sort_values("total_likes", ascending=True).tail(15)
            fig_hl = px.bar(
                top_by_likes,
                y="hashtag",
                x="total_likes",
                orientation="h",
                title="Top 15 Hashtags by Total Likes",
                labels={"total_likes": "Total Likes", "hashtag": "Hashtag"},
                color="hashtag_count",
                color_continuous_scale="Sunsetdark",
            )
            fig_hl.update_layout(**layout_config)
            st.plotly_chart(fig_hl, use_container_width=True)

        st.markdown(
            "<div class='section-header'>Full Hashtag Analysis Table</div>",
            unsafe_allow_html=True,
        )
        st.dataframe(
            df_hash_agg.sort_values(by="total_views", ascending=False).rename(
                columns={
                    "hashtag": "Hashtag",
                    "total_views": "Total Views",
                    "total_likes": "Total Likes",
                    "avg_engagement": "Avg Engagement %",
                    "hashtag_count": "Explore Appearances",
                }
            ),
            column_config={
                "Total Views": st.column_config.NumberColumn(format="%d views"),
                "Total Likes": st.column_config.NumberColumn(format="%d likes"),
                "Avg Engagement %": st.column_config.NumberColumn(format="%.2f%%"),
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No hashtags found in the descriptions of the selected videos.")
