import pytest
from src.validate import TikTokItemModel, validate_records

def test_valid_tiktok_item():
    item_dict = {
        "id": "1234567890",
        "desc": "Check out this trending video! #trending",
        "stats": {
            "playCount": 1000,
            "diggCount": 200,
            "commentCount": 15,
            "shareCount": 5,
            "collectCount": 2
        },
        "author": {
            "id": "author_id_999",
            "uniqueId": "tiktok_star",
            "nickname": "TikTok Star",
            "verified": True
        },
        "authorStats": {
            "followerCount": 50000
        },
        "video": {
            "duration": 15,
            "cover": "https://example.com/cover.jpg",
            "playAddr": "https://example.com/video.mp4",
            "width": 720,
            "height": 1280
        },
        "music": {
            "id": "music_id_888",
            "title": "Popular Song",
            "authorName": "Famous Artist",
            "duration": 60,
            "original": False,
            "playUrl": "https://example.com/music.mp3"
        },
        "challenges": [
            {"id": "ch1", "title": "trending"}
        ]
    }
    model = TikTokItemModel(**item_dict)
    assert model.id == "1234567890"
    assert model.stats.playCount == 1000
    assert model.author.uniqueId == "tiktok_star"
    assert model.video.duration == 15
    assert len(model.challenges) == 1
    assert model.music.title == "Popular Song"

def test_missing_required_fields():
    # Missing 'stats'
    item_dict = {
        "id": "1234567890",
        "author": {
            "id": "author_id_999",
            "uniqueId": "tiktok_star"
        },
        "video": {
            "duration": 15,
            "cover": "cover_url",
            "playAddr": "play_url"
        }
    }
    with pytest.raises(Exception):
        TikTokItemModel(**item_dict)

def test_negative_stats():
    item_dict = {
        "id": "1234567890",
        "stats": {
            "playCount": -100,  # Negative count!
            "diggCount": 200,
            "commentCount": 15,
            "shareCount": 5,
            "collectCount": 2
        },
        "author": {
            "id": "author_id_999",
            "uniqueId": "tiktok_star"
        },
        "video": {
            "duration": 15,
            "cover": "cover_url",
            "playAddr": "play_url"
        }
    }
    with pytest.raises(Exception):
        TikTokItemModel(**item_dict)

def test_normalization_malformed_optional():
    item_dict = {
        "id": "1234567890",
        "stats": {
            "playCount": 1000,
            "diggCount": 200,
            "commentCount": 15,
            "shareCount": 5,
            "collectCount": 2
        },
        "author": {
            "id": "author_id_999",
            "uniqueId": "tiktok_star"
        },
        "video": {
            "duration": 15,
            "cover": "cover_url",
            "playAddr": "play_url"
        },
        "music": "not_a_dict_but_a_string",  # Malformed optional!
        "challenges": "not_a_list_either"  # Malformed optional!
    }
    model = TikTokItemModel(**item_dict)
    assert model.id == "1234567890"
    # Should normalize malformed fields to their defaults
    assert model.music.title == ""
    assert model.challenges == []

def test_validate_records_batch():
    batch = {
        "crawled_at": "2026-08-27 07:00:00",
        "categories_crawled": ["All"],
        "item_list": [
            {
                "id": "1",
                "stats": {"playCount": 10, "diggCount": 1, "commentCount": 0, "shareCount": 0, "collectCount": 0},
                "author": {"id": "auth1", "uniqueId": "u1"},
                "video": {"duration": 10, "cover": "c1", "playAddr": "p1"}
            },
            {
                # Invalid: missing stats
                "id": "2",
                "author": {"id": "auth2", "uniqueId": "u2"},
                "video": {"duration": 10, "cover": "c2", "playAddr": "p2"}
            },
            {
                "id": "3",
                "stats": {"playCount": 30, "diggCount": 3, "commentCount": 0, "shareCount": 0, "collectCount": 0},
                "author": {"id": "auth3", "uniqueId": "u3"},
                "video": {"duration": 30, "cover": "c3", "playAddr": "p3"}
            }
        ]
    }
    result = validate_records(batch)
    assert result["total_discovered"] == 3
    assert result["total_videos"] == 2  # 2 valid records
    assert result["total_invalid"] == 1  # 1 invalid record skipped
    assert len(result["item_list"]) == 2
    assert result["item_list"][0]["id"] == "1"
    assert result["item_list"][1]["id"] == "3"
    assert "rejected_list" in result
    assert len(result["rejected_list"]) == 1
    assert result["rejected_list"][0]["item_id"] == "2"
    assert "error" in result["rejected_list"][0]


def test_dead_letter_queue_structure(tmp_path, monkeypatch):
    from src import validate
    monkeypatch.setattr(validate, "PROJECT_ROOT", str(tmp_path))

    rejected_data = {
        "crawled_at": "2026-09-14 10:00:00",
        "date": "2026-09-14",
        "total_rejected": 1,
        "rejected_list": [
            {
                "item_id": "bad_item_1",
                "error": "Field required: stats",
                "rejected_at": "2026-09-14 10:00:01",
                "raw_record": {"id": "bad_item_1"}
            }
        ]
    }
    # Test local write without error
    dlq_path = validate.write_rejected_json("2026-09-14", rejected_data)
    assert dlq_path is not None
    assert "rejected_explore_2026-09-14.json" in dlq_path
    
    # Verify empty rejected list returns None
    assert validate.write_rejected_json("2026-09-14", {"rejected_list": []}) is None


def test_new_analytical_attributes():
    item_dict = {
        "id": "7693226011021987092",
        "desc": "Check out this AI review! #review #tips",
        "stats": {
            "playCount": 50000,
            "diggCount": 4200,
            "commentCount": 150,
            "shareCount": 80,
            "collectCount": 200,
            "repostCount": 45
        },
        "author": {
            "id": "author_1",
            "uniqueId": "tech_reviewer",
            "nickname": "Tech Reviewer",
            "verified": True
        },
        "authorStats": {
            "followerCount": 150000,
            "heartCount": 2500000,
            "videoCount": 350
        },
        "video": {
            "duration": 45,
            "cover": "https://example.com/cover.jpg",
            "playAddr": "https://example.com/video.mp4",
            "width": 1080,
            "height": 1920
        },
        "music": {
            "id": "m1",
            "title": "Commercial Sound",
            "is_commerce_music": True
        },
        "ShowAIGC": True,
        "textLanguage": "vi"
    }
    model = TikTokItemModel(**item_dict)
    assert model.stats.repostCount == 45
    assert model.authorStats.heartCount == 2500000
    assert model.authorStats.videoCount == 350
    assert model.music.is_commerce_music is True
    assert model.ShowAIGC is True
    assert model.textLanguage == "vi"


