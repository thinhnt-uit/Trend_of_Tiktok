"""
Styles, themes, constants and header components for the Streamlit dashboard.
"""

import streamlit as st
import pandas as pd

PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans", size=12),
)

CATEGORY_COLORS = {
    "All": "#E0E0E0",
    "Singing & Dancing": "#FF6B81",
    "Comedy": "#FFD93D",
    "Sports": "#6BCB77",
    "Anime & Comics": "#9B59B6",
    "Relationship": "#FF6348",
    "Shows": "#1E90FF",
    "Daily Life": "#00D2D3",
    "Unknown": "#636e72",
}


def apply_custom_styles():
    """Inject custom CSS for dark theme, typography, and card designs."""
    st.markdown(
        """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        
        /* Global Overrides */
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        
        /* Background dark color */
        .stApp {
            background-color: #0c0c0e;
        }
        
        /* Header Gradient */
        .header-container {
            padding: 1.5rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            margin-bottom: 2rem;
        }
        .title-gradient {
            background: linear-gradient(135deg, #FE2C55 0%, #25F4EE 50%, #FFD700 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.8rem;
            font-weight: 800;
            letter-spacing: -0.5px;
        }
        .subtitle-muted {
            color: #8E8E93;
            font-size: 1.1rem;
            margin-top: 0.2rem;
        }
        
        /* Metric Cards */
        .metric-card {
            background: #16161a;
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: left;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            border-color: rgba(254, 44, 85, 0.25);
            box-shadow: 0 8px 30px rgba(254, 44, 85, 0.08);
        }
        .metric-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: #FE2C55;
        }
        .metric-card.views::before { background: #25F4EE; }
        .metric-card.engagement::before { background: #FFD93D; }
        .metric-card.creator::before { background: #9B59B6; }
        .metric-card.velocity::before { background: #FE2C55; }

        .metric-label {
            font-size: 0.8rem;
            font-weight: 600;
            color: #8E8E93;
            text-transform: uppercase;
            letter-spacing: 1.2px;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: 800;
            color: #ffffff;
            margin-top: 0.5rem;
        }
        .metric-sub {
            font-size: 0.75rem;
            color: #8E8E93;
            margin-top: 0.3rem;
            font-weight: 500;
        }
        
        /* Section headers */
        .section-header {
            font-size: 1.4rem;
            font-weight: 700;
            color: #ffffff;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* Custom info boxes */
        .insight-box {
            background: rgba(37, 244, 238, 0.03);
            border: 1px dashed rgba(37, 244, 238, 0.2);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1.5rem;
            color: #E5E5EA;
            font-size: 0.95rem;
            line-height: 1.5;
        }
        .insight-icon {
            color: #25F4EE;
            font-weight: bold;
            margin-right: 6px;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_header():
    """Render top title banner and quick guide."""
    st.markdown(
        """
    <div class='header-container'>
        <div class='title-gradient'>TikTok Explore Trend Analytics</div>
        <div class='subtitle-muted'>A practical dashboard for understanding what is trending, which creators are winning, and what content patterns are driving engagement.</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>Quick guide:</span>
        Start with the leaderboard to spot viral patterns, then use category, audio, hashtag, and video format views to understand the drivers behind the performance.
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_kpis_and_summary(df: pd.DataFrame):
    """Render AI business insight summary (KPI cards are now in Tab 1: Overview & Pulse)."""
    if df.empty:
        st.warning("No trending videos match the selected filters. Please adjust the sidebar controls.")
        st.stop()
