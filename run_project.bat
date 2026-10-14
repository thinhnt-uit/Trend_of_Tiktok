@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ==============================================================
echo              TikTok Explore Trend Pipeline Launcher
echo ==============================================================

:: 0. Check and setup environment & Python paths
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating .env from .env.example...
        copy .env.example .env > nul
    )
)

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    set "DBT_CMD=.venv\Scripts\dbt.exe"
    set "STREAMLIT_CMD=.venv\Scripts\streamlit.exe"
) else (
    set "PYTHON_CMD=python"
    set "DBT_CMD=dbt"
    set "STREAMLIT_CMD=streamlit"
)

:: 1. Check and start Docker containers
echo [1/5] Checking and starting Docker infrastructure...
docker compose -f docker/docker-compose.yml up -d
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start Docker infrastructure.
    echo Please ensure Docker Desktop is running and try again.
    pause
    exit /b %errorlevel%
)

:: 2. Wait for services and initialize MinIO bucket
echo Waiting 5 seconds for databases and object storage services...
ping 127.0.0.1 -n 6 > nul

echo [2/5] Initializing S3/MinIO bucket...
%PYTHON_CMD% -c "import boto3, os, dotenv; dotenv.load_dotenv(); bucket = os.getenv('S3_BUCKET_NAME', 'tiktok-explore-raw'); s3 = boto3.client('s3', endpoint_url=os.getenv('S3_ENDPOINT_URL'), aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'), region_name=os.getenv('AWS_REGION')); s3.create_bucket(Bucket=bucket) if bucket not in [b['Name'] for b in s3.list_buckets().get('Buckets', [])] else print('Bucket ready.')"
if %errorlevel% neq 0 (
    echo [WARNING] MinIO initialization had a minor issue, continuing pipeline...
)

:: 3. Run the TikTok crawler
echo [3/5] Scraping TikTok Explore Page (this takes about 1-2 minutes)...
%PYTHON_CMD% src/crawl_explore.py --scroll-rounds 2
if %errorlevel% neq 0 (
    echo [ERROR] Crawler failed.
    pause
    exit /b %errorlevel%
)

:: 3.5. Validate crawled data
echo [3.5/5] Validating crawled JSON data...
%PYTHON_CMD% src/validate.py
if %errorlevel% neq 0 (
    echo [ERROR] Data validation failed.
    pause
    exit /b %errorlevel%
)

:: 4. Load raw JSON into PostgreSQL
echo [4/5] Loading raw JSON to PostgreSQL staging...
%PYTHON_CMD% src/load.py
if %errorlevel% neq 0 (
    echo [ERROR] Loading script failed.
    pause
    exit /b %errorlevel%
)

:: 5. Run dbt model transformations and data tests
echo [5/5] Running dbt transformations and tests...
%DBT_CMD% run --project-dir dbt_project --profiles-dir dbt_project
if %errorlevel% neq 0 (
    echo [ERROR] dbt transformation failed.
    pause
    exit /b %errorlevel%
)

%DBT_CMD% test --project-dir dbt_project --profiles-dir dbt_project
if %errorlevel% neq 0 (
    echo [ERROR] dbt testing failed.
    pause
    exit /b %errorlevel%
)

echo.
echo ==============================================================
echo             Pipeline completed successfully!
echo             Launching Streamlit Dashboard...
echo ==============================================================
echo.

:: 6. Launch Streamlit Dashboard
%STREAMLIT_CMD% run src/dashboard.py

pause
