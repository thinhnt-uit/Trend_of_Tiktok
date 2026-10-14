"""
Tab 1 — Overview & Pulse.
Entry-point tab: 5 KPI hero cards, Signal Matrix quadrant, AI executive summary.
"""

import pandas as pd
import plotly.express as px
import streamlit as st


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _fmt_large(n: float) -> str:
    """Format large numbers: 1.2M / 450K."""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return f"{n:.0f}"


def _engagement_badge(val: float) -> str:
    if val >= 10:
        return "🟢 Exceptional"
    if val >= 6:
        return "🟡 Strong"
    if val >= 3:
        return "🔵 Average"
    return "🔴 Low"


# ─────────────────────────────────────────────────────────────
# KPI Row (5 cards)
# ─────────────────────────────────────────────────────────────

def _render_kpi_row(df: pd.DataFrame):
    total_videos = df["video_id"].nunique()
    total_views  = df["play_count"].sum()
    avg_eng      = df["engagement_rate"].mean() if not df.empty else 0.0

    top_cat_series = (
        df.groupby("category_name")["play_count"].sum().sort_values(ascending=False)
    )
    top_category = top_cat_series.index[0] if not top_cat_series.empty else "N/A"
    top_cat_pct  = (top_cat_series.iloc[0] / total_views * 100) if total_views > 0 else 0

    avg_velocity = 0.0
    if "virality_velocity" in df.columns:
        avg_velocity = df["virality_velocity"].replace(0, pd.NA).dropna().mean() or 0.0

    eng_badge = _engagement_badge(avg_eng)
    vel_label  = "🔥 Hot" if avg_velocity >= 10_000 else ("⚡ Active" if avg_velocity >= 2_000 else "📉 Slow")

    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, "metric-card",           "🎬 Trending Videos",   f"{total_videos:,}",              None),
        (c2, "metric-card views",     "👀 Total Views",        _fmt_large(total_views),          None),
        (c3, "metric-card engagement","🔥 Avg Engagement",     f"{avg_eng:.2f}%",                eng_badge),
        (c4, "metric-card creator",   "🏆 Hottest Category",   top_category,                    f"{top_cat_pct:.0f}% of views"),
        (c5, "metric-card velocity",  "⚡ Viral Velocity",      f"{_fmt_large(avg_velocity)}/hr", vel_label),
    ]
    for col, cls, label, value, sub in cards:
        sub_html = f"<div class='metric-sub'>{sub}</div>" if sub else ""
        with col:
            st.markdown(
                f"<div class='{cls}'><div class='metric-label'>{label}</div>"
                f"<div class='metric-value'>{value}</div>{sub_html}</div>",
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────────────────
# Signal Matrix
# ─────────────────────────────────────────────────────────────

def _render_signal_matrix(df: pd.DataFrame, layout_config: dict):
    st.markdown(
        "<div class='section-header'>⚡ Signal Matrix — Viral Velocity × Engagement Rate</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class='insight-box'>
            <span class='insight-icon'>How to read this chart:</span>
            Each bubble = 1 video. <strong>X-axis = Views/hour</strong> (how fast it spreads).
            <strong>Y-axis = Engagement %</strong> (how deeply it resonates). Bubble size = total views.<br>
            Focus on <strong style='color:#FE2C55'>🔥 Hot &amp; Sticky</strong> (top-right) — these videos spread fast AND have high engagement.
            <strong style='color:#25F4EE'>💎 Niche Gold</strong> (top-left) are high-quality underexposed videos worth referencing.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "virality_velocity" not in df.columns or "engagement_rate" not in df.columns:
        st.info("Signal Matrix requires `virality_velocity` column. Run `dbt run` then refresh.")
        return

    df_sig = df.copy()
    df_sig["virality_velocity"] = pd.to_numeric(df_sig["virality_velocity"], errors="coerce").fillna(0)
    df_sig = df_sig[df_sig["virality_velocity"] > 0].copy()
    if df_sig.empty:
        st.info("No videos with velocity data yet. Data may need more than one crawl date.")
        return

    med_vel = df_sig["virality_velocity"].median()
    med_eng = df_sig["engagement_rate"].median()

    def _quadrant(row):
        v, e = row["virality_velocity"], row["engagement_rate"]
        if v >= med_vel and e >= med_eng:
            return "🔥 Hot & Sticky"
        if v >= med_vel and e < med_eng:
            return "⚡ Fast Burn"
        if v < med_vel and e >= med_eng:
            return "💎 Niche Gold"
        return "📉 Fading"

    df_sig["signal"] = df_sig.apply(_quadrant, axis=1)
    df_sig["label"]  = (
        "@" + df_sig["author_username"].fillna("?")
        + " | " + df_sig["video_desc"].str.slice(0, 45).fillna("")
    )

    color_map = {
        "🔥 Hot & Sticky": "#FE2C55",
        "⚡ Fast Burn":    "#FFD93D",
        "💎 Niche Gold":   "#25F4EE",
        "📉 Fading":       "#555a63",
    }

    hover_extra = {}
    if "creator_tier" in df_sig.columns:
        hover_extra["creator_tier"] = True

    fig = px.scatter(
        df_sig,
        x="virality_velocity",
        y="engagement_rate",
        color="signal",
        size="play_count",
        size_max=45,
        color_discrete_map=color_map,
        hover_name="label",
        hover_data={
            "virality_velocity": ":.0f",
            "engagement_rate":   ":.2f",
            "play_count":        ":,",
            "category_name":     True,
            "signal":            False,
            "label":             False,
            **hover_extra,
        },
        labels={
            "virality_velocity": "⚡ Views / Hour",
            "engagement_rate":   "🔥 Engagement Rate (%)",
        },
        title="Signal Matrix — Trend Lifecycle Position of Every Video",
    )
    fig.add_hline(
        y=med_eng, line_dash="dot", line_color="rgba(255,255,255,0.12)",
        annotation_text=f"Median Eng: {med_eng:.1f}%", annotation_position="top right",
        annotation_font_color="rgba(255,255,255,0.4)",
    )
    fig.add_vline(
        x=med_vel, line_dash="dot", line_color="rgba(255,255,255,0.12)",
        annotation_text=f"Median Vel: {_fmt_large(med_vel)}/hr", annotation_position="top right",
        annotation_font_color="rgba(255,255,255,0.4)",
    )
    fig.update_layout(**{**layout_config, "height": 500})
    st.plotly_chart(fig, use_container_width=True)

    # Quadrant summary pills
    q_counts = df_sig["signal"].value_counts()
    total_s  = len(df_sig)
    qc1, qc2, qc3, qc4 = st.columns(4)
    for col, key, bg in [
        (qc1, "🔥 Hot & Sticky", "#FE2C55"),
        (qc2, "⚡ Fast Burn",    "#FFD93D"),
        (qc3, "💎 Niche Gold",   "#25F4EE"),
        (qc4, "📉 Fading",       "#555a63"),
    ]:
        cnt = q_counts.get(key, 0)
        pct = cnt / total_s * 100 if total_s else 0
        with col:
            st.markdown(
                f"""
                <div style='background:rgba(255,255,255,0.04);border:1px solid {bg}40;
                            border-left:4px solid {bg};border-radius:10px;
                            padding:0.8rem 1rem;margin-top:0.5rem;'>
                    <div style='font-size:0.8rem;font-weight:700;color:{bg};
                                text-transform:uppercase;letter-spacing:1px'>{key}</div>
                    <div style='font-size:1.4rem;font-weight:800;color:#fff;margin-top:4px'>
                        {cnt} <span style='font-size:0.85rem;color:#8E8E93'>({pct:.0f}%)</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────────────────
# AI Executive Summary
# ─────────────────────────────────────────────────────────────

def _render_ai_summary(df: pd.DataFrame):
    if df.empty:
        return

    st.markdown(
        "<div class='section-header'>🤖 AI Executive Summary & Actionable Takeaways</div>",
        unsafe_allow_html=True,
    )

    top_video = df.sort_values("engagement_rate", ascending=False).iloc[0]
    top_creator = (
        df.groupby(["author_username", "author_nickname"])
          .agg(avg_eng=("engagement_rate", "mean"), total_views=("play_count", "sum"))
          .reset_index()
          .sort_values(["avg_eng", "total_views"], ascending=False)
          .iloc[0]
    )
    top_cat = df.groupby("category_name")["play_count"].sum().idxmax()

    best_duration = "N/A"
    if "video_duration" in df.columns:
        def _bin(d):
            if d <= 15: return "< 15s"
            if d <= 30: return "15 – 30s"
            if d <= 60: return "30 – 60s"
            return "> 60s"
        df_d = df[df["video_duration"] > 0].copy()
        if not df_d.empty:
            df_d["_b"] = df_d["video_duration"].apply(_bin)
            br = (
                df_d.groupby("_b")
                    .agg(avg_eng=("engagement_rate", "mean"), avg_v=("play_count", "mean"))
                    .sort_values(["avg_eng", "avg_v"], ascending=False)
                    .iloc[0]
            )
            best_duration = f"{br.name} ({br['avg_eng']:.2f}% avg eng)"

    lines = [
        f"🏆 <strong>Dominant Category:</strong> <strong style='color:#FE2C55'>{top_cat}</strong> is generating the most views right now.",
        f"🔥 <strong>Most Engaging Video:</strong> <em style='color:#25F4EE'>'{top_video['video_desc'][:70]}…'</em> "
        f"by <strong>@{top_video['author_username']}</strong> — "
        f"<strong style='color:#FFD93D'>{top_video['engagement_rate']:.2f}%</strong> engagement, "
        f"<strong>{_fmt_large(top_video['play_count'])}</strong> views.",
        f"👑 <strong>Top Creator:</strong> <strong style='color:#9B59B6'>@{top_creator['author_username']}</strong> "
        f"averaging <strong style='color:#FFD93D'>{top_creator['avg_eng']:.2f}%</strong> engagement across all videos.",
        f"⏱️ <strong>Optimal Format:</strong> The <strong style='color:#00D2D3'>{best_duration}</strong> duration bucket shows the best results.",
    ]

    if "virality_velocity" in df.columns:
        vel_df = df[df["virality_velocity"] > 0]
        if not vel_df.empty:
            tv = vel_df.sort_values("virality_velocity", ascending=False).iloc[0]
            lines.append(
                f"⚡ <strong>Fastest Rising:</strong> <strong style='color:#FFD93D'>@{tv['author_username']}</strong>'s video is spreading at "
                f"<strong style='color:#FE2C55'>{_fmt_large(tv['virality_velocity'])}/hr</strong> — monitor this one closely."
            )

    bullets = "".join(f"<div style='margin-bottom:0.55rem'>{l}</div>" for l in lines)
    st.markdown(
        f"""
        <div class='insight-box' style='background:rgba(37,244,238,0.04);
             border:1px solid rgba(37,244,238,0.2);border-left:4px solid #FE2C55;'>
            <div style='display:flex;align-items:center;gap:8px;margin-bottom:0.8rem'>
                <span style='font-size:1rem'>🤖</span>
                <strong style='color:#25F4EE;text-transform:uppercase;
                               letter-spacing:1px;font-size:0.8rem'>
                    AI Executive Summary &amp; Actionable Takeaways
                </strong>
            </div>
            {bullets}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Main render function
# ─────────────────────────────────────────────────────────────

def render_tab_overview(df: pd.DataFrame, layout_config: dict):
    """Render Tab 1: Overview & Pulse — entry point for the dashboard."""
    _render_kpi_row(df)
    st.markdown(
        "<hr style='border:none;border-top:1px solid rgba(255,255,255,0.05);margin:1.8rem 0'>",
        unsafe_allow_html=True,
    )
    _render_signal_matrix(df, layout_config)
    st.markdown(
        "<hr style='border:none;border-top:1px solid rgba(255,255,255,0.05);margin:1.8rem 0'>",
        unsafe_allow_html=True,
    )
    _render_ai_summary(df)

