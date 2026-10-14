"""
Airflow DAG: TikTok Explore — Daily Pipeline
Crawl trending videos → Validate → Load to Postgres → dbt Transform → dbt Test
"""

import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

# Fetch configs dynamically from environment variables, falling back to sensible defaults
IMAGE_NAME   = os.getenv("DOCKER_IMAGE_NAME", "tiktok-explore-pipeline:latest")
NETWORK_NAME = os.getenv("DOCKER_NETWORK_NAME", "docker_default")
PROJECT_DIR  = os.getenv("AIRFLOW_PROJECT_DIR") or os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

# Connection credentials
DB_HOST               = os.getenv("DB_HOST", "postgres")
DB_PORT               = os.getenv("DB_PORT", "5432")
DB_NAME               = os.getenv("DB_NAME", "tiktok_explore")
DB_USER               = os.getenv("DB_USER", "postgres")
DB_PASSWORD           = os.getenv("DB_PASSWORD", "postgres")
S3_ENDPOINT_URL       = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")
AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
AWS_REGION            = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME        = os.getenv("S3_BUCKET_NAME", "tiktok-explore-raw")

MOUNTS = [
    Mount(
        source=os.path.join(PROJECT_DIR, "data"),
        target="/app/data",
        type="bind",
    ),
    Mount(
        source=os.path.join(PROJECT_DIR, "dbt_project"),
        target="/app/dbt_project",
        type="bind",
    ),
]

ENV_FILE = os.path.join(PROJECT_DIR, ".env")
if os.path.exists(ENV_FILE):
    MOUNTS.append(
        Mount(
            source=ENV_FILE,
            target="/app/.env",
            type="bind",
        )
    )

default_args = {
    "owner":             "data_engineer",
    "depends_on_past":   False,
    "start_date":        datetime(2026, 6, 14),
    "email_on_failure":  False,
    "email_on_retry":    False,
    "retries":           2,
    "retry_delay":       timedelta(minutes=3),
    "execution_timeout": timedelta(minutes=15),  # Prevent tasks from hanging
}

with DAG(
    dag_id="tiktok_explore_daily_pipeline",
    description="Daily pipeline: Crawl TikTok Explore → Validate → Load to Postgres → dbt Transform → dbt Test",
    default_args=default_args,
    schedule_interval="0 8 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["tiktok", "explore", "data-engineering", "daily"],
) as dag:

    crawl_task = DockerOperator(
        task_id="crawl_tiktok_explore",
        image=IMAGE_NAME,
        command="python src/crawl_explore.py --scroll-rounds 3",
        network_mode=NETWORK_NAME,
        mounts=MOUNTS,
        auto_remove="success",
        docker_url="unix://var/run/docker.sock",
        mount_tmp_dir=False,
        environment={
            "DB_HOST":              DB_HOST,
            "DB_PORT":              DB_PORT,
            "DB_NAME":              DB_NAME,
            "DB_USER":              DB_USER,
            "DB_PASSWORD":          DB_PASSWORD,
            "S3_ENDPOINT_URL":      S3_ENDPOINT_URL,
            "AWS_ACCESS_KEY_ID":    AWS_ACCESS_KEY_ID,
            "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
            "AWS_REGION":           AWS_REGION,
            "S3_BUCKET_NAME":       S3_BUCKET_NAME,
            "PYTHONPATH":           "/app",
        },
    )

    validate_task = DockerOperator(
        task_id="validate_tiktok_explore",
        image=IMAGE_NAME,
        command="python src/validate.py",
        network_mode=NETWORK_NAME,
        mounts=MOUNTS,
        auto_remove="success",
        docker_url="unix://var/run/docker.sock",
        mount_tmp_dir=False,
        environment={
            "DB_HOST":              DB_HOST,
            "DB_PORT":              DB_PORT,
            "DB_NAME":              DB_NAME,
            "DB_USER":              DB_USER,
            "DB_PASSWORD":          DB_PASSWORD,
            "S3_ENDPOINT_URL":      S3_ENDPOINT_URL,
            "AWS_ACCESS_KEY_ID":    AWS_ACCESS_KEY_ID,
            "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
            "AWS_REGION":           AWS_REGION,
            "S3_BUCKET_NAME":       S3_BUCKET_NAME,
            "PYTHONPATH":           "/app",
        },
    )

    load_task = DockerOperator(
        task_id="load_to_postgres_staging",
        image=IMAGE_NAME,
        command="python src/load.py",
        network_mode=NETWORK_NAME,
        mounts=MOUNTS,
        auto_remove="success",
        docker_url="unix://var/run/docker.sock",
        mount_tmp_dir=False,
        environment={
            "DB_HOST":              DB_HOST,
            "DB_PORT":              DB_PORT,
            "DB_NAME":              DB_NAME,
            "DB_USER":              DB_USER,
            "DB_PASSWORD":          DB_PASSWORD,
            "S3_ENDPOINT_URL":      S3_ENDPOINT_URL,
            "AWS_ACCESS_KEY_ID":    AWS_ACCESS_KEY_ID,
            "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
            "AWS_REGION":           AWS_REGION,
            "S3_BUCKET_NAME":       S3_BUCKET_NAME,
            "PYTHONPATH":           "/app",
        },
    )

    dbt_task = DockerOperator(
        task_id="dbt_transform",
        image=IMAGE_NAME,
        command="dbt run --project-dir dbt_project --profiles-dir dbt_project",
        network_mode=NETWORK_NAME,
        mounts=MOUNTS,
        auto_remove="success",
        docker_url="unix://var/run/docker.sock",
        mount_tmp_dir=False,
        environment={
            "DB_HOST":     DB_HOST,
            "DB_PORT":     DB_PORT,
            "DB_NAME":     DB_NAME,
            "DB_USER":     DB_USER,
            "DB_PASSWORD": DB_PASSWORD,
            "PYTHONPATH":  "/app",
        },
    )

    dbt_test_task = DockerOperator(
        task_id="dbt_test",
        image=IMAGE_NAME,
        command="dbt test --project-dir dbt_project --profiles-dir dbt_project",
        network_mode=NETWORK_NAME,
        mounts=MOUNTS,
        auto_remove="success",
        docker_url="unix://var/run/docker.sock",
        mount_tmp_dir=False,
        environment={
            "DB_HOST":     DB_HOST,
            "DB_PORT":     DB_PORT,
            "DB_NAME":     DB_NAME,
            "DB_USER":     DB_USER,
            "DB_PASSWORD": DB_PASSWORD,
            "PYTHONPATH":  "/app",
        },
    )

    crawl_task >> validate_task >> load_task >> dbt_task >> dbt_test_task
