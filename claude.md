# TikTok Explore Trend — Project Instructions

## 1. Project Overview

This project builds an end-to-end ELT data pipeline to collect and analyze trending TikTok videos across multiple content categories.

The pipeline covers:

* Data collection using Playwright
* Raw data storage in MinIO (S3-compatible)
* Data transformation using dbt
* Data warehousing using PostgreSQL
* Pipeline orchestration using Apache Airflow
* Data quality validation
* Visualization and monitoring using Streamlit
* Docker-based deployment

## 2. Architecture

Data flow:

TikTok
→ Playwright
→ MinIO (Raw Layer)
→ dbt
→ PostgreSQL Data Warehouse
→ Streamlit Dashboard

Apache Airflow is responsible for scheduling and orchestrating the pipeline.

## 3. Data Engineering Principles

* Keep raw and transformed data separated.
* Use incremental loading whenever possible.
* Avoid hard-coded credentials.
* Validate data before loading it into analytical tables.
* Keep transformations modular and reproducible.
* Design reusable pipeline components.
* Log important pipeline events and errors.

## 4. Data Warehouse

PostgreSQL is used as the analytical data warehouse.

The warehouse should contain:

* Dimension tables for descriptive attributes
* Fact tables for video and engagement metrics
* Appropriate primary and foreign keys
* Incremental models for regularly updated data

dbt is responsible for transformation and data modeling.

## 5. Development Workflow

Before implementing a new feature:

1. Understand the requirement.
2. Check the existing project architecture.
3. Define the expected input and output.
4. Identify affected components.
5. Implement the smallest appropriate change.
6. Test the implementation.
7. Review the generated or modified code.
8. Update documentation when necessary.

## 6. AI-Assisted Development

Claude Code may be used as a development assistant for:

* Code generation
* Debugging
* Refactoring
* Documentation
* Exploring implementation alternatives

AI-generated code must be reviewed and validated before being integrated into the project.

The developer remains responsible for:

* Architecture decisions
* Business and technical requirements
* Code review
* Testing
* Data validation
* Final implementation decisions

## 7. Coding Guidelines

* Prefer clear and modular Python code.
* Use meaningful variable and function names.
* Avoid unnecessary duplication.
* Separate data collection, transformation, validation, and presentation logic.
* Add error handling for external data sources.
* Keep configuration separate from application logic.

## 8. Security

Never commit:

* API keys
* Passwords
* Access tokens
* Private credentials
* Environment-specific secrets

Use environment variables or `.env` files instead.
