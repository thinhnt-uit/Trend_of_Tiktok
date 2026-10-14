"""
Unit tests for modular components and train_predictor utilities.
"""

import pandas as pd
from src.train_predictor import parse_hashtag_count, prepare_dataset


def test_parse_hashtag_count():
    assert parse_hashtag_count(["trend", "fyp"]) == 2
    assert parse_hashtag_count('["dance", "tiktok", "viral"]') == 3
    assert parse_hashtag_count("invalid_json") == 0
    assert parse_hashtag_count(None) == 0


def test_prepare_dataset_features():
    df = pd.DataFrame([
        {
            "video_id": "v1",
            "category_name": "Comedy",
            "video_duration": 15,
            "author_followers": 10000,
            "author_verified": True,
            "is_ad": False,
            "hashtag_list": ["funny", "skit"],
            "play_count": 5000,
        },
        {
            "video_id": "v2",
            "category_name": "Sports",
            "video_duration": 30,
            "author_followers": 50000,
            "author_verified": False,
            "is_ad": True,
            "hashtag_list": ["football"],
            "play_count": 25000,
        },
    ])
    X, y, all_cats = prepare_dataset(df)
    assert len(X) == 2
    assert "video_duration" in X.columns
    assert "author_followers" in X.columns
    assert "author_verified" in X.columns
    assert "is_ad" in X.columns
    assert "hashtag_count" in X.columns
    assert "cat_Comedy" in X.columns
    assert "cat_Sports" in X.columns
    assert list(y) == [5000.0, 25000.0]
    assert all_cats == ["Comedy", "Sports"]


def test_dashboard_imports():
    """Verify that all modularized dashboard components can be imported cleanly."""
    from src.dashboard_components.styles import PLOTLY_LAYOUT, CATEGORY_COLORS
    from src.dashboard_components.data import fetch_data, convert_df_to_excel
    from src.dashboard_components.sidebar import render_sidebar
    from src.dashboard_components.tabs import (
        render_tab_system,
        render_tab_overview,
        render_tab_leaderboard,
        render_tab_category,
        render_tab_content_dna,
        render_tab_creator,
        render_tab_player,
        render_tab_ml,
    )

    assert isinstance(PLOTLY_LAYOUT, dict)
    assert isinstance(CATEGORY_COLORS, dict)
    assert callable(fetch_data)
    assert callable(convert_df_to_excel)
    assert callable(render_sidebar)
    assert callable(render_tab_system)
    assert callable(render_tab_overview)
    assert callable(render_tab_leaderboard)
    assert callable(render_tab_category)
    assert callable(render_tab_content_dna)
    assert callable(render_tab_ml)

