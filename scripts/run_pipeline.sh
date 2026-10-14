#!/bin/bash
# Run the full pipeline manually: Crawl → Load → dbt Transform

set -e

echo "============================================"
echo "TikTok Explore — Full Pipeline Run"
echo "============================================"

# Step 1: Crawl
echo "[1/3] Crawling TikTok Explore..."
python src/crawl_explore.py --scroll-rounds 3

# Step 2: Validate
echo "[2/4] Validating crawled data..."
python src/validate.py

# Step 3: Load
echo "[3/4] Loading into PostgreSQL..."
python src/load.py

# Step 4: dbt
echo "[4/4] Running dbt transformations and tests..."
dbt run --project-dir dbt_project --profiles-dir dbt_project
dbt test --project-dir dbt_project --profiles-dir dbt_project

echo "============================================"
echo "Pipeline complete!"
echo "============================================"
