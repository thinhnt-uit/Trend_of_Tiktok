"""
Tab 5: Audio & Soundtrack Trends (including audio player).
"""

import pandas as pd
import plotly.express as px
import streamlit as st


def render_tab_audio(df_latest: pd.DataFrame, layout_config: dict):
    """Render Audio & Soundtrack Trends tab."""
    st.markdown(
        "<div class='section-header'>Audio & Soundtrack Performance Analysis</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>Integrated audio player:</span> 
        Use the list below to <strong>preview trending tracks</strong> crawled in real-time from the TikTok API. 
        Using these hot sounds will help your video reach the search algorithm and the FYP (For You Page) more easily.
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

        st.markdown("### Trending Sound Preview Player")
        song_options = df_audio_agg["music_title"].head(15).tolist()
        if song_options:
            selected_song = st.selectbox("Select a track to preview:", options=song_options)
            song_row = df_audio_agg[df_audio_agg["music_title"] == selected_song].iloc[0]
            st.markdown(
                f"**Artist:** {song_row['music_author']} | **Explore Views:** {int(song_row['total_views']):,} views"
            )
            if song_row["music_play_url"] and str(song_row["music_play_url"]).startswith("http"):
                st.audio(song_row["music_play_url"])
            else:
                st.warning("Preview link unavailable or expired (TikTok URLs expire after 24 hours).")

        st.markdown("---")
        df_audio_disp = df_audio_agg.head(20).copy().rename(
            columns={
                "music_title": "Track Title",
                "music_author": "Artist",
                "videos_using_sound": "Videos Using Sound",
                "total_views": "Total Views",
                "total_likes": "Total Likes",
                "avg_engagement_rate": "Avg Engagement %",
            }
        )

        col_aud1, col_aud2 = st.columns([1, 1])

        with col_aud1:
            fig_audio = px.bar(
                df_audio_agg.head(10),
                x="total_views",
                y="music_title",
                orientation="h",
                color="videos_using_sound",
                color_continuous_scale="Tealgrn",
                title="Top 10 Sounds by Total Views",
                labels={"total_views": "Total Views", "music_title": "Track Title"},
                hover_data=["music_author", "avg_engagement_rate"],
            )
            fig_audio.update_layout(**layout_config)
            st.plotly_chart(fig_audio, use_container_width=True)

        with col_aud2:
            st.markdown("**Hot Sounds Leaderboard**")
            st.dataframe(
                df_audio_disp[
                    [
                        "Track Title",
                        "Artist",
                        "Videos Using Sound",
                        "Total Views",
                        "Avg Engagement %",
                    ]
                ],
                column_config={
                    "Total Views": st.column_config.NumberColumn(format="%d views"),
                    "Avg Engagement %": st.column_config.NumberColumn(format="%.2f%%"),
                },
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("No audio metadata found in the database.")
