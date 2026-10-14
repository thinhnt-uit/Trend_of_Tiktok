{{
    config(
        materialized='incremental',
        unique_key='performance_key',
        on_schema_change='sync_all_columns'
    )
}}

-- Fact table: daily performance snapshot per video (incremental) with core engagement and virality metrics.
with staging as (
    select * from {{ ref('stg_explore_videos') }}
    {% if is_incremental() %}
        where crawled_at > (select coalesce(max(crawled_at), '1970-01-01'::timestamptz) from {{ this }})
    {% endif %}
)

select
    md5(concat(video_id, '_', cast(crawled_date as varchar))) as performance_key,
    video_id,
    category_id,
    category_name,
    crawled_date,
    play_count,
    like_count,
    comment_count,
    share_count,
    collect_count,
    repost_count,
    
    -- Total interactions including modern TikTok reposts
    (like_count + comment_count + share_count + collect_count + repost_count) as total_interactions,

    -- Engagement rate calculated at warehouse level
    case
        when play_count > 0
        then round(cast((like_count + comment_count + share_count + collect_count + repost_count) * 100.0 / play_count as numeric), 2)
        else 0.0
    end as engagement_rate,

    -- Virality Velocity: Views per Hour since creation
    case
        when extract(epoch from (crawled_at - created_at)) > 0
        then round(cast(play_count / (extract(epoch from (crawled_at - created_at)) / 3600.0) as numeric), 1)
        else cast(play_count as numeric)
    end as virality_velocity,

    crawled_at
from staging
