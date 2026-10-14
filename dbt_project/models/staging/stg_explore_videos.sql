with source as (
    select * from {{ source('public', 'stg_tiktok_explore_videos') }}
),

renamed as (
    select
        id                              as video_id,
        crawled_date,
        video_desc,
        author_id,
        author_username,
        author_nickname,
        category_id,
        category_name,
        play_count,
        like_count,
        comment_count,
        share_count,
        collect_count,
        -- New analytical virality metric: Repost Count
        cast(coalesce(raw_item->'statsV2'->>'repostCount', raw_item->'stats'->>'repostCount', '0') as integer) as repost_count,
        coalesce(nullif(create_time, 0), case when id ~ '^[0-9]+$' then (id::bigint >> 32) else null end) as create_time,
        to_timestamp(coalesce(nullif(create_time, 0), case when id ~ '^[0-9]+$' then (id::bigint >> 32) else null end)) as created_at,
        crawled_at,
        loaded_at,

        -- Author profile & engagement depth
        author_followers,
        author_verified,
        cast(coalesce(raw_item->'authorStats'->>'heartCount', '0') as bigint) as author_heart_count,
        cast(coalesce(raw_item->'authorStats'->>'videoCount', '0') as integer) as author_video_count,
        is_ad,

        -- Content & AI metadata
        cast(coalesce(raw_item->>'ShowAIGC', 'false') as boolean) as is_aigc,
        coalesce(nullif(raw_item->>'textLanguage', ''), 'unknown') as caption_language,

        -- Extract video metadata from JSONB
        cast(video_info->>'duration' as integer)    as video_duration,
        video_info->>'cover'                        as video_cover_url,
        video_info->>'playAddr'                     as video_play_url,
        cast(video_info->>'width' as integer)       as video_width,
        cast(video_info->>'height' as integer)      as video_height,

        -- Extract music metadata
        music_info->>'id'                           as music_id,
        music_info->>'title'                        as music_title,
        music_info->>'authorName'                   as music_author,
        music_info->>'playUrl'                      as music_play_url,
        cast(music_info->>'duration' as integer)    as music_duration,
        cast(music_info->>'original' as boolean)    as music_is_original,
        cast(coalesce(raw_item->'music'->>'is_commerce_music', 'false') as boolean) as music_is_commerce,

        -- Hashtags as array
        hashtags                                    as hashtag_list,

        -- Preserve raw JSON for ad-hoc queries only at staging level
        raw_item

    from source
),

-- Filter out ads (brand-sponsored content): keep only organic creator videos
organic_only as (
    select * from renamed
    where coalesce(is_ad, false) = false
),

-- Deduplicate: each video appears only once per crawl day
deduped as (
    select *,
        row_number() over (
            partition by video_id, crawled_date
            order by crawled_at desc
        ) as _row_num
    from organic_only
)

select
    video_id,
    crawled_date,
    video_desc,
    author_id,
    author_username,
    author_nickname,
    category_id,
    category_name,
    play_count,
    like_count,
    comment_count,
    share_count,
    collect_count,
    repost_count,
    create_time,
    created_at,
    crawled_at,
    loaded_at,
    author_followers,
    author_verified,
    author_heart_count,
    author_video_count,
    is_aigc,
    caption_language,
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
    raw_item
from deduped
where _row_num = 1
