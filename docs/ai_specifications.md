# AI-Assisted Development: Code Generation Specifications

This document outlines the structured development templates and prompt procedures used with **Claude Code** and **Gemini Code Assist** during the building of the TikTok Explore Trend pipeline. 

---

## 📋 Methodology Overview

Instead of letting AI write code arbitrarily, we follow a three-step cycle:
1. **Define Specification**: Write exact inputs, target outputs, and constraints in Markdown.
2. **Execute Generation**: Context-feed the specification to the AI agent.
3. **Verify & Refine**: Run compiler/linter/tests and manually audit security and efficiency.

---

## 🛠️ Sample Spec Sheet: dbt Transformation Model

Below is an example of a Markdown specification sheet fed to **Claude Code** to generate the dbt staging model (`stg_explore_videos.sql`):

### 1. Context & Objective
* **Source Database**: PostgreSQL 15
* **Source Table**: `public.stg_tiktok_explore_videos`
* **Target Schema**: `public_staging`
* **Target View**: `stg_explore_videos`
* **Goal**: Extract, clean, and cast fields from the `video_info` JSONB column.

### 2. JSONB Structure Example (for `video_info`)
```json
{
  "duration": 18,
  "cover": "https://p16-common-sign.tiktokcdn.com/...",
  "playAddr": "https://v16-webapp.tiktok.com/...",
  "downloadAddr": "https://v16-webapp.tiktok.com/...",
  "width": 576,
  "height": 1024,
  "ratio": "540p",
  "videoID": "v24044gl0000d8crjbfog65ghbosg5ag"
}
```

### 3. Transformation Rules (Prompt Blueprint)
> **Prompt**: 
> "Generate a dbt staging model (`stg_explore_videos.sql`) using PostgreSQL syntax.
> Sourcing from `public.stg_tiktok_explore_videos`, select all top-level columns and extract/typecast the following nested fields from the `video_info` JSONB column:
> - `duration` -> `video_duration` (cast to integer)
> - `cover` -> `video_cover_url` (text)
> - `playAddr` -> `video_play_url` (text)
> - `downloadAddr` -> `video_download_url` (text)
> - `width` -> `video_width` (cast to integer)
> - `height` -> `video_height` (cast to integer)
> - `ratio` -> `video_ratio` (text)
> - `videoID` -> `video_cdn_id` (text)
>
> Convert `create_time` to timestamp using `to_timestamp(create_time) as created_at`."

---

## 💬 Prompts & Iterations Example

When the dbt model was generated, the AI initially produced SQL syntax containing raw text JSON extraction without data type casting. We iterated using the following prompt:

> **Refinement Prompt**: 
> "The fields `duration`, `width`, and `height` inside `video_info` must be explicitly cast to integers so that they can be used for downstream analytical queries in the marts layer. Please update the query to use `cast(video_info->>'duration' as integer)`."

**Resulting Code (Staging View Snippet):**
```sql
with source as (
    select * from {{ source('public', 'stg_tiktok_explore_videos') }}
),

renamed as (
    select
        id                              as video_id,
        crawled_date,
        video_desc,
        -- ... other top level columns ...
        to_timestamp(create_time)       as created_at,

        -- Extract video metadata from JSONB with type casting
        cast(video_info->>'duration' as integer)    as video_duration,
        video_info->>'cover'                        as video_cover_url,
        video_info->>'playAddr'                     as video_play_url,
        video_info->>'downloadAddr'                 as video_download_url,
        cast(video_info->>'width' as integer)       as video_width,
        cast(video_info->>'height' as integer)      as video_height,
        video_info->>'ratio'                        as video_ratio,
        video_info->>'videoID'                      as video_cdn_id
        -- ... extract music metadata ...
    from source
)
select * from renamed
```
