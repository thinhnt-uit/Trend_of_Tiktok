"""
Tab 4 - Content DNA.
Consolidated tab: Format & Duration + Audio Trends + Hashtag Intelligence.
"""

import re
import json
import pandas as pd
import plotly.express as px
import ast
import streamlit as st


def _parse_hashtag_count(x, desc: str = "") -> int:
    if isinstance(x, list):
        return len(x)
    if isinstance(x, str) and x.strip():
        s = x.strip()
        try:
            p = json.loads(s)
            if isinstance(p, list):
                return len(p)
        except Exception:
            pass
        try:
            p = ast.literal_eval(s)
            if isinstance(p, (list, tuple, set)):
                return len(p)
        except Exception:
            pass
    if isinstance(desc, str) and "#" in desc:
        return len(re.findall(r"#([a-zA-Z0-9_\u00C0-\u024F\u1E00-\u1EFF]+)", desc))
    return 0


def _section(title: str):
    st.markdown(f"<div class='section-header'>{title}</div>", unsafe_allow_html=True)


def _render_format(df: pd.DataFrame, category_colors: dict, layout_config: dict):
    _section("A — Format & Duration Sweet Spot")
    st.markdown(
        """<div class='insight-box'><span class='insight-icon'>Duration strategy:</span>
        Are short videos still dominant, or is TikTok shifting toward longer content?
        Use the scatter chart to identify the <strong>optimal duration range</strong> for your category.</div>""",
        unsafe_allow_html=True,
    )

    df_dur = df[df["video_duration"] > 0].copy()
    if df_dur.empty:
        st.info("No duration data found.")
        return

    def _bin(d):
        if d <= 15: return "Short (<15s)"
        elif d <= 30: return "Medium (15-30s)"
        elif d <= 60: return "Long (30-60s)"
        return "Very Long (>60s)"

    df_dur["duration_bin"] = df_dur["video_duration"].apply(_bin)

    col1, col2 = st.columns([3, 2])
    with col1:
        fig_scat = px.scatter(
            df_dur, x="video_duration", y="play_count",
            size="engagement_rate", color="category_name",
            color_discrete_map=category_colors,
            hover_name="author_nickname",
            hover_data=["engagement_rate", "like_count"],
            title="Duration vs Views (bubble = Engagement Rate)",
            labels={"video_duration": "Duration (s)", "play_count": "Views"},
        )
        fig_scat.update_layout(**layout_config)
        st.plotly_chart(fig_scat, use_container_width=True)

    with col2:
        bin_order = ["Short (<15s)", "Medium (15-30s)", "Long (30-60s)", "Very Long (>60s)"]
        df_bin_agg = (
            df_dur.groupby("duration_bin")
            .agg(avg_views=("play_count", "mean"), avg_eng=("engagement_rate", "mean"), cnt=("video_id", "count"))
            .reindex(bin_order).dropna(how="all").reset_index()
        )
        fig_bin = px.bar(
            df_bin_agg, x="duration_bin", y="avg_views",
            color="avg_eng", color_continuous_scale="Viridis",
            title="Avg Views & Engagement by Duration Group",
            labels={"duration_bin": "Duration Group", "avg_views": "Average Views"},
            text="cnt",
        )
        fig_bin.update_layout(**layout_config, coloraxis_showscale=False)
        fig_bin.update_traces(texttemplate="%{text} videos", textposition="outside")
        st.plotly_chart(fig_bin, use_container_width=True)

    # Aspect ratio
    def _aspect(row):
        w, h = row.get("video_width", 0), row.get("video_height", 0)
        if not w or not h: return "Unknown"
        ratio = h / w
        if ratio > 1.2: return "Vertical (9:16)"
        if ratio < 0.8: return "Landscape"
        return "Square (1:1)"

    if "video_width" in df_dur.columns and "video_height" in df_dur.columns:
        df_dur["orientation"] = df_dur.apply(_aspect, axis=1)
        df_or = (
            df_dur.groupby("orientation")
            .agg(count=("video_id", "count"), avg_eng=("engagement_rate", "mean"))
            .reset_index()
        )
        oc1, oc2 = st.columns(2)
        with oc1:
            fig_pie = px.pie(
                df_or, names="orientation", values="count",
                title="Aspect Ratio Distribution",
                color="orientation",
                color_discrete_map={"Vertical (9:16)": "#FE2C55", "Landscape": "#1E90FF", "Square (1:1)": "#FFD93D", "Unknown": "#636e72"},
                hole=0.4,
            )
            fig_pie.update_layout(**layout_config)
            st.plotly_chart(fig_pie, use_container_width=True)
        with oc2:
            fig_or_bar = px.bar(
                df_or, x="orientation", y="avg_eng",
                color="orientation",
                color_discrete_map={"Vertical (9:16)": "#FE2C55", "Landscape": "#1E90FF", "Square (1:1)": "#FFD93D", "Unknown": "#636e72"},
                title="Avg Engagement by Aspect Ratio",
                labels={"orientation": "Aspect Ratio", "avg_eng": "Avg Engagement %"},
            )
            fig_or_bar.update_layout(**layout_config, showlegend=False)
            st.plotly_chart(fig_or_bar, use_container_width=True)


def _render_audio(df: pd.DataFrame, layout_config: dict):
    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin:1.5rem 0'>", unsafe_allow_html=True)
    _section("B — Audio & Soundtrack Fingerprint")
    st.markdown(
        """<div class='insight-box'><span class='insight-icon'>Audio strategy:</span>
        Using the right trending sound can significantly boost discoverability on FYP.
        Preview tracks below and identify which sounds are driving the most engagement.</div>""",
        unsafe_allow_html=True,
    )

    df_aud = df[df["music_title"].notna() & (df["music_title"] != "")].copy()
    if df_aud.empty:
        st.info("No audio metadata found.")
        return

    df_aud_agg = (
        df_aud.groupby(["music_title", "music_author", "music_play_url"])
        .agg(videos=("video_id", "count"), total_views=("play_count", "sum"),
             avg_eng=("engagement_rate", "mean"))
        .reset_index()
        .sort_values("total_views", ascending=False)
    )

    song_options = df_aud_agg["music_title"].head(15).tolist()
    if song_options:
        selected_song = st.selectbox("Preview a trending track:", options=song_options, key="dna_audio_select")
        song_row = df_aud_agg[df_aud_agg["music_title"] == selected_song].iloc[0]
        st.caption(f"Artist: {song_row['music_author']} | Explore Views: {int(song_row['total_views']):,}")
        url = str(song_row.get("music_play_url", ""))
        if url.startswith("http"):
            st.audio(url)
        else:
            st.warning("Preview link unavailable (TikTok audio URLs expire after 24h).")

    a1, a2 = st.columns([1, 1])
    with a1:
        fig_aud = px.bar(
            df_aud_agg.head(10),
            x="total_views", y="music_title", orientation="h",
            color="videos", color_continuous_scale="Tealgrn",
            title="Top 10 Sounds by Total Views",
            labels={"total_views": "Total Views", "music_title": "Track", "videos": "# Videos"},
        )
        fig_aud.update_layout(**layout_config, coloraxis_showscale=False)
        st.plotly_chart(fig_aud, use_container_width=True)
    with a2:
        st.markdown("**Hot Sounds Leaderboard**")
        st.dataframe(
            df_aud_agg.head(20)[["music_title", "music_author", "videos", "total_views", "avg_eng"]].rename(
                columns={"music_title": "Track", "music_author": "Artist", "videos": "# Videos",
                         "total_views": "Total Views", "avg_eng": "Avg Eng %"}
            ),
            column_config={
                "Total Views": st.column_config.NumberColumn(format="%d"),
                "Avg Eng %":   st.column_config.NumberColumn(format="%.2f%%"),
            },
            use_container_width=True, hide_index=True,
        )


def _render_hashtags(df: pd.DataFrame, layout_config: dict):
    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin:1.5rem 0'>", unsafe_allow_html=True)
    _section("C — Hashtag Intelligence")
    st.markdown(
        """<div class='insight-box'><span class='insight-icon'>Hashtag strategy:</span>
        The charts below show view volume and average engagement rate for each hashtag on the Explore page.
        High-engagement hashtags with fewer videos signal <strong>emerging, low-competition niches</strong>.</div>""",
        unsafe_allow_html=True,
    )

    hashtags_list = []
    for _, row in df.iterrows():
        desc = row.get("video_desc", "") or ""
        plays = row.get("play_count", 0) or 0
        likes = row.get("like_count", 0) or 0
        eng   = row.get("engagement_rate", 0.0) or 0.0
        found = re.findall(r"#([a-zA-Z0-9_\u00C0-\u024F\u1E00-\u1EFF]+)", desc)
        for h in found:
            hashtags_list.append({"hashtag": f"#{h.lower()}", "views": plays, "likes": likes, "engagement": eng})
        ht = row.get("hashtag_list")
        if isinstance(ht, str) and ht.strip():
            try:
                ht = json.loads(ht)
            except Exception:
                try:
                    ht = ast.literal_eval(ht)
                except Exception:
                    pass
        if isinstance(ht, list):
            for h in ht:
                if isinstance(h, str) and h.strip():
                    hashtags_list.append({"hashtag": f"#{h.lower()}", "views": plays, "likes": likes, "engagement": eng})

    if not hashtags_list:
        st.info("No hashtags found in the selected video descriptions.")
        return

    df_hash = pd.DataFrame(hashtags_list).drop_duplicates()
    df_hash_agg = (
        df_hash.groupby("hashtag")
        .agg(total_views=("views", "sum"), total_likes=("likes", "sum"),
             avg_engagement=("engagement", "mean"), appearances=("hashtag", "count"))
        .reset_index()
    )

    h1, h2 = st.columns(2)
    with h1:
        top_v = df_hash_agg.sort_values("total_views", ascending=True).tail(15)
        fig_hv = px.bar(
            top_v, y="hashtag", x="total_views", orientation="h",
            title="Top 15 Hashtags by Total Views",
            color="avg_engagement", color_continuous_scale="Viridis",
            labels={"total_views": "Total Views", "hashtag": "Hashtag"},
        )
        fig_hv.update_layout(**layout_config, coloraxis_showscale=False)
        st.plotly_chart(fig_hv, use_container_width=True)
    with h2:
        top_e = df_hash_agg.sort_values("avg_engagement", ascending=True).tail(15)
        fig_he = px.bar(
            top_e, y="hashtag", x="avg_engagement", orientation="h",
            title="Top 15 Hashtags by Avg Engagement %",
            color="appearances", color_continuous_scale="Sunsetdark",
            labels={"avg_engagement": "Avg Engagement %", "hashtag": "Hashtag"},
        )
        fig_he.update_layout(**layout_config, coloraxis_showscale=False)
        st.plotly_chart(fig_he, use_container_width=True)

    st.markdown("**Full Hashtag Table**")
    st.dataframe(
        df_hash_agg.sort_values("total_views", ascending=False).rename(
            columns={"hashtag": "Hashtag", "total_views": "Total Views",
                     "total_likes": "Total Likes", "avg_engagement": "Avg Eng %",
                     "appearances": "Explore Appearances"}
        ),
        column_config={
            "Total Views":  st.column_config.NumberColumn(format="%d"),
            "Total Likes":  st.column_config.NumberColumn(format="%d"),
            "Avg Eng %":    st.column_config.NumberColumn(format="%.2f%%"),
        },
        use_container_width=True, hide_index=True,
    )


def render_tab_content_dna(
    df_latest: pd.DataFrame,
    category_colors: dict,
    layout_config: dict,
):
    """Render Tab 4: Content DNA - Format, Audio, and Hashtag in one unified view."""
    st.markdown(
        """<div class='insight-box'>
            <span class='insight-icon'>Content DNA:</span>
            Three pillars of viral content strategy in one place.
            <strong>A - Format</strong>: optimal duration and aspect ratio.
            <strong>B - Audio</strong>: which sounds are driving views.
            <strong>C - Hashtags</strong>: which tags have the best reach vs. engagement balance.
        </div>""",
        unsafe_allow_html=True,
    )
    _render_format(df_latest, category_colors, layout_config)
    _render_audio(df_latest, layout_config)
    _render_hashtags(df_latest, layout_config)
