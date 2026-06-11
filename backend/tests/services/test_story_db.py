from datetime import datetime, timedelta, timezone

from app.models.article import Article
from app.services.story_clusterer import get_stories, get_story_detail


def _article(id, title, source_id="reddit-ml", read=False, hours_ago=1):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return Article(
        id=id,
        title=title,
        url=f"https://example.com/{id}",
        source_id=source_id,
        summary=None,
        published_at=now - timedelta(hours=hours_ago),
        fetched_at=now,
        topic_tags=["llm"],
        is_read=read,
        is_bookmarked=False,
        trending_score=1.0,
    )


class TestGetStories:
    async def test_bounded_digest_with_caught_up_flag(self, db):
        db.add_all([
            _article("s1", "Frobnicator 9000 announced today"),
            _article("s2", "Frobnicator 9000 announced — discussion"),
            _article("s3", "Unrelated robotics paper grault"),
        ])
        await db.commit()

        digest = await get_stories(db, days=2, limit=50)
        assert len(digest["stories"]) <= 50
        assert digest["caught_up"] == (digest["total_stories"] <= 50)
        # The two Frobnicator items must have merged into one story
        frob = [s for s in digest["stories"] if "Frobnicator" in s["headline"]]
        assert len(frob) == 1
        assert frob[0]["article_count"] == 2

    async def test_unread_only_filters_read(self, db):
        db.add(_article("s4", "A fully read story xyzzy", read=True))
        await db.commit()
        digest = await get_stories(db, days=2, unread_only=True)
        assert all("xyzzy" not in s["headline"] for s in digest["stories"])

    async def test_topic_filter(self, db):
        db.add(_article("s5", "Topic filter target plugh"))
        await db.commit()
        digest = await get_stories(db, days=2, topic="computer-vision")
        assert all("plugh" not in s["headline"] for s in digest["stories"])


class TestGetStoryDetail:
    async def test_groups_by_source_category(self, db):
        db.add_all([
            _article("d1", "Llama 6 leaked", source_id="reddit-ml"),
            _article("d2", "Llama 6 leaked report", source_id="rss-techcrunch-ai"),
        ])
        await db.commit()
        detail = await get_story_detail(db, ["d1", "d2"])
        assert set(detail["groups"]) == {"social", "funding"}

    async def test_empty_ids(self, db):
        assert (await get_story_detail(db, []))["groups"] == {}
