# TikTok Explore Trend — Data Engineering Pipeline

An end-to-end data engineering project that automatically crawls organic trending videos from TikTok's Explore page, validates and stores raw data in object storage, transforms it into an analytics-ready data warehouse, and serves insights via an interactive dashboard.

> **Stack**: Python · Playwright · Pydantic v2 · MinIO · PostgreSQL · dbt · Apache Airflow · Streamlit · Plotly · Scikit-learn · Docker

---

## 📌 Project positioning

This project is designed as a practical data product for monitoring TikTok trend signals and turning them into business insight. It is especially relevant for:

- Content creators who want to understand what is trending and why
- Social media teams who need category-level and creator-level performance data
- Analysts who want a repeatable workflow from raw social data to dashboard insight
- Data engineers who want to see a full pipeline from crawl to warehouse to BI

### Business value
This project turns raw social data into structured, queryable insight that can answer questions such as:
- Which categories are currently attracting the most attention?
- Which creators are converting attention into strong engagement?
- Which video durations, sounds, and hashtags are outperforming the baseline?
- What content patterns are trending and worth replicating?

### Target users
- Marketing and content planning teams
- Social media analysts
- Creator strategy teams
- Portfolio reviewers and hiring managers looking for end-to-end data engineering experience

### Roadmap alignment
This project targets three practical phases:

- Phase 1: Portfolio-ready foundation
  - End-to-end pipeline, clear architecture, reproducible setup, and clean documentation
- Phase 3: Insight-rich analytics
  - Trend monitoring by category and time
  - Creator performance, audio, hashtag, and format analysis
- Phase 4: Decision-support data product
  - Repeatable analytics model and business-facing dashboard
  - Insight-oriented views for strategic content planning

## 🧭 How to use this project

This project is intended to be both educational and practical. You can use it in three ways:

1. Learn the full data stack
   - Ingestion with Playwright
   - Data validation with Pydantic v2
   - PostgreSQL staging and warehouse loading
   - Transformation with dbt
   - Visualization & ML inference with Streamlit & Plotly

2. Run it as a trend-monitoring dashboard
   - Collect data from TikTok Explore
   - Load it into the warehouse
   - Explore trend changes by category, sound, creator, and format

3. Use it as a portfolio demonstration
   - Show a real end-to-end data engineering workflow
   - Present business questions and answers using a working dashboard

## 🏗️ Architecture

```
TikTok Explore Page (tiktok.com/explore)
        │
        ▼  Playwright — headless browser + API interception
src/crawl_explore.py  →  raw_explore_{date}.json
        │
        ▼  boto3 — S3-compatible upload
MinIO (tiktok-explore-raw bucket)
        │
        ▼  Pydantic v2 — schema validation + normalization
src/validate.py  →  validated_explore_{date}.json  →  MinIO
        │
        ▼  psycopg2 — transactional UPSERT
PostgreSQL: public.stg_tiktok_explore_videos
        │
        ▼  dbt run
public_staging.stg_explore_videos  (VIEW — typed, renamed fields)
        │
        ├── public_analytics.dim_videos             (unique video records)
        └── public_analytics.fact_video_performance (daily metrics per video)
                │
                ▼  dbt test (15 automated data quality tests)
                │
                ▼  Streamlit + Plotly + Scikit-learn
        src/dashboard.py  →  http://localhost:8501 (8 Specialized Decision Tabs)

Apache Airflow — orchestrates the full pipeline daily at 08:00 AM
```

---

## 📁 Project Structure

```
Trend_of_Tiktok/
├── dags/
│   └── tiktok_explore_dag.py       # Airflow DAG (5 tasks)
├── data/
│   └── raw/                        # Local JSON snapshots (gitignored)
├── dbt_project/
│   ├── models/
│   │   ├── staging/                # stg_explore_videos view + schema tests
│   │   └── marts/                  # dim_videos, fact_video_performance + tests
│   ├── tests/
│   │   └── assert_positive_metrics.sql  # Custom business rule test
│   ├── dbt_project.yml
│   └── profiles.yml
├── docker/
│   └── docker-compose.yml          # PostgreSQL + MinIO + Airflow services
├── docs/
│   ├── dashboard_analytics_guide.md# In-depth Stakeholder & Analyst guide (8 tabs & metrics)
│   ├── version_update_summary.md   # Version 2.0 release notes, technical upgrades & pros/cons
│   └── portfolio_summary.md        # Portfolio presentation summary
├── attribute.md                    # Dictionary of 140+ TikTok API attributes & derived metrics
├── queries/
│   └── trend_analysis.sql          # Ad-hoc analytical queries
├── scripts/
│   ├── run_pipeline.sh             # Manual full pipeline run (Linux/macOS)
│   └── run_dashboard.sh            # Launch Streamlit dashboard
├── src/
│   ├── crawl_explore.py            # Playwright crawler
│   ├── validate.py                 # Pydantic v2 validation layer
│   ├── load.py                     # Validated JSON → Postgres staging
│   ├── dashboard.py                # Streamlit analytics dashboard entry point
│   ├── dashboard_components/       # Modular dashboard architecture
│   │   ├── data.py                 # Data fetching, caching & feature engineering
│   │   ├── sidebar.py              # Filter controls & Excel export
│   │   ├── styles.py               # Dark mode CSS tokens & styling
│   │   └── tabs/                   # 8 analytical tabs
│   │       ├── tab_overview.py     # Executive KPIs & Signal Matrix
│   │       ├── tab_leaderboard.py  # Sortable viral leaderboard & velocity
│   │       ├── tab_category.py     # Category analysis & 100% Stacked Creator Tier
│   │       ├── tab_content_dna.py  # Consolidated Format, Duration, Audio & Hashtags
│   │       ├── tab_creator.py      # Followers vs Views, Creator Tier segmentation
│   │       ├── tab_player.py       # Video auditing & inline media playback
│   │       ├── tab_ml.py           # ML Trend Predictor & feature importance
│   │       └── tab_system.py       # Pipeline & warehouse health monitoring
│   └── utils/
│       ├── db.py                   # Postgres connection helper
│       └── s3.py                   # MinIO/S3 upload & download helpers
├── tests/
│   ├── test_validation.py          # pytest unit tests for validation logic
│   └── test_components.py          # pytest unit tests for dashboard modules
├── .dockerignore
├── .env.example
├── .gitignore
├── CLAUDE.md                       # AI-assisted development guidelines
├── Dockerfile                      # Pipeline container image
├── requirements.txt
└── run_project.bat                 # One-click launcher (Windows)
```

---

## 🚀 Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (≥ 4.x)
- Python 3.11+

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env if needed — defaults work for local Docker setup
```

### 2. Start infrastructure

```bash
docker compose -f docker/docker-compose.yml up -d
```

| Service    | Port        | Purpose                      | Credentials           |
|------------|-------------|------------------------------|-----------------------|
| PostgreSQL | 5433        | Data warehouse               | postgres / postgres   |
| MinIO      | 9000 / 9001 | S3-compatible object storage | minioadmin / minioadmin |
| Airflow    | 8080        | Pipeline scheduler UI        | admin / admin         |

### 3. Create MinIO bucket

Open [http://localhost:9001](http://localhost:9001) and create a bucket named **`tiktok-explore-raw`**.

### 4. Set up local Python environment

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
playwright install chromium
```

### 5. Build the pipeline Docker image

Required for Airflow's DockerOperator tasks.

```bash
docker build -t tiktok-explore-pipeline:latest .
```

---

## 🔄 Running the Pipeline

### Option A — Manual (step by step)

```bash
# 1. Crawl TikTok Explore (all categories, 3 scroll rounds)
python src/crawl_explore.py --scroll-rounds 3

# 2. Validate crawled data
python src/validate.py

# 3. Load validated data into Postgres
python src/load.py

# 4. Run dbt transformations
dbt run --project-dir dbt_project --profiles-dir dbt_project

# 5. Run dbt data quality tests
dbt test --project-dir dbt_project --profiles-dir dbt_project
```

### Option B — Windows one-click

```bat
run_project.bat
```

### Option C — Automated via Airflow

The DAG `tiktok_explore_daily_pipeline` runs automatically at **08:00 AM** daily.

1. Open Airflow UI: [http://localhost:8080](http://localhost:8080)
2. Toggle the DAG **On** → it will run on its next schedule, or click **Trigger DAG** for an immediate run.

---

## ✈️ Airflow DAG — `tiktok_explore_daily_pipeline`

| # | Task ID                  | Command                                              | Timeout | Retries |
|---|--------------------------|------------------------------------------------------|---------|---------|
| 1 | `crawl_tiktok_explore`   | `python src/crawl_explore.py --scroll-rounds 3`      | 15 min  | 2       |
| 2 | `validate_tiktok_explore`| `python src/validate.py`                             | 15 min  | 2       |
| 3 | `load_to_postgres_staging`| `python src/load.py`                                | 15 min  | 2       |
| 4 | `dbt_transform`          | `dbt run --project-dir dbt_project ...`              | 15 min  | 2       |
| 5 | `dbt_test`               | `dbt test --project-dir dbt_project ...`             | 15 min  | 2       |

Each task runs inside the `tiktok-explore-pipeline:latest` Docker container via `DockerOperator`.

---

## 🛡️ Data Validation & Quality

### Pydantic Validation (`src/validate.py`)

Runs between crawl and load. Validates every record individually using **Pydantic v2** — invalid records are skipped and logged; the batch continues.

| Field / JSON Path | Rule | Description |
|---|---|---|
| `id` | Non-empty string | Unique TikTok video ID |
| `author.id`, `author.uniqueId` | Non-empty string | Creator ID and handle |
| `stats.*` (playCount, diggCount, etc.) | Integer ≥ 0 | Core performance counts |
| `statsV2.repostCount` / `stats.repostCount` | Integer ≥ 0 | Video repost count (fallback handled) |
| `authorStats.heartCount`, `videoCount` | Integer ≥ 0 | Creator total channel hearts & video count |
| `video.cover`, `video.playAddr` | Non-empty string | Media preview and playback URLs |
| `video.duration` | Number ≥ 0 | Video length in seconds |
| `music`, `challenges`, `authorStats` | Optional | Malformed values normalized to defaults |

### dbt Tests (15 total)

| Layer | Test |
|---|---|
| Staging | `not_null` on `video_id`, `author_id`, `crawled_date`, `play_count`, `like_count`, `category_name` |
| `dim_videos` | `unique` + `not_null` on `video_id` |
| `fact_video_performance` | `unique` on `performance_key`, `not_null` on `video_id`, `relationships` → `dim_videos` |
| Custom | `assert_positive_metrics` — all metric columns ≥ 0 |

---

## 🗄️ Data Model & Engineered Metrics

| Schema             | Object                      | Type        | Description                                               |
|--------------------|-----------------------------|-------------|-----------------------------------------------------------|
| `public`           | `stg_tiktok_explore_videos` | Table       | Raw staging. Composite PK: `(id, crawled_date)`.          |
| `public_staging`   | `stg_explore_videos`        | View (dbt)  | Typed and renamed columns extracted from staging JSONB.   |
| `public_analytics` | `dim_videos`                | Table (dbt) | Unique video dimension, de-duplicated to latest crawl.    |
| `public_analytics` | `fact_video_performance`    | Table (dbt) | Daily performance metrics per video, with surrogate key.  |

### Key Engineered Features & Business Metrics

- **Virality Velocity (Views/Hour)**:
  $$\text{Virality Velocity} = \frac{\text{play\_count}}{\text{video\_age\_hours}}$$
  Identifies breakout "dark horse" trends in their first 6–24 hours, eliminating historical survival bias.
- **Comprehensive Engagement Rate (%)**:
  $$\text{Engagement Rate} = \frac{\text{Likes} + \text{Comments} + \text{Shares} + \text{Collects (Saves)} + \text{Reposts}}{\text{Play Count}} \times 100$$
  Includes high-intent signals (Saves and Reposts) that heavily weight the TikTok For You algorithm.
- **Creator Tier Segmentation**:
  - **Nano (<10k)**: Emerging creators; open opportunity signal.
  - **Micro (10k–100k)**: Fast-growing accounts with high community engagement.
  - **Macro (100k–1M)**: Established creators with substantial audience reach.
  - **Mega (1M+)**: Top influencers, celebrities, and enterprise media brands.
- **Contextual Attributes**: `video_age_hours`, `is_aigc` (AI content flag), `author_heart_count` (total creator hearts), `caption_language`.

---

## 📊 Dashboard Architecture & Analytics Guide

The Streamlit dashboard is structured around an **Analytical Decision Funnel** spanning 8 specialized tabs:

```bash
streamlit run src/dashboard.py
```
Open [http://localhost:8501](http://localhost:8501).

| # | Tab | Analytical Purpose | Key Visualizations |
|---|---|---|---|
| 1 | **🏠 Overview & Pulse** | Executive snapshot & market temperature in 30 seconds | Executive 5-KPI row, **Virality vs. Engagement Signal Matrix** (4-quadrant scatter: Hot & Sticky, Fast Burn, Niche Gold, Fading), AI automated summary |
| 2 | **🔥 Viral Leaderboard** | In-depth benchmarking and reverse-engineering top 1% | Sortable leaderboard with **Views/hr**, **Video Age (hrs)**, **Tier badges**, drill-down inspector (Likes, Comments, Shares, Saves, Reposts) |
| 3 | **📊 Category Intelligence** | Category-level strategy & market selection | Total Views by Category with Engagement gradient, Velocity vs. Engagement bubble plot, **100% Horizontal Stacked Bar (Creator Tier Mix)**, Growth trendlines |
| 4 | **🎵 Content DNA** | Actionable content production formulas | Vertical (9:16) vs Horizontal performance, Duration sweet spot (<15s, 15-30s, 30-60s, >60s), Trending audio ranking, Commercial audio share, Hashtag reach |
| 5 | **👤 Creator Intelligence** | Creator tier dynamics & influencer vetting | Views vs Followers correlation (log-scale algorithm validation), Creator Tier share, Verified vs Non-verified performance |
| 6 | **🎬 Video Auditing Tool** | Qualitative review & hook analysis | Direct inline video player, audio playback, cover image preview, pixel aspect ratio, ad status, AIGC disclosure |
| 7 | **🤖 Trend Predictor** | Machine learning viral probability forecasting | Interactive viral probability scorer, Feature Importance chart for optimal pre-publishing optimization |
| 8 | **⚙️ System & Data Health** | Data governance & pipeline reliability | Last crawl timestamp, warehouse record counts, dbt test status, data integrity audit |

> 📘 **Detailed Documentation:**
> - [Dashboard Analytics Guide](docs/dashboard_analytics_guide.md) — Comprehensive stakeholder & analyst manual explaining all tabs, charts, and business decisions.
> - [Version Update Summary](docs/version_update_summary.md) — Complete changelog, bug fixes, architecture evolution, and v1 vs. v2 pros & cons.
> - [TikTok Attributes Dictionary](attribute.md) — Complete mapping of 140+ raw API fields and derived features.

---

## 🧪 Tests

```bash
# Unit tests (Pydantic validation logic & dashboard modules)
pytest

# dbt data quality tests (requires running Postgres)
dbt test --project-dir dbt_project --profiles-dir dbt_project
```

---

## ⚙️ Environment Variables

| Variable                | Default                 | Description                          |
|-------------------------|-------------------------|--------------------------------------|
| `DB_HOST`               | `localhost`             | Postgres host                        |
| `DB_PORT`               | `5433`                  | Postgres port                        |
| `DB_NAME`               | `tiktok_explore`        | Postgres database name               |
| `DB_USER`               | `postgres`              | Postgres username                    |
| `DB_PASSWORD`           | `postgres`              | Postgres password                    |
| `S3_ENDPOINT_URL`       | `http://localhost:9000` | MinIO/S3 endpoint                    |
| `AWS_ACCESS_KEY_ID`     | `minioadmin`            | S3 access key                        |
| `AWS_SECRET_ACCESS_KEY` | `minioadmin`            | S3 secret key                        |
| `AWS_REGION`            | `us-east-1`             | S3 region                            |
| `S3_BUCKET_NAME`        | `tiktok-explore-raw`    | S3 bucket name                       |
| `AIRFLOW_PROJECT_DIR`   | *(host project path)*   | Host path mounted into Airflow tasks |

---

## 🛠️ Technologies

| Tool            | Role                                   |
|-----------------|----------------------------------------|
| Python 3.11     | Core scripting and data processing     |
| Playwright      | Headless browser + API interception    |
| Pydantic v2     | Schema enforcement and data validation |
| PostgreSQL 15   | Analytical data warehouse              |
| dbt-postgres    | SQL transformations and dimensional data modeling |
| Apache Airflow  | Pipeline orchestration and automated scheduling |
| MinIO           | S3-compatible local object storage     |
| boto3           | AWS S3 SDK for storage management      |
| Streamlit       | Web application & interactive reporting|
| Plotly          | Rich interactive charts & visualizations|
| Scikit-learn    | ML trend prediction & feature importance modeling |
| Docker          | Containerized multi-service infrastructure |

---

## 🤖 AI-Assisted Development

This project was built using a structured **AI-assisted software engineering** methodology, leveraging **Google Gemini** and **Claude** as collaborative pair programmers.

Key practices:
- Markdown-first specifications to guide AI code generation
- Iterative schema and prompt engineering for dbt models
- Manual code review, linting, and local validation of every AI-generated component

See [CLAUDE.md](CLAUDE.md) for development guidelines and validation commands.
