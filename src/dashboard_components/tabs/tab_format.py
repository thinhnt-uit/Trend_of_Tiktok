"""
Tab 4: Format & Duration Sweet Spot.
"""

import pandas as pd
import plotly.express as px
import streamlit as st


def render_tab_format(
    df_latest: pd.DataFrame,
    category_colors: dict,
    layout_config: dict,
):
    """Render Format & Duration Sweet Spot tab."""
    st.markdown(
        "<div class='section-header'>Optimal Video Duration Analysis</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>Format analysis:</span> 
        Are short videos (&lt;15s) still dominant, or is TikTok shifting toward longer content? 
        Use the charts below to identify the <strong>optimal duration range</strong> for maximum views and engagement in your category.
    </div>
    """,
        unsafe_allow_html=True,
    )

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
                color_discrete_map=category_colors,
                hover_name="author_nickname",
                hover_data=["engagement_rate", "like_count"],
                title="Duration Sweet Spot Matrix (Duration vs. Views)",
                labels={
                    "video_duration": "Video Duration (seconds)",
                    "play_count": "Views",
                },
            )
            fig_scat.update_layout(**layout_config)
            st.plotly_chart(fig_scat, use_container_width=True)

        with col_f2:
            def bin_duration(d):
                if d <= 15:
                    return "Short (<15s)"
                elif d <= 30:
                    return "Medium (15s–30s)"
                elif d <= 60:
                    return "Long (30s–60s)"
                else:
                    return "Very Long (>60s)"

            df_duration["duration_bin"] = df_duration["video_duration"].apply(bin_duration)
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
                title="Avg Views & Engagement by Duration Group",
                labels={"duration_bin": "Duration Group", "avg_views": "Average Views"},
                text="video_count",
            )
            fig_bin.update_layout(**layout_config)
            fig_bin.update_traces(texttemplate="Videos: %{text}", textposition="outside")
            st.plotly_chart(fig_bin, use_container_width=True)

        # Resolution distribution (Vertical vs Landscape)
        st.markdown(
            "<div class='section-header'>Aspect Ratio Distribution</div>",
            unsafe_allow_html=True,
        )

        def calculate_aspect_ratio(row):
            w, h = row["video_width"], row["video_height"]
            if pd.isna(w) or pd.isna(h) or w == 0 or h == 0:
                return "Unknown"
            ratio = h / w
            if ratio > 1.2:
                return "Vertical (9:16)"
            elif ratio < 0.8:
                return "Landscape"
            else:
                return "Square (1:1)"

        df_fmt = df_latest.copy()
        df_fmt["orientation"] = df_fmt.apply(calculate_aspect_ratio, axis=1)
        df_orient = (
            df_fmt.groupby("orientation")
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
                title="Aspect Ratio Distribution (Explore Page)",
                color="orientation",
                color_discrete_map={
                    "Vertical (9:16)": "#FE2C55",
                    "Landscape": "#1E90FF",
                    "Square (1:1)": "#FFD93D",
                    "Unknown": "#636e72",
                },
                hole=0.4,
            )
            fig_orient_pie.update_layout(**layout_config)
            st.plotly_chart(fig_orient_pie, use_container_width=True)

        with col_res2:
            fig_orient_bar = px.bar(
                df_orient,
                x="orientation",
                y="avg_views",
                color="avg_eng",
                color_continuous_scale="Magenta",
                title="Average Views by Aspect Ratio",
                labels={"orientation": "Aspect Ratio", "avg_views": "Average Views"},
            )
            fig_orient_bar.update_layout(**layout_config)
            st.plotly_chart(fig_orient_bar, use_container_width=True)

        # Interactive list by aspect ratio
        st.markdown(
            "<div class='section-header'>📋 Video List by Aspect Ratio</div>",
            unsafe_allow_html=True,
        )

        orientation_options = sorted(df_fmt["orientation"].dropna().unique().tolist())
        if orientation_options:
            orient_labels = {
                o: f"{o}  ({len(df_fmt[df_fmt['orientation'] == o])} videos)"
                for o in orientation_options
            }
            selected_orient_label = st.selectbox(
                "Select aspect ratio to view video list:",
                options=list(orient_labels.values()),
                index=0,
                key="orient_select",
            )
            selected_orient = [k for k, v in orient_labels.items() if v == selected_orient_label][0]

            df_orient_vids = (
                df_fmt[df_fmt["orientation"] == selected_orient]
                .copy()
                .sort_values("play_count", ascending=False)
            )

            if not df_orient_vids.empty:
                st.markdown(f"**Found {len(df_orient_vids)} videos** with aspect ratio **{selected_orient}**")
                orient_display_cols = {
                    "video_cover_url": "Cover",
                    "category_name": "Category",
                    "video_desc": "Description",
                    "author_nickname": "Creator",
                    "author_followers": "Followers",
                    "play_count": "Views",
                    "like_count": "Likes",
                    "engagement_rate": "Engagement %",
                    "video_duration": "Duration (s)",
                    "video_play_url": "Watch",
                }
                df_orient_disp = df_orient_vids[list(orient_display_cols.keys())].rename(columns=orient_display_cols)

                st.dataframe(
                    df_orient_disp,
                    column_config={
                        "Cover": st.column_config.ImageColumn("Cover", width="small"),
                        "Watch": st.column_config.LinkColumn("Watch", display_text="▶ Play"),
                        "Followers": st.column_config.NumberColumn(format="%d 👥"),
                        "Views": st.column_config.NumberColumn(format="%d 👀"),
                        "Likes": st.column_config.NumberColumn(format="%d ❤️"),
                        "Engagement %": st.column_config.NumberColumn(format="%.2f%% 🔥"),
                    },
                    use_container_width=True,
                    hide_index=True,
                    height=450,
                )
    else:
        st.info("No video duration data found for the selected time range.")
