@echo off
echo ==============================================================
echo              TikTok Explore Trend Pipeline Launcher
echo ==============================================================

:: Check Docker containers
echo [1/5] Checking and starting Docker infrastructure...
docker compose -f docker/docker-compose.yml up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start Docker. Please ensure Docker Desktop is running.
    pause
    exit /b %errorlevel%
)

:: Wait for services to be ready
echo Waiting 5 seconds for databases and object storage to be ready...
ping 127.0.0.1 -n 6 > nul

:: Initialize S3 bucket if it doesn't exist
echo [2/5] Initializing S3/MinIO bucket...
.venv\Scripts\python.exe -c "import boto3, os, dotenv; dotenv.load_dotenv(); s3 = boto3.client('s3', endpoint_url=os.getenv('S3_ENDPOINT_URL'), aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'), region_name=os.getenv('AWS_REGION')); bucket = os.getenv('S3_BUCKET_NAME'); s3.create_bucket(Bucket=bucket) if bucket not in [b['Name'] for b in s3.list_buckets().get('Buckets', [])] else print('Bucket ready.')"

:: Step 3: Run the crawler
echo [3/5] Scraping TikTok Explore Page (this takes about 1-2 minutes)...
.venv\Scripts\python.exe src/crawl_explore.py --scroll-rounds 2
if %errorlevel% neq 0 (
    echo [ERROR] Crawler failed.
    pause
    exit /b %errorlevel%
)

:: Step 4: Load raw JSON into PostgreSQL
echo [4/5] Loading raw JSON to PostgreSQL staging...
.venv\Scripts\python.exe src/load.py
if %errorlevel% neq 0 (
    echo [ERROR] Loading script failed.
    pause
    exit /b %errorlevel%
)

:: Step 5: Run dbt model transformations
echo [5/5] Running dbt transformations...
.venv\Scripts\dbt.exe run --project-dir dbt_project --profiles-dir dbt_project
if %errorlevel% neq 0 (
    echo [ERROR] dbt transformation failed.
    pause
    exit /b %errorlevel%
)

echo ==============================================================
echo             Pipeline completed successfully!
echo             Launching Streamlit Dashboard...
echo ==============================================================

:: Run Streamlit Dashboard
.venv\Scripts\streamlit.exe run src/dashboard.py
