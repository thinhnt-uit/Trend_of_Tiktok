"""
Tab 0: System Overview (Crawl statistics and volume per day).
"""

import pandas as pd
import plotly.express as px
import streamlit as st


def render_tab_system(df_raw: pd.DataFrame, layout_config: dict):
    """Render System Overview tab."""
    st.markdown(
        "<div class='section-header'>📊 System Overview (Crawl Statistics)</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='insight-box'>
            <span class='insight-icon'>Data collection:</span> 
            Summary of crawl days and video volume distribution per day.
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_days = df_raw["crawled_date"].nunique()
    videos_per_day = df_raw.groupby("crawled_date")["video_id"].nunique().reset_index()
    videos_per_day.columns = ["Crawl Date", "Video Count"]

    col_sys1, col_sys2 = st.columns([1, 2])
    with col_sys1:
        st.markdown(
            f"""
            <div class='metric-card' style='margin-bottom: 1rem;'>
                <div class='metric-label'>Total Crawl Days</div>
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
                x="Crawl Date",
                y="Video Count",
                text="Video Count",
                title="Videos Collected per Crawl Day",
                color_discrete_sequence=["#25F4EE"],
            )
            fig_sys.update_layout(**layout_config)
            st.plotly_chart(fig_sys, use_container_width=True)
        else:
            st.info("No crawl data available yet.")
