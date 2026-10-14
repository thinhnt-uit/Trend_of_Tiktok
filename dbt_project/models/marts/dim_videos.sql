
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
        video_width,
        video_height,
        music_id,
        music_title,
        music_author,
        music_play_url,
        music_duration,
        music_is_original,
        music_is_commerce,
        hashtag_list,
        crawled_at,
        author_followers,
        author_verified,
        author_heart_count,
        author_video_count,
        is_aigc,
        caption_language,
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
    video_width,
    video_height,
    music_id,
    music_title,
    music_author,
    music_play_url,
    music_duration,
    music_is_original,
    music_is_commerce,
    hashtag_list,
    crawled_at,
    author_followers,
    author_verified,
    false as is_ad,
    author_heart_count,
    author_video_count,
    is_aigc,
    caption_language,

    -- Derived feature 1: Video Age in Hours at crawl time
    round(cast(extract(epoch from (crawled_at - created_at)) / 3600.0 as numeric), 1) as video_age_hours,

    -- Derived feature 2: Creator Tier segmentation
    case
        when author_followers >= 1000000 then 'Mega (1M+)'
        when author_followers >= 100000 then 'Macro (100k-1M)'
        when author_followers >= 10000 then 'Micro (10k-100k)'
        else 'Nano (<10k)'
    end as creator_tier,

    -- Derived feature 3: Rule-based Video Content Format
    case
        when lower(coalesce(video_desc, '')) ~* '(#review|#danhgia|review|đánh giá)' then 'Review'
        when lower(coalesce(video_desc, '')) ~* '(#tutorial|#huongdan|#tips|#meo|hướng dẫn|cách làm)' then 'Tutorial'
        when lower(coalesce(video_desc, '')) ~* '(#vlog|#daily|#cuocsong|vlog|daily life)' then 'Vlog'
        when lower(coalesce(video_desc, '')) ~* '(#pov|pov)' then 'POV'
        when lower(coalesce(video_desc, '')) ~* '(#dance|#nhay|nhảy|vũ đạo)' then 'Dance'
        else 'General / Entertainment'
    end as video_format

from ranked
where rn = 1
