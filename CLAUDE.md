# CLAUDE.md — AI & Development Guidelines

This file serves as the configuration and collaboration guide for **Claude Code** (and other AI coding assistants) inside the TikTok Trend Analytics repository.

---

## 🛠️ Development & Validation Commands

Use these exact commands when prompting the AI to run, test, or validate the code:

### 1. Python Environment & Scraper
* **Run Scraper**: `python src/crawl_explore.py`
* **Test Database Loader**: `python src/load.py`
* **Verify dependencies**: `pip install -r requirements.txt`

### 2. dbt Transformations (PostgreSQL)
* **Compile dbt**: `dbt compile --project-dir dbt_project --profiles-dir dbt_project`
* **Run dbt Models**: `dbt run --project-dir dbt_project --profiles-dir dbt_project`
* **Test dbt constraints**: `dbt test --project-dir dbt_project --profiles-dir dbt_project`

### 3. Docker Infrastructure
* **Start services**: `docker compose -f docker/docker-compose.yml up -d`
* **Stop services**: `docker compose -f docker/docker-compose.yml down`

### 4. Streamlit Dashboard
* **Launch UI**: `streamlit run src/dashboard.py`

---

## 📐 Coding Guidelines & Standards

To maintain codebase quality and consistency, the AI assistant must adhere to these rules:

### 🐍 Python (Scraper & Loader)
* **Error Handling**: Always use explicit exception handling and log errors to stdout.
* **Playwright**: Utilize Playwright with proper browser context/cookie preservation to prevent anti-bot detection.
* **DB Connections**: Wrap database connections and cursors in context managers or try-finally blocks (e.g., in `src/load.py` and `src/dashboard.py`) to prevent connection leaks.
* **Naming**: Prefer clear, modular, and PEP8-compliant variable and function names.

### 📊 dbt & SQL (Data Warehouse)
* **SQL Formatting**: Keep SQL keywords **lowercase** (e.g., `select`, `from`, `join`, `where`) to maintain consistency with the existing dbt codebase.
* **Staging Layer (`staging/`)**: Perform only basic cleaning, type casting, renaming, and JSONB field extraction.
* **Marts Layer (`marts/`)**: Implement business logic, analytical joins, and de-duplication.
* **Deduplication**: Deduplicate TikTok JSONB snapshots using window functions: `row_number() over (partition by video_id order by crawled_at desc)`.

---

## 🔒 Security & Credentials

Never hardcode or commit:
* API keys, database passwords, or access tokens.
* Environment-specific configurations or local paths.
* **Action**: Always load configuration via environment variables (using python-dotenv) or reference `.env` values.

---

## 🤖 Structured AI-Assisted Workflow

For adding new features, debugging, or refactoring:

1. **Understand Specification**: Define the inputs, target outputs, and constraints before modifying code.
2. **Context Feeding**: Feed this `CLAUDE.md` and related schemas/requirements to the AI agent.
3. **Iterative Code Gen**: Generate code incrementally (e.g. schema definitions first, then model SQL).
4. **Validation**: Execute the verification commands listed in Section 1 to ensure correctness before committing.
