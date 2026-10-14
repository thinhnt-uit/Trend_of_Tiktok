-- ============================================================
-- TikTok Explore Trend — Analytical Queries
-- Run against public_analytics schema after dbt transform
-- ============================================================

-- 1. Top 20 videos by view count (latest crawl)
SELECT
    dv.video_id,
    dv.video_desc,
    dv.author_nickname,
    dv.category_name,
    fp.play_count,
    fp.like_count,
    fp.comment_count,
    fp.share_count
FROM public_analytics.fact_video_performance fp
JOIN public_analytics.dim_videos dv ON dv.video_id = fp.video_id
WHERE fp.crawled_date = (SELECT MAX(crawled_date) FROM public_analytics.fact_video_performance)
ORDER BY fp.play_count DESC
LIMIT 20;


-- 2. Category leaderboard — total views & likes per category
SELECT
    category_name,
    COUNT(DISTINCT video_id)   AS video_count,
    SUM(play_count)            AS total_views,
    SUM(like_count)            AS total_likes,
    ROUND(AVG(like_count), 0)  AS avg_likes_per_video
FROM public_analytics.fact_video_performance
WHERE crawled_date = (SELECT MAX(crawled_date) FROM public_analytics.fact_video_performance)
GROUP BY category_name
ORDER BY total_views DESC;


-- 3. Hashtag popularity — extracted from dim_videos
SELECT
    tag,
    COUNT(*)               AS usage_count,
    SUM(fp.play_count)     AS total_views,
    SUM(fp.like_count)     AS total_likes
FROM public_analytics.dim_videos dv
CROSS JOIN LATERAL jsonb_array_elements_text(dv.hashtag_list) AS tag
JOIN public_analytics.fact_video_performance fp
  ON fp.video_id = dv.video_id
 AND fp.crawled_date = (SELECT MAX(crawled_date) FROM public_analytics.fact_video_performance)
GROUP BY tag
ORDER BY total_views DESC
LIMIT 30;


-- 4. Day-over-day view growth per video (requires multiple crawl days)
SELECT
    video_id,
    crawled_date,
    play_count,
    LAG(play_count) OVER (PARTITION BY video_id ORDER BY crawled_date) AS prev_play_count,
    play_count - COALESCE(LAG(play_count) OVER (PARTITION BY video_id ORDER BY crawled_date), 0) AS view_growth
FROM public_analytics.fact_video_performance
ORDER BY video_id, crawled_date;


-- 5. Average engagement rate by category
SELECT
    category_name,
    ROUND(AVG(like_count::numeric / NULLIF(play_count, 0) * 100), 2) AS avg_like_rate_pct,
    ROUND(AVG(comment_count::numeric / NULLIF(play_count, 0) * 100), 2) AS avg_comment_rate_pct,
    ROUND(AVG(share_count::numeric / NULLIF(play_count, 0) * 100), 2) AS avg_share_rate_pct
FROM public_analytics.fact_video_performance
WHERE crawled_date = (SELECT MAX(crawled_date) FROM public_analytics.fact_video_performance)
GROUP BY category_name
ORDER BY avg_like_rate_pct DESC;
