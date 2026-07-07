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
        create_time,
        to_timestamp(create_time)       as created_at,
        crawled_at,
        loaded_at,

        -- New analytics fields
        author_followers,
        author_verified,
        is_ad,
        music_play_url,
        stickers,
        raw_item,

        -- Extract video metadata from JSONB
        cast(video_info->>'duration' as integer)    as video_duration,
        video_info->>'cover'                        as video_cover_url,
        video_info->>'playAddr'                     as video_play_url,
        video_info->>'downloadAddr'                 as video_download_url,
        cast(video_info->>'width' as integer)       as video_width,
        cast(video_info->>'height' as integer)      as video_height,
        video_info->>'ratio'                        as video_ratio,
        video_info->>'videoID'                      as video_cdn_id,

        -- Extract music metadata
        music_info->>'id'                           as music_id,
        music_info->>'title'                        as music_title,
        music_info->>'authorName'                   as music_author,
        cast(music_info->>'duration' as integer)    as music_duration,
        cast(music_info->>'original' as boolean)    as music_is_original,

        -- Hashtags as array
        hashtags                                    as hashtag_list

    from source
)

select * from renamed
