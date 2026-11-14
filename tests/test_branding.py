"""Canary logo and brand palette are used across the app (design/logo.png)."""
import re

from tests.conftest import login, org_id

ASSETS = ["brand/canary-logo-256.png", "brand/canary-mark-64.png", "brand/favicon-32.png", "brand/favicon.ico"]


def test_brand_assets_are_served_and_web_sized(client):
    for path in ASSETS:
        resp = client.get(f"/static/{path}")
        assert resp.status_code == 200, path
        assert len(resp.data) < 120_000, f"{path} is {len(resp.data)} bytes"
        resp.close()


def test_every_page_has_favicon_and_header_logo(client, db):
    for page in (client.get("/login").data.decode(),):
        assert 'rel="icon"' in page and "brand/favicon-32.png" in page
    login(client, "wyatt", org=org_id(db, "Fernwood Labs"))
    page = client.get("/").data.decode()
    assert re.search(r'<img[^>]+brand/canary-mark-64\.png[^>]+alt=""', page), "decorative header mark"
    assert ">Canary<" in page


def test_sign_in_page_shows_full_logo_with_alt_text(client):
    page = client.get("/login").data.decode()
    assert re.search(r'<img[^>]+brand/canary-logo-256\.png[^>]+alt="Canary logo', page)


def test_stylesheet_uses_logo_palette_in_light_and_dark(client):
    css = client.get("/static/canary.css").data.decode()
    for token in ("--canary:", "--canary-deep:", "--navy:", "--cream:"):
        assert token in css, token
    assert "#0a1a36" in css.lower() and "#ffcc00" in css.lower()
    assert "prefers-color-scheme: dark" in css
