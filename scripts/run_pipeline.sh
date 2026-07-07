#!/bin/bash
# Run the full pipeline manually: Crawl → Load → dbt Transform

set -e

echo "============================================"
echo "TikTok Explore — Full Pipeline Run"
echo "============================================"

# Step 1: Crawl
echo "[1/3] Crawling TikTok Explore..."
python src/crawl_explore.py --scroll-rounds 3

# Step 2: Load
echo "[2/3] Loading into PostgreSQL..."
python src/load.py

# Step 3: dbt
echo "[3/3] Running dbt transformations..."
dbt run --project-dir dbt_project --profiles-dir dbt_project

echo "============================================"
echo "Pipeline complete!"
echo "============================================"
