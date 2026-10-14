"""
Tab components for TikTok Explore Trend Dashboard.
7-tab redesigned architecture:
  1. Overview & Pulse     — Signal Matrix, KPIs, AI Summary
  2. Viral Leaderboard    — Sortable enhanced table
  3. Category Intelligence— Category deep-dive + growth
  4. Content DNA          — Format + Audio + Hashtags unified
  5. Creator Intelligence — Tier analysis + leaderboard
  6. Trend Predictor      — ML predictions
  7. System & Data Health — Technical info
"""

from .tab_overview import render_tab_overview
from .tab_leaderboard import render_tab_leaderboard
from .tab_category import render_tab_category
from .tab_content_dna import render_tab_content_dna
from .tab_creator import render_tab_creator
from .tab_player import render_tab_player
from .tab_ml import render_tab_ml
from .tab_system import render_tab_system

__all__ = [
    "render_tab_overview",
    "render_tab_leaderboard",
    "render_tab_category",
    "render_tab_content_dna",
    "render_tab_creator",
    "render_tab_player",
    "render_tab_ml",
    "render_tab_system",
]
