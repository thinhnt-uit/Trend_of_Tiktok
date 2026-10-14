"""
Tab 2: Historical Growth Trends.
"""

import pandas as pd
import plotly.express as px
import streamlit as st


def render_tab_growth(
    df_raw: pd.DataFrame,
    df_latest: pd.DataFrame,
    category_colors: dict,
    layout_config: dict,
):
    """Render Historical Growth Trends tab."""
    st.markdown(
        "<div class='section-header'>📈 Historical View Growth by Category</div>",
        unsafe_allow_html=True,
    )

    all_dates = sorted(df_raw["crawled_date"].unique())
    if len(all_dates) < 2:
        st.info(
            "💡 Only one day of data has been crawled so far. The historical growth chart will appear automatically once you run the crawler on subsequent days."
        )
        return

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>📊 Cumulative principle:</span> 
        TikTok view counts accumulate over time. The chart below shows the <strong>total cumulative views</strong> 
        for each category across crawl dates, helping identify which category is surging the fastest.
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
        title="Cumulative View Growth Trend by Category",
        labels={"crawled_date": "Crawl Date", "play_count": "Total Views"},
        markers=True,
        color_discrete_map=category_colors,
    )
    fig_line_growth.update_layout(**layout_config)
    st.plotly_chart(fig_line_growth, use_container_width=True)

    # Line chart: top videos view growth rate
    st.markdown(
        "<div class='section-header'>📈 View Growth Rate of Top Viral Videos</div>",
        unsafe_allow_html=True,
    )

    top_vids = (
        df_latest.sort_values(by="play_count", ascending=False)
        .head(5)["video_id"]
        .tolist()
    )
    df_top_hist = df_raw[df_raw["video_id"].isin(top_vids)].sort_values("crawled_date")

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
            title="View Growth Rate of Top 5 Hottest Videos",
            labels={
                "crawled_date": "Crawl Date",
                "play_count": "View Count",
            },
            markers=True,
        )
        fig_vid_growth.update_layout(**layout_config)
        st.plotly_chart(fig_vid_growth, use_container_width=True)
