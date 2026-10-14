# TikTok Explore Trend Analytics — Portfolio Summary

## Phase 1: Portfolio-ready foundation

This project is structured as a complete data product rather than a one-off notebook. It covers the full lifecycle of a data workflow:

- Ingestion: Playwright-based extraction from TikTok Explore
- Storage: raw JSON snapshots saved locally and in MinIO/S3-compatible storage
- Quality gating: Pydantic validation for malformed or low-value records
- Warehouse loading: PostgreSQL staging table with UPSERT logic
- Transformation: dbt models for staging and analytics marts
- Reporting: Streamlit dashboard for trend exploration
- Automation: Airflow orchestration and Docker-based environment management

This makes the project suitable for GitHub portfolio presentation and for demonstrating a realistic end-to-end data engineering workflow.

## Phase 3: Business analytics and insight generation

The analytical layer is designed to help answer key business questions:

- Which content categories are trending?
- Which videos generate the strongest engagement rates?
- Which creators and verified accounts seem most effective?
- Which video duration ranges or formats perform best?
- Which audio tracks or hashtags are associated with virality?

The dashboard includes 8 specialized tabs structured around an **Analytical Decision Funnel**:

1. **Overview & Pulse**: Executive KPIs & 4-quadrant Virality vs. Engagement Signal Matrix
2. **Viral Leaderboard**: Sortable ranking with Virality Velocity (views/hr) & video age
3. **Category Intelligence**: Total views, velocity, and 100% normalized stacked bar for Creator Tier mix
4. **Content DNA**: Consolidated format sweet spots (<15s to >60s), audio intelligence & hashtag reach
5. **Creator Intelligence**: Follower vs. view distribution (log-scale algorithm proof) & Tier segmentation
6. **Video Auditing Tool**: Direct inline media player, aspect ratio, and AIGC/ad metadata auditing
7. **Trend Predictor**: Machine learning viral probability scoring & feature importance
8. **System & Data Health**: Data pipeline reliability, freshness, and dbt data quality test monitoring

These features turn raw data into actionable creative intelligence rather than only raw metrics.

## Phase 4: Data product evolution toward decision support

The project moves beyond simple reporting toward a lightweight decision-support product by structuring the data as a reusable analytics layer:

- fact table for daily video performance
- dimension table for unique video metadata
- consistent staging model for downstream analysis
- SQL analytics queries for repeated business analysis
- dashboard filters for different content decisions and creator segmentation

The resulting product is useful to stakeholders asking:
- What content should we replicate?
- What is the best category to prioritize?
- Which creators show the strongest engagement efficiency?
- Which themes and formats are most promising for future content?

## Outcome

The project now demonstrates capability across three dimensions:

1. Data engineering: collection, validation, load, orchestration
2. Data analytics: trend monitoring, KPI analysis, insight extraction
3. Business storytelling: dashboard and decision-oriented reporting

This is a strong foundation for a portfolio project and a credible starting point for further production-grade enhancement.
