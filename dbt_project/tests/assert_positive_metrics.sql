-- Test to ensure engagement metrics (including repost_count) are not negative
select
    video_id,
    play_count,
    like_count,
    comment_count,
    share_count,
    collect_count,
    repost_count
from {{ ref('stg_explore_videos') }}
where 
    play_count < 0 
    or like_count < 0 
    or comment_count < 0 
    or share_count < 0 
    or collect_count < 0
    or repost_count < 0
