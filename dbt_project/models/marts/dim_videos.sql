-- Dimension table: unique video records, de-duplicated to the latest crawl.
with staging as (
    select * from {{ ref('stg_explore_videos') }}
),

ranked as (
    select
        video_id,
        video_desc,
        author_id,
        author_username,
        author_nickname,
        category_id,
        category_name,
        created_at,
        video_duration,
        video_cover_url,
        video_play_url,
        video_download_url,
        video_width,
        video_height,
        video_ratio,
        video_cdn_id,
        music_id,
        music_title,
        music_author,
        music_duration,
        music_is_original,
        hashtag_list,
        crawled_at,
        -- New analytics fields
        author_followers,
        author_verified,
        is_ad,
        music_play_url,
        stickers,
        raw_item,
        row_number() over (partition by video_id order by crawled_at desc) as rn
    from staging
)

select
    video_id,
    video_desc,
    author_id,
    author_username,
    author_nickname,
    category_id,
    category_name,
    created_at,
    video_duration,
    video_cover_url,
    video_play_url,
    video_download_url,
    video_width,
    video_height,
    video_ratio,
    video_cdn_id,
    music_id,
    music_title,
    music_author,
    music_duration,
    music_is_original,
    hashtag_list,
    author_followers,
    author_verified,
    is_ad,
    music_play_url,
    stickers,
    raw_item,
    crawled_at as last_seen_at
from ranked
where rn = 1
