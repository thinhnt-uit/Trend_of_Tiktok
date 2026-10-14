"""
TikTok Explore — Professional Creator Insights Dashboard
Entry point for the Streamlit web application.
Redesigned 7-tab architecture for optimal analyst workflow.
"""

import os
import sys
import importlib
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── Hot-reload all modules ──────────────────────────────────────────────────
import src.dashboard_components.styles   as _styles_mod
import src.dashboard_components.data     as _data_mod
import src.dashboard_components.sidebar  as _sidebar_mod
import src.dashboard_components.tabs     as _tabs_mod
import src.dashboard_components.tabs.tab_overview     as _t_ov
import src.dashboard_components.tabs.tab_leaderboard  as _t_lb
import src.dashboard_components.tabs.tab_category     as _t_cat
import src.dashboard_components.tabs.tab_content_dna  as _t_dna
import src.dashboard_components.tabs.tab_creator      as _t_cr
import src.dashboard_components.tabs.tab_player       as _t_pl
import src.dashboard_components.tabs.tab_ml           as _t_ml
import src.dashboard_components.tabs.tab_system       as _t_sys

for _m in [
    _styles_mod, _data_mod, _sidebar_mod,
    _t_ov, _t_lb, _t_cat, _t_dna, _t_cr, _t_pl, _t_ml, _t_sys,
    _tabs_mod,
]:
    importlib.reload(_m)

from src.dashboard_components.styles import (
    PLOTLY_LAYOUT,
    CATEGORY_COLORS,
    apply_custom_styles,
    render_header,
    render_kpis_and_summary,
)
from src.dashboard_components.data import fetch_data, deduplicate_latest
from src.dashboard_components.sidebar import render_sidebar
from src.dashboard_components.tabs import (
    render_tab_overview,
    render_tab_leaderboard,
    render_tab_category,
    render_tab_content_dna,
    render_tab_creator,
    render_tab_player,
    render_tab_ml,
    render_tab_system,
)

# ── 1. Page configuration ───────────────────────────────────────────────────
st.set_page_config(
    page_title="TikTok Explore — Professional Creator Insights",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 2. Inject CSS ───────────────────────────────────────────────────────────
apply_custom_styles()

# ── 3. Fetch data ───────────────────────────────────────────────────────────
try:
    df_raw = fetch_data()
except Exception as e:
    st.error(f"Connection to the data warehouse failed: {e}")
    st.stop()

# ── 4. Sidebar filters ──────────────────────────────────────────────────────
df_filtered = render_sidebar(df_raw)

# ── 5. Deduplicate for analysis tabs ────────────────────────────────────────
# df_latest keeps only the latest crawl snapshot per video_id so that
# analysis tabs (leaderboard, category, creator, etc.) don't inflate
# counts when a video trends across multiple crawl dates.
df_latest = deduplicate_latest(df_filtered)

# ── 6. Header ───────────────────────────────────────────────────────────────
render_header()

# ── 7. Stop-guard for empty data ────────────────────────────────────────────
render_kpis_and_summary(df_latest)   # now only shows stop-guard if empty

# ── 8. Seven tabs ───────────────────────────────────────────────────────────
(
    tab_overview,
    tab_leaderboard,
    tab_category,
    tab_dna,
    tab_creator,
    tab_player,
    tab_ml,
    tab_system,
) = st.tabs(
    [
        "🏠 Overview & Pulse",
        "🔥 Viral Leaderboard",
        "📊 Category Intelligence",
        "🎵 Content DNA",
        "👤 Creator Intelligence",
        "🎬 Video Auditing Tool",
        "🤖 Trend Predictor",
        "⚙️ System & Data Health",
    ]
)

# Analysis tabs receive df_latest (deduplicated per video_id).
# System/health tab receives df_raw (full history for diagnostics).

with tab_overview:
    render_tab_overview(df_latest, PLOTLY_LAYOUT)

with tab_leaderboard:
    render_tab_leaderboard(df_latest)

with tab_category:
    render_tab_category(df_latest, df_filtered, CATEGORY_COLORS, PLOTLY_LAYOUT)

with tab_dna:
    render_tab_content_dna(df_latest, CATEGORY_COLORS, PLOTLY_LAYOUT)

with tab_creator:
    render_tab_creator(df_latest, CATEGORY_COLORS, PLOTLY_LAYOUT)

with tab_player:
    render_tab_player(df_latest, df_filtered, PLOTLY_LAYOUT)

with tab_ml:
    render_tab_ml(df_latest, PLOTLY_LAYOUT)

with tab_system:
    render_tab_system(df_raw, PLOTLY_LAYOUT)
