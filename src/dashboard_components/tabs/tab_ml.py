"""
Tab 8: ML Trend Predictor (Duration, Posting Time, Hashtags, and Random Forest views prediction).
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ast
import re

MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "trend_predictor.joblib")


def parse_hashtag_count(x, desc: str = "") -> int:
    """Safely parse hashtag count from list, JSON string, Python repr, or text description."""
    if isinstance(x, list):
        return len(x)
    if isinstance(x, str) and x.strip():
        s = x.strip()
        # 1. Standard JSON parsing
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return len(parsed)
        except Exception:
            pass
        # 2. Python list literal representation (e.g. "['tag1', 'tag2']")
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, (list, tuple, set)):
                return len(parsed)
        except Exception:
            pass
        # 3. Quoted strings inside brackets
        tags = re.findall(r"['\"]([^'\"]+)['\"]", s)
        if tags:
            return len(tags)

    # 4. Fallback: extract hashtags from video description
    if isinstance(desc, str) and "#" in desc:
        desc_tags = re.findall(r"#([a-zA-Z0-9_\u00C0-\u024F\u1E00-\u1EFF]+)", desc)
        if desc_tags:
            return len(desc_tags)

    return 0


def render_tab_ml(df: pd.DataFrame, layout_config: dict):
    """Render ML Trend Predictor tab."""
    st.markdown("<div class='section-header'>ML Trend Predictor</div>", unsafe_allow_html=True)

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>Model Overview:</span> 
        This system uses a <strong>Random Forest Regressor</strong> machine learning model that analyzes correlations between features: 
        video duration, author follower count, verification status, ad flag, category, and hashtag count to predict 
        the potential view count of a new video.
    </div>
    """,
        unsafe_allow_html=True,
    )

    df_ml = df.copy()
    df_ml["hashtag_count"] = df_ml.apply(
        lambda r: parse_hashtag_count(r.get("hashtag_list"), r.get("video_desc", "")), axis=1
    )
    if "created_at" in df_ml.columns:
        df_ml["created_at"] = pd.to_datetime(df_ml["created_at"], errors="coerce")
        missing_mask = df_ml["created_at"].isna()
        if missing_mask.any() and "video_id" in df_ml.columns:
            def _extract_ts(vid):
                try:
                    s = str(vid).strip()
                    if s.isdigit():
                        return pd.to_datetime(int(s) >> 32, unit="s", utc=True)
                except Exception:
                    pass
                return pd.NaT
            df_ml.loc[missing_mask, "created_at"] = df_ml.loc[missing_mask, "video_id"].apply(_extract_ts)

    df_ml = df_ml.dropna(
        subset=["play_count", "video_duration", "author_followers", "category_name"]
    )
    df_ml = df_ml[(df_ml["play_count"] > 0) & (df_ml["video_duration"] > 0)]

    if len(df_ml) < 10:
        st.warning("Not enough data for Machine Learning analysis. A minimum of 10 video records is required.")
        return

    # Check for pre-trained model bundle
    bundle = None
    if os.path.exists(MODEL_PATH):
        try:
            bundle = joblib.load(MODEL_PATH)
        except Exception as e:
            st.warning(f"Could not load saved model: {e}. A new model will be trained.")

    # Train or retrain button
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        retrain_clicked = st.button("🔄 Retrain Model", key="retrain_rf_btn")
    with col_info:
        if bundle and "trained_at" in bundle:
            st.caption(f"Model trained at: **{bundle['trained_at']}** ({bundle.get('total_samples', 0)} videos)")

    if retrain_clicked or bundle is None:
        with st.spinner("Training Random Forest model..."):
            from src.train_predictor import train_and_save_model
            bundle = train_and_save_model(df_ml, output_path=MODEL_PATH)

    if bundle:
        r2 = bundle.get("r2_score", 0.0)
        mae = bundle.get("mae", 0.0)
        feat_imp_records = bundle.get("feature_importances", [])

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown(
                f"""
            <div style='background: #16161a; padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);'>
                <h4 style='margin-top:0; color:#25F4EE;'>Model Performance Metrics</h4>
                <p><strong>Model:</strong> Random Forest Regressor (Optimized Pipeline)</p>
                <p><strong>Accuracy (R² Score):</strong> <code>{r2:.2f}</code></p>
                <p><strong>Mean Absolute Error (MAE):</strong> <code>{int(mae):,} views</code></p>
                <small style='color:#8E8E93;'>* Model is pre-computed and saved as an artifact (.joblib) for instant page loading.</small>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col_m2:
            feat_imp_df = pd.DataFrame(feat_imp_records)
            if not feat_imp_df.empty:
                feat_imp_df["Feature"] = feat_imp_df["Feature"].apply(
                    lambda name: str(name)
                    .replace("cat_", "Category: ")
                    .replace("video_duration", "Duration (seconds)")
                    .replace("author_followers", "Followers Count")
                    .replace("author_verified", "Is Verified Account")
                    .replace("is_ad", "Is Sponsored/Ad")
                    .replace("hashtag_count", "Hashtags Count")
                )

                fig_imp = px.bar(
                    feat_imp_df.head(8).sort_values(by="Importance", ascending=True),
                    x="Importance",
                    y="Feature",
                    orientation="h",
                    title="Feature Importance",
                    color="Importance",
                    color_continuous_scale="Mint",
                )
                fig_imp.update_layout(height=230, margin=dict(l=0, r=0, t=30, b=0), **layout_config)
                st.plotly_chart(fig_imp, use_container_width=True)

    # ──────────────────────────────────────────────────────────────
    # ML SECTION 1: Best Video Duration Recommendation
    # ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("<div class='section-header'>⏱️ Best Video Duration Recommendation</div>", unsafe_allow_html=True)

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>Optimal duration analysis:</span>
        The chart below analyzes the relationship between <strong>video duration</strong> and <strong>engagement rate</strong>.
        The highlighted duration range is where engagement peaks — helping you identify the ideal video length for your content.
    </div>
    """,
        unsafe_allow_html=True,
    )

    df_dur_ml = df_ml[df_ml["video_duration"] > 0].copy()
    if not df_dur_ml.empty:
        max_dur = min(int(df_dur_ml["video_duration"].quantile(0.95)), 180)
        bins = list(range(0, max_dur + 5, 5))
        labels = [f"{b}-{b+5}s" for b in bins[:-1]]
        df_dur_ml["dur_bin"] = pd.cut(
            df_dur_ml["video_duration"].clip(upper=max_dur),
            bins=bins,
            labels=labels,
            include_lowest=True,
        )

        df_dur_agg = (
            df_dur_ml.groupby("dur_bin", observed=True)
            .agg(
                avg_engagement=("engagement_rate", "mean"),
                avg_views=("play_count", "mean"),
                video_count=("video_id", "count"),
            )
            .reset_index()
        )
        df_dur_agg = df_dur_agg[df_dur_agg["video_count"] >= 2]

        if not df_dur_agg.empty:
            best_bin = df_dur_agg.loc[df_dur_agg["avg_engagement"].idxmax()]
            col_dur1, col_dur2 = st.columns([3, 1])

            with col_dur1:
                colors = [
                    "#FE2C55" if row["dur_bin"] == best_bin["dur_bin"] else "#25F4EE"
                    for _, row in df_dur_agg.iterrows()
                ]

                fig_dur_rec = go.Figure()
                fig_dur_rec.add_trace(
                    go.Bar(
                        x=df_dur_agg["dur_bin"].astype(str),
                        y=df_dur_agg["avg_engagement"],
                        marker_color=colors,
                        text=df_dur_agg["video_count"].apply(lambda v: f"{v} videos"),
                        textposition="outside",
                        hovertemplate=(
                            "<b>%{x}</b><br>"
                            "Avg Engagement: %{y:.2f}%<br>"
                            "Avg Views: %{customdata:,.0f}<br>"
                            "<extra></extra>"
                        ),
                        customdata=df_dur_agg["avg_views"],
                    )
                )
                fig_dur_rec.update_layout(
                    title="Average Engagement Rate by Video Duration Range",
                    xaxis_title="Duration Range",
                    yaxis_title="Avg Engagement Rate (%)",
                    **layout_config,
                )
                st.plotly_chart(fig_dur_rec, use_container_width=True)

            with col_dur2:
                st.markdown(
                    f"""
                <div style='background: linear-gradient(135deg, rgba(254, 44, 85, 0.12) 0%, rgba(37, 244, 238, 0.12) 100%);
                            padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08); text-align: center;'>
                    <div style='font-size: 0.85rem; color: #8E8E93; text-transform: uppercase; letter-spacing: 1.5px;'>Optimal Duration</div>
                    <div style='font-size: 2.2rem; font-weight: 800; color: #FE2C55; margin: 0.8rem 0;'>{best_bin['dur_bin']}</div>
                    <div style='font-size: 0.95rem; color: #E5E5EA;'>Avg Engagement: <strong>{best_bin['avg_engagement']:.2f}%</strong></div>
                    <div style='font-size: 0.85rem; color: #8E8E93; margin-top: 0.5rem;'>{int(best_bin['video_count'])} videos analyzed</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                st.markdown("")
                top3_dur = df_dur_agg.nlargest(3, "avg_engagement")
                st.markdown("**Top 3 Duration Ranges:**")
                for i, (_, r) in enumerate(top3_dur.iterrows()):
                    medal = ["🥇", "🥈", "🥉"][i]
                    st.markdown(f"{medal} **{r['dur_bin']}** — {r['avg_engagement']:.2f}% engagement")

    # ──────────────────────────────────────────────────────────────
    # ML SECTION 2: Best Posting Time Prediction
    # ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("<div class='section-header'>🕐 Best Posting Time Prediction (Local Time — GMT+7)</div>", unsafe_allow_html=True)

    st.markdown(
        """
    <div class='insight-box'>
        <span class='insight-icon'>Posting time analysis:</span>
        Based on the video publish timestamps (converted to <strong>Vietnam Local Time GMT+7</strong>),
        this system identifies which <strong>hours and days of the week</strong> yield the highest engagement rates.
        Use these insights to schedule your posts at the optimal viral window.
    </div>
    """,
        unsafe_allow_html=True,
    )

    df_time_ml = df_ml.copy()
    if "created_at" in df_time_ml.columns:
        df_time_ml["created_at"] = pd.to_datetime(df_time_ml["created_at"], errors="coerce")
    else:
        df_time_ml["created_at"] = pd.NaT

    # Fallback to snowflake ID if created_at has nulls
    missing_time = df_time_ml["created_at"].isna()
    if missing_time.any() and "video_id" in df_time_ml.columns:
        def _extract_ts(vid):
            try:
                s = str(vid).strip()
                if s.isdigit():
                    return pd.to_datetime(int(s) >> 32, unit="s", utc=True)
            except Exception:
                pass
            return pd.NaT
        df_time_ml.loc[missing_time, "created_at"] = df_time_ml.loc[missing_time, "video_id"].apply(_extract_ts)

    df_time_ml = df_time_ml.dropna(subset=["created_at"])

    if not df_time_ml.empty:
        # Convert to Vietnam Local Time (GMT+7) for intuitive scheduling
        try:
            if df_time_ml["created_at"].dt.tz is not None:
                df_time_ml["created_at_local"] = df_time_ml["created_at"].dt.tz_convert("Asia/Ho_Chi_Minh")
            else:
                df_time_ml["created_at_local"] = df_time_ml["created_at"].dt.tz_localize("UTC").dt.tz_convert("Asia/Ho_Chi_Minh")
        except Exception:
            df_time_ml["created_at_local"] = df_time_ml["created_at"]

        df_time_ml["post_hour"] = df_time_ml["created_at_local"].dt.hour
        df_time_ml["post_dayofweek"] = df_time_ml["created_at_local"].dt.dayofweek
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        df_time_ml["post_day_name"] = df_time_ml["post_dayofweek"].map({i: d for i, d in enumerate(day_names)})

        col_time1, col_time2 = st.columns([3, 1])

        with col_time1:
            df_heatmap = (
                df_time_ml.groupby(["post_day_name", "post_dayofweek", "post_hour"])
                .agg(avg_engagement=("engagement_rate", "mean"), video_count=("video_id", "count"))
                .reset_index()
                .sort_values(["post_dayofweek", "post_hour"])
            )
            heatmap_pivot = df_heatmap.pivot_table(
                index="post_day_name",
                columns="post_hour",
                values="avg_engagement",
                aggfunc="mean",
            ).reindex(index=day_names, columns=list(range(24)))

            fig_heatmap = go.Figure(
                data=go.Heatmap(
                    z=heatmap_pivot.values,
                    x=[f"{h:02d}:00" for h in heatmap_pivot.columns],
                    y=heatmap_pivot.index,
                    colorscale=[
                        [0, "#0c0c0e"],
                        [0.25, "#1a1a2e"],
                        [0.5, "#16213e"],
                        [0.75, "#FE2C55"],
                        [1, "#FFD93D"],
                    ],
                    hoverongaps=False,
                    hovertemplate="<b>%{y} at %{x}</b><br>Avg Engagement: %{z:.2f}%<br><extra></extra>",
                )
            )
            fig_heatmap.update_layout(
                title="Engagement Rate Heatmap: Day × Hour (GMT+7)",
                xaxis_title="Posting Hour (00:00 - 23:00)",
                yaxis_title="Day of Week",
                **layout_config,
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)

        with col_time2:
            hour_agg = df_time_ml.groupby("post_hour").agg(avg_eng=("engagement_rate", "mean"), count=("video_id", "count")).reset_index()
            hour_agg_filtered = hour_agg[hour_agg["count"] >= 2]
            if hour_agg_filtered.empty:
                hour_agg_filtered = hour_agg[hour_agg["count"] >= 1]
            best_hour = hour_agg_filtered.loc[hour_agg_filtered["avg_eng"].idxmax()] if not hour_agg_filtered.empty else None

            day_agg = df_time_ml.groupby(["post_day_name", "post_dayofweek"]).agg(avg_eng=("engagement_rate", "mean"), count=("video_id", "count")).reset_index().sort_values("post_dayofweek")
            day_agg_filtered = day_agg[day_agg["count"] >= 2]
            if day_agg_filtered.empty:
                day_agg_filtered = day_agg[day_agg["count"] >= 1]
            best_day = day_agg_filtered.loc[day_agg_filtered["avg_eng"].idxmax()] if not day_agg_filtered.empty else None

            if best_hour is not None and best_day is not None:
                start_h = int(best_hour['post_hour'])
                end_h = (start_h + 1) % 24
                st.markdown(
                    f"""
                <div style='background: linear-gradient(135deg, rgba(254, 44, 85, 0.12) 0%, rgba(37, 244, 238, 0.12) 100%);
                            padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08); text-align: center;'>
                    <div style='font-size: 0.85rem; color: #8E8E93; text-transform: uppercase; letter-spacing: 1.5px;'>Golden Hour (GMT+7)</div>
                    <div style='font-size: 2.2rem; font-weight: 800; color: #25F4EE; margin: 0.5rem 0;'>{start_h:02d}:00 - {end_h:02d}:00</div>
                    <div style='font-size: 0.95rem; color: #E5E5EA;'>Avg Engagement: <strong>{best_hour['avg_eng']:.2f}%</strong></div>
                    <div style='font-size: 0.8rem; color: #8E8E93; margin-top: 0.3rem;'>{int(best_hour['count'])} videos posted</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                st.markdown("")
                st.markdown(
                    f"""
                <div style='background: linear-gradient(135deg, rgba(255, 217, 61, 0.12) 0%, rgba(155, 89, 182, 0.12) 100%);
                            padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08); text-align: center;'>
                    <div style='font-size: 0.85rem; color: #8E8E93; text-transform: uppercase; letter-spacing: 1.5px;'>Best Day</div>
                    <div style='font-size: 2.2rem; font-weight: 800; color: #FFD93D; margin: 0.5rem 0;'>{best_day['post_day_name']}</div>
                    <div style='font-size: 0.95rem; color: #E5E5EA;'>Avg Engagement: <strong>{best_day['avg_eng']:.2f}%</strong></div>
                    <div style='font-size: 0.8rem; color: #8E8E93; margin-top: 0.3rem;'>{int(best_day['count'])} videos posted</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("No video posting time data available for analysis.")

    # ──────────────────────────────────────────────────────────────
    # ML SECTION 3: Recommended Hashtag Count
    # ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("<div class='section-header'># Recommended Hashtag Count</div>", unsafe_allow_html=True)

    df_hash_ml = df_ml.copy()
    if not df_hash_ml.empty and df_hash_ml["hashtag_count"].max() > 0:
        df_hash_ml["hashtag_count_capped"] = df_hash_ml["hashtag_count"].clip(upper=15)
        df_hash_agg = (
            df_hash_ml.groupby("hashtag_count_capped")
            .agg(
                avg_engagement=("engagement_rate", "mean"),
                avg_views=("play_count", "mean"),
                video_count=("video_id", "count"),
            )
            .reset_index()
            .rename(columns={"hashtag_count_capped": "hashtag_count"})
        )
        df_hash_filtered = df_hash_agg[df_hash_agg["video_count"] >= 2]
        if df_hash_filtered.empty:
            df_hash_filtered = df_hash_agg[df_hash_agg["video_count"] >= 1]

        if not df_hash_filtered.empty:
            best_hash = df_hash_filtered.loc[df_hash_filtered["avg_engagement"].idxmax()]
            col_hash1, col_hash2 = st.columns([3, 1])

            with col_hash1:
                fig_hash = go.Figure()
                hash_colors = [
                    "#FE2C55" if r["hashtag_count"] == best_hash["hashtag_count"] else "#25F4EE"
                    for _, r in df_hash_filtered.iterrows()
                ]
                fig_hash.add_trace(
                    go.Bar(
                        x=df_hash_filtered["hashtag_count"],
                        y=df_hash_filtered["avg_engagement"],
                        name="Avg Engagement (%)",
                        marker_color=hash_colors,
                        text=df_hash_filtered["video_count"].apply(lambda v: f"{v} vids"),
                        textposition="outside",
                    )
                )
                fig_hash.add_trace(
                    go.Scatter(
                        x=df_hash_filtered["hashtag_count"],
                        y=df_hash_filtered["avg_views"],
                        name="Avg Views",
                        mode="lines+markers",
                        line=dict(color="#FFD93D", width=2),
                        marker=dict(size=8),
                        yaxis="y2",
                    )
                )
                fig_hash.update_layout(
                    title="Engagement Rate & Views by Hashtag Count",
                    xaxis_title="Number of Hashtags",
                    xaxis=dict(dtick=1),
                    yaxis=dict(title="Avg Engagement Rate (%)", side="left"),
                    yaxis2=dict(title="Average Views", side="right", overlaying="y", showgrid=False),
                    legend=dict(x=0.5, y=1.15, orientation="h", xanchor="center"),
                    **layout_config,
                )
                st.plotly_chart(fig_hash, use_container_width=True)

            with col_hash2:
                st.markdown(
                    f"""
                <div style='background: linear-gradient(135deg, rgba(254, 44, 85, 0.12) 0%, rgba(37, 244, 238, 0.12) 100%);
                            padding: 1.5rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08); text-align: center;'>
                    <div style='font-size: 0.85rem; color: #8E8E93; text-transform: uppercase; letter-spacing: 1.5px;'>Optimal Hashtag Count</div>
                    <div style='font-size: 3rem; font-weight: 800; color: #FE2C55; margin: 0.5rem 0;'>{int(best_hash['hashtag_count'])}</div>
                    <div style='font-size: 0.95rem; color: #E5E5EA;'>Avg Engagement: <strong>{best_hash['avg_engagement']:.2f}%</strong></div>
                    <div style='font-size: 0.85rem; color: #8E8E93; margin-top: 0.3rem;'>Avg Views: {int(best_hash['avg_views']):,}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                optimal_range = df_hash_filtered.nlargest(min(3, len(df_hash_filtered)), "avg_engagement")["hashtag_count"]
                low, high = int(optimal_range.min()), int(optimal_range.max())
                st.markdown("")
                st.markdown(
                    f"""
                <div style='background: rgba(37, 244, 238, 0.05); border: 1px dashed rgba(37, 244, 238, 0.3);
                            border-radius: 10px; padding: 0.8rem; font-size: 0.9rem; color: #E5E5EA;'>
                    💡 <strong>Recommendation:</strong> Use between <strong>{low}</strong> and <strong>{high}</strong> hashtags per video.
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No sufficient hashtag distribution data available to generate recommendation.")
    else:
        st.info("No hashtag count data found in the current selection.")
