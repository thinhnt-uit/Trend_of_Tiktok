# TikTok Explore Trend — Data Engineering Pipeline

An end-to-end data engineering project that automatically crawls organic trending videos from TikTok's Explore page, stores raw data in cloud object storage, transforms it into an analytics-ready data warehouse, and serves insights via a custom interactive dashboard.

---

## 🏗️ Architecture

```
TikTok Explore Page (tiktok.com/explore)
        │
        ▼ Playwright (Browser Automation + API Interception)
src/crawl_explore.py
        │
        ▼ boto3 (S3-compatible)
MinIO / AWS S3  ──── raw JSON per day
        │
        ▼ psycopg2 UPSERT
PostgreSQL → public.stg_tiktok_explore_videos  (raw staging)
        │
        ▼ dbt run
public_staging.stg_explore_videos              (VIEW — cleaned, typed)
        │
        ├── public_analytics.dim_videos            (Dimension Table)
        └── public_analytics.fact_video_performance (Fact Table)
                │
                ▼ Streamlit + Plotly
         src/dashboard.py  →  http://localhost:8501

Apache Airflow  ─── orchestrates all steps daily at 08:00 AM
```

---

## 📁 Project Structure

```
Trend_of_Tiktok/
├── dags/
│   └── tiktok_explore_dag.py       # Airflow DAG: crawl → load → dbt
├── data/
│   └── raw/                        # Local raw JSON snapshots (gitignored)
├── dbt_project/
│   ├── models/
│   │   ├── staging/                # stg_explore_videos view
│   │   └── marts/                  # dim_videos, fact_video_performance
│   ├── dbt_project.yml
│   └── profiles.yml
├── docker/
│   └── docker-compose.yml          # PostgreSQL + MinIO + Airflow services
├── queries/
│   └── trend_analysis.sql          # Analytical queries
├── scripts/
│   ├── run_pipeline.sh             # Manual full pipeline run
│   └── run_dashboard.sh            # Launch Streamlit dashboard
├── src/
│   ├── crawl_explore.py            # Playwright crawler for Explore page
│   ├── load.py                     # Load raw JSON → Postgres staging
│   ├── dashboard.py                # Streamlit analytics dashboard
│   └── utils/
│       ├── db.py                   # Postgres connection helper
│       └── s3.py                   # MinIO/S3 upload & download
├── Dockerfile
├── requirements.txt
└── .env
```

---

## 🚀 Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (≥ 4.x)
- Python 3.11+ with `venv`

### 1. Configure

```bash
cp .env.example .env
# Edit .env if needed
```

### 2. Start Infrastructure

```bash
docker compose -f docker/docker-compose.yml up -d
```

| Service    | Port        | Purpose                       |
|------------|-------------|-------------------------------|
| PostgreSQL | 5433        | Data Warehouse                |
| MinIO      | 9000 / 9001 | S3-compatible Object Storage  |
| Airflow    | 8080        | Pipeline Scheduler UI         |

### 3. Set Up Python Environment

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
playwright install chromium
```

### 4. Build Pipeline Docker Image

```bash
docker build -t tiktok-explore-pipeline:latest .
```

### 5. Create MinIO Bucket

Open [http://localhost:9001](http://localhost:9001) (user: `minioadmin`, pass: `minioadmin`) and create a bucket named `tiktok-explore-raw`.

---

## 🔄 Running the Pipeline

### Option A — Manual Run

```bash
# Step 1: Crawl
python src/crawl_explore.py

# Step 2: Load into Postgres
python src/load.py

# Step 3: dbt Transform
dbt run --project-dir dbt_project --profiles-dir dbt_project
```

### Option B — Automated (Airflow)

The DAG `tiktok_explore_daily_pipeline` runs daily at **08:00 AM**.

1. Open Airflow: [http://localhost:8080](http://localhost:8080) (admin / admin)
2. Toggle the DAG **On** and trigger

---

## 📊 Dashboard

```bash
streamlit run src/dashboard.py
```

Open [http://localhost:8501](http://localhost:8501).

| Tab                      | Description                                                      |
|--------------------------|------------------------------------------------------------------|
| 🏆 Top Trending          | Ranked table with covers, views, likes, and direct video links   |
| 📊 Category Analysis     | Bar and pie charts of engagement density across explore categories|
| 🏷️ Hashtag Trends        | Top hashtags by views and likes                                  |
| 📽️ Video Player          | Play any video inline, view metadata and historical engagement   |

---

## 🗄️ Data Model

| Schema             | Table / View               | Type        | Description                                              |
|--------------------|-----------------------------|-------------|----------------------------------------------------------|
| `public`           | `stg_tiktok_explore_videos` | Table       | Raw data ingested from crawler. Contains `video_info` JSONB. |
| `public_staging`   | `stg_explore_videos`        | View (dbt)  | Typed and renamed fields. Extracts video/music metadata.  |
| `public_analytics` | `dim_videos`                | Table (dbt) | Unique video records, de-duplicated to latest crawl.      |
| `public_analytics` | `fact_video_performance`    | Table (dbt) | Daily performance metrics per video.                      |

### Explore Categories

| Category          | categoryType |
|-------------------|-------------|
| All               | 123         |
| Singing & Dancing | 120         |
| Comedy            | 119         |
| Sports            | 104         |
| Anime & Comics    | 112         |
| Relationship      | 100         |
| Shows             | 107         |
| Daily Life        | 105         |

---

## 🛠️ Technologies

| Tool              | Role                                    |
|-------------------|-----------------------------------------|
| Python 3.11       | Core scripting language                 |
| Playwright        | Headless browser for API interception   |
| PostgreSQL 15     | Data warehouse                          |
| dbt-postgres      | SQL transformations and data modelling  |
| Apache Airflow    | Pipeline orchestration and scheduling   |
| MinIO             | Local S3-compatible object storage      |
| boto3             | S3 SDK for upload & download            |
| Streamlit         | Interactive analytics dashboard         |
| Plotly            | Interactive charts and visualizations   |
| Docker            | Service containerisation                |

---

## ⚙️ Environment Variables

| Variable               | Default                   | Description             |
|------------------------|---------------------------|-------------------------|
| `DB_HOST`              | `localhost`               | Postgres host           |
| `DB_PORT`              | `5433`                    | Postgres port           |
| `DB_NAME`              | `tiktok_explore`          | Postgres database name  |
| `DB_USER`              | `postgres`                | Postgres username       |
| `DB_PASSWORD`          | `postgres`                | Postgres password       |
| `S3_ENDPOINT_URL`      | `http://localhost:9000`   | MinIO endpoint          |
| `AWS_ACCESS_KEY_ID`    | `minioadmin`              | S3 access key           |
| `AWS_SECRET_ACCESS_KEY`| `minioadmin`              | S3 secret key           |
| `AWS_REGION`           | `us-east-1`               | S3 region               |
| `S3_BUCKET_NAME`       | `tiktok-explore-raw`      | S3 bucket name          |
