-- Fact table: daily performance snapshot per video.
with staging as (
    select * from {{ ref('stg_explore_videos') }}
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
    crawled_at
from staging
