"""
Tab 3 - Category Intelligence.
Deep-dive into category performance: views, velocity, tier mix, growth.
"""

import pandas as pd
import plotly.express as px
import streamlit as st


def render_tab_category(
    df_latest: pd.DataFrame,
    df_raw: pd.DataFrame,
    category_colors: dict,
    layout_config: dict,
):
    """Render Tab 3: Category Intelligence."""
    st.markdown(
        """
        <div class='insight-box'>
            <span class='insight-icon'>Category intelligence:</span>
            Understand <strong>which content categories are dominating the Explore feed</strong>,
            how they compare in engagement and velocity, and which creator tier is powering each category.
            Use this to pick the right category before producing content.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_latest.empty:
        st.info("No data available for the selected filters.")
        return

    # --- Row 1: Bar chart + Scatter ---
    cat_agg = (
        df_latest.groupby("category_name")
        .agg(
            total_views=("play_count", "sum"),
            avg_engagement=("engagement_rate", "mean"),
            video_count=("video_id", "count"),
            avg_velocity=("virality_velocity", "mean") if "virality_velocity" in df_latest.columns else ("play_count", "count"),
        )
        .reset_index()
        .sort_values("total_views", ascending=False)
    )

    r1c1, r1c2 = st.columns([3, 2])

    with r1c1:
        fig_bar = px.bar(
            cat_agg,
            x="total_views",
            y="category_name",
            orientation="h",
            color="avg_engagement",
            color_continuous_scale="Plasma",
            title="Total Explore Views by Category (color = Avg Engagement %)",
            labels={"total_views": "Total Views", "category_name": "Category", "avg_engagement": "Avg Eng %"},
            text="video_count",
        )
        fig_bar.update_traces(texttemplate="%{text} videos", textposition="inside")
        fig_bar.update_layout(**layout_config, coloraxis_showscale=False, height=400)
        st.plotly_chart(fig_bar, use_container_width=True)

    with r1c2:
        if "virality_velocity" in df_latest.columns:
            fig_scat = px.scatter(
                cat_agg,
                x="avg_velocity",
                y="avg_engagement",
                size="total_views",
                color="category_name",
                color_discrete_map=category_colors,
                hover_name="category_name",
                text="category_name",
                title="Category: Velocity vs. Engagement",
                labels={"avg_velocity": "Avg Views/hr", "avg_engagement": "Avg Engagement %"},
            )
            fig_scat.update_traces(textposition="top center", textfont_size=9)
            fig_scat.update_layout(**layout_config, showlegend=False, height=400)
            st.plotly_chart(fig_scat, use_container_width=True)
        else:
            fig_eng = px.bar(
                cat_agg.sort_values("avg_engagement", ascending=False),
                x="category_name",
                y="avg_engagement",
                color="category_name",
                color_discrete_map=category_colors,
                title="Average Engagement Rate by Category",
                labels={"avg_engagement": "Avg Engagement %", "category_name": "Category"},
            )
            fig_eng.update_layout(**layout_config, showlegend=False, height=400)
            st.plotly_chart(fig_eng, use_container_width=True)

    # --- Row 2: Creator Tier Mix (100% Stacked Bar Chart) ---
    st.markdown(
        "<div class='section-header'>Creator Tier Mix by Category (Cơ cấu Creator Tier theo Danh mục)</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class='insight-box'>
            <span class='insight-icon'>Insight:</span>
            Biểu đồ chuẩn hóa 100% giúp loại bỏ sự áp đảo về số lượng của các category lớn (như Singing & Dancing).
            Nhờ đó, bạn dễ dàng thấy ngay <strong>tỉ lệ cơ cấu Creator Tier</strong> trong từng ngành hàng:
            danh mục nhiều <strong>Nano creators</strong> là cơ hội mở cho kênh mới; danh mục nhiều <strong>Mega/Macro</strong> có mức độ cạnh tranh cao.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "creator_tier" in df_latest.columns:
        tier_cat = (
            df_latest.groupby(["category_name", "creator_tier"])
            .agg(videos=("video_id", "count"), total_views=("play_count", "sum"))
            .reset_index()
        )

        cat_totals = tier_cat.groupby("category_name")["videos"].transform("sum")
        tier_cat["percentage"] = (tier_cat["videos"] / cat_totals) * 100
        tier_cat["label_text"] = tier_cat["percentage"].apply(lambda p: f"{p:.1f}%" if p >= 7 else "")

        tier_order = [
            "Nano (<10k)",
            "Micro (10k-100k)",
            "Macro (100k-1M)",
            "Mega (1M+)",
        ]
        tier_color_map = {
            "Nano (<10k)": "#25F4EE",
            "Micro (10k-100k)": "#FFD93D",
            "Macro (100k-1M)": "#FE2C55",
            "Mega (1M+)": "#9B59B6",
        }

        tier_cat["creator_tier"] = pd.Categorical(
            tier_cat["creator_tier"],
            categories=[t for t in tier_order if t in tier_cat["creator_tier"].unique()],
            ordered=True,
        )
        tier_cat = tier_cat.sort_values(["category_name", "creator_tier"])

        # Quick insight callouts
        piv = tier_cat.pivot(index="category_name", columns="creator_tier", values="percentage").fillna(0)
        ins_c1, ins_c2 = st.columns(2)

        nano_col = "Nano (<10k)"
        if nano_col in piv.columns and not piv[nano_col].empty:
            top_nano_cat = piv[nano_col].idxmax()
            top_nano_val = piv[nano_col].max()
            with ins_c1:
                st.markdown(
                    f"""
                    <div class='metric-card views'>
                        <div class='metric-label'>🟢 Cơ hội lớn nhất cho Creator mới (Nano Tier)</div>
                        <div class='metric-value' style='font-size: 1.2rem;'>{top_nano_cat}</div>
                        <div class='metric-sub'>Chiếm <b>{top_nano_val:.1f}%</b> video từ kênh Nano — sân chơi còn rất mở</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        mega_col = "Mega (1M+)"
        macro_col = "Macro (100k-1M)"
        comp_series = None
        if mega_col in piv.columns and macro_col in piv.columns:
            comp_series = piv[mega_col] + piv[macro_col]
        elif mega_col in piv.columns:
            comp_series = piv[mega_col]
        elif macro_col in piv.columns:
            comp_series = piv[macro_col]

        if comp_series is not None and not comp_series.empty:
            top_comp_cat = comp_series.idxmax()
            top_comp_val = comp_series.max()
            with ins_c2:
                st.markdown(
                    f"""
                    <div class='metric-card engagement'>
                        <div class='metric-label'>⚔️ Danh mục cạnh tranh gay gắt nhất (Macro/Mega)</div>
                        <div class='metric-value' style='font-size: 1.2rem;'>{top_comp_cat}</div>
                        <div class='metric-sub'><b>{top_comp_val:.1f}%</b> video từ kênh lớn — thị trường đã định hình</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        ctrl_col1, _ = st.columns([2, 3])
        with ctrl_col1:
            chart_mode = st.radio(
                "Kiểu hiển thị:",
                ["Chuẩn hóa 100% (Khuyên dùng)", "Số lượng video thực tế"],
                horizontal=True,
                key="cat_tier_chart_mode",
            )

        is_normalized = "100%" in chart_mode

        if is_normalized:
            fig_tier = px.bar(
                tier_cat,
                y="category_name",
                x="percentage",
                color="creator_tier",
                color_discrete_map=tier_color_map,
                category_orders={"creator_tier": tier_order},
                orientation="h",
                text="label_text",
                title="Cơ cấu Creator Tier chuẩn hóa 100% theo Danh mục (% Video Share)",
                labels={
                    "percentage": "Tỉ lệ % trong danh mục",
                    "category_name": "Danh mục",
                    "creator_tier": "Creator Tier",
                },
                custom_data=["videos", "total_views", "percentage"],
            )
            fig_tier.update_traces(
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=11, color="#ffffff"),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Creator Tier: %{fullData.name}<br>"
                    "Tỉ lệ: <b>%{customdata[2]:.1f}%</b><br>"
                    "Số video: %{customdata[0]:,} clips<br>"
                    "Tổng lượt xem: %{customdata[1]:,}<extra></extra>"
                ),
            )
            fig_tier.update_xaxes(range=[0, 100], ticksuffix="%")
        else:
            fig_tier = px.bar(
                tier_cat,
                y="category_name",
                x="videos",
                color="creator_tier",
                color_discrete_map=tier_color_map,
                category_orders={"creator_tier": tier_order},
                orientation="h",
                title="Số lượng video theo Creator Tier & Danh mục",
                labels={
                    "videos": "Số lượng video",
                    "category_name": "Danh mục",
                    "creator_tier": "Creator Tier",
                },
                custom_data=["percentage", "total_views"],
            )
            fig_tier.update_traces(
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Creator Tier: %{fullData.name}<br>"
                    "Số video: <b>%{x:,}</b><br>"
                    "Tỉ lệ: %{customdata[0]:.1f}%<br>"
                    "Tổng lượt xem: %{customdata[1]:,}<extra></extra>"
                ),
            )

        n_cats = tier_cat["category_name"].nunique()
        chart_height = max(400, n_cats * 42)
        fig_tier.update_layout(
            **layout_config,
            barmode="stack",
            height=chart_height,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                title="",
            ),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_tier, use_container_width=True)
    else:
        st.info("creator_tier column not available in the dataset.")

    # --- Row 3: Historical growth (if multiple dates) ---
    st.markdown(
        "<div class='section-header'>Category Growth Over Time</div>",
        unsafe_allow_html=True,
    )
    all_dates = sorted(df_raw["crawled_date"].unique())
    if len(all_dates) < 2:
        st.info(
            "Historical growth chart will appear once you have data from 2+ crawl dates. "
            "Run the crawler again tomorrow to unlock this view."
        )
    else:
        df_growth = (
            df_raw.groupby(["crawled_date", "category_name"])["play_count"]
            .sum()
            .reset_index()
        )
        fig_line = px.line(
            df_growth,
            x="crawled_date",
            y="play_count",
            color="category_name",
            color_discrete_map=category_colors,
            title="Cumulative View Growth Trend by Category",
            labels={"crawled_date": "Crawl Date", "play_count": "Total Views"},
            markers=True,
        )
        fig_line.update_layout(**layout_config)
        st.plotly_chart(fig_line, use_container_width=True)
