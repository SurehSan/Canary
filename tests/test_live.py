"""CAN-REQ-003/004: optional live RSS adapter for The Hacker News (offline fixtures stay the default)."""
import pytest

from canary import create_app
from canary.db import get_db
from canary.live import is_ai_relevant, parse_rss
from tests.conftest import login, org_id, refresh

SAMPLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>The Hacker News</title>
<item><title>Rogue MCP Server Lets Attackers Hijack AI Coding Agents</title>
  <link>https://thehackernews.com/2026/11/rogue-mcp-server.html?utm_source=rss</link>
  <pubDate>Thu, 12 Nov 2026 18:30:00 +0530</pubDate>
  <description><![CDATA[<p>Researchers show a <b>malicious</b> MCP server can steer LLM agents.</p>]]></description></item>
<item><title>Ransomware Gang Hits Regional Bank</title>
  <link>https://thehackernews.com/2026/11/ransomware-bank.html</link>
  <pubDate>Wed, 11 Nov 2026 09:00:00 +0000</pubDate>
  <description>Financial sector incident.</description></item>
</channel></rss>"""


def test_parse_rss_extracts_url_title_date_and_short_plain_excerpt():
    items = parse_rss(SAMPLE)
    first = items[0]
    assert first["title"] == "Rogue MCP Server Lets Attackers Hijack AI Coding Agents"
    assert first["url"].startswith("https://thehackernews.com/2026/11/rogue-mcp-server.html")
    assert first["published_at"] == "2026-11-12"
    assert first["excerpt"] == "Researchers show a malicious MCP server can steer LLM agents."
    assert len(parse_rss(SAMPLE)) == 2


def test_only_ai_relevant_items_are_kept():
    titles = [i["title"] for i in parse_rss(SAMPLE) if is_ai_relevant(i["title"], i["excerpt"])]
    assert titles == ["Rogue MCP Server Lets Attackers Hijack AI Coding Agents"]


def live_app(tmp_path, http_get):
    return create_app({
        "TESTING": True, "SECRET_KEY": "t", "DATABASE": str(tmp_path / "l.sqlite"),
        "FIXED_NOW": "2026-11-14T15:00:00+00:00", "RETRY_SLEEP_SECONDS": 0, "START_SCHEDULER": False,
        "SMTP_HOST": None, "EMAIL_ALLOWLIST": set(), "TEST_RECIPIENTS": {},
        "LIVE_SOURCES": True, "HTTP_GET": http_get,
    })


def runs_for(db, key):
    return db.execute("SELECT r.* FROM collection_runs r JOIN source_catalog c ON c.id=r.source_id"
                      " WHERE c.key=? ORDER BY r.id", (key,)).fetchall()


def test_live_mode_runs_live_feed_alongside_offline_fixtures(tmp_path):
    calls = []
    app = live_app(tmp_path, lambda url: calls.append(url) or SAMPLE)
    client = app.test_client()
    with app.app_context():
        db = get_db()
        login(client, "wyatt", org=org_id(db, "Fernwood Labs"))
        refresh(client)
        adapters = {r["adapter"]: r for r in runs_for(db, "thehackernews")}
        assert set(adapters) == {"Offline fixture adapter (demo)", "Live RSS"}
        assert adapters["Live RSS"]["outcome"] == "success" and adapters["Live RSS"]["new_items"] == 1
        assert calls == ["https://feeds.feedburner.com/TheHackersNews"]
        item = db.execute("SELECT * FROM source_items WHERE title LIKE 'Rogue MCP%'").fetchone()
        assert item["published_at"] == "2026-11-12" and "utm_source" not in item["canonical_url"]
        assert db.execute("SELECT COUNT(*) FROM source_items WHERE title LIKE 'Ransomware%'").fetchone()[0] == 0
        # Seeded walkthrough still works: the HalluSquatting alert exists.
        assert db.execute("SELECT COUNT(*) FROM alerts").fetchone()[0] == 1
        assert "Live RSS" in client.get("/sources").data.decode()


def test_live_fetch_failure_is_recorded_after_three_attempts(tmp_path):
    def boom(url):
        raise OSError("network unreachable")
    app = live_app(tmp_path, boom)
    client = app.test_client()
    with app.app_context():
        db = get_db()
        login(client, "wyatt", org=org_id(db, "Fernwood Labs"))
        refresh(client)
        live = [r for r in runs_for(db, "thehackernews") if r["adapter"] == "Live RSS"][0]
        assert live["outcome"] == "failed" and live["attempts"] == 3 and "network unreachable" in live["error"]
        fixture = [r for r in runs_for(db, "thehackernews") if r["adapter"] != "Live RSS"][0]
        assert fixture["outcome"] == "success"


def test_live_fetch_respects_minimum_interval(tmp_path):
    calls = []
    app = live_app(tmp_path, lambda url: calls.append(url) or SAMPLE)
    client = app.test_client()
    with app.app_context():
        db = get_db()
        login(client, "wyatt", org=org_id(db, "Fernwood Labs"))
        refresh(client)
        refresh(client)
        live = [r for r in runs_for(db, "thehackernews") if r["adapter"] == "Live RSS"]
        assert [r["outcome"] for r in live] == ["success", "skipped"]
        assert len(calls) == 1


def test_live_sources_off_by_default_never_touch_network(client, db, app):
    app.config["HTTP_GET"] = lambda url: pytest.fail("network must not be used when live sources are off")
    login(client, "wyatt", org=org_id(db, "Fernwood Labs"))
    refresh(client)
    assert all(r["adapter"] != "Live RSS" for r in runs_for(db, "thehackernews"))
