from app.utils.url_parser import detect_platform


def test_youtube_standard():
    assert detect_platform("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "youtube"


def test_youtube_short():
    assert detect_platform("https://youtu.be/dQw4w9WgXcQ") == "youtube"


def test_youtube_mobile():
    assert detect_platform("https://m.youtube.com/watch?v=abc123") == "youtube"


def test_instagram_reel():
    assert detect_platform("https://www.instagram.com/reel/ABC123/") == "instagram"


def test_instagram_post():
    assert detect_platform("https://www.instagram.com/p/ABC123/") == "instagram"


def test_unknown():
    assert detect_platform("https://tiktok.com/@user/video/123") == "unknown"
