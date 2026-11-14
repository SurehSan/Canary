"""Run HTTP acceptance checks for CDX-3, branding, and guide citations."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

import requests

ROOT = Path.cwd()
DB_PATH = ROOT / "instance" / "canary.sqlite"
BASE = "http://127.0.0.1:5000"
LOG = ROOT / "tests" / "codex" / "final-target-app.log"
SAFE_EMAIL = {
    "CANARY_SMTP_HOST": "", "CANARY_SMTP_PORT": "", "CANARY_SMTP_STARTTLS": "0",
    "CANARY_SMTP_SSL": "0", "CANARY_SMTP_USERNAME": "", "CANARY_SMTP_PASSWORD": "",
    "CANARY_MAIL_FROM": "", "CANARY_EMAIL_ALLOWLIST": "", "CANARY_TEST_RECIPIENTS": "",
    "CANARY_LIVE_SOURCES": "0", "CANARY_SCHEDULER": "0",
}
results = {}


def db():
    c = sqlite3.connect(DB_PATH, timeout=15)
    c.row_factory = sqlite3.Row
    return c


def scalar(sql, args=()):
    with db() as c:
        return c.execute(sql, args).fetchone()[0]


def rows(sql, args=()):
    with db() as c:
        return c.execute(sql, args).fetchall()


def req(session, method, path, data=None, status=302):
    r = session.request(method, BASE + path, data=data, allow_redirects=False, timeout=20)
    assert r.status_code == status, (method, path, r.status_code, r.text[:400])
    return r


def login(s, username, password="demo", org=None):
    req(s, "POST", "/logout") if s.cookies else None
    req(s, "POST", "/login", {"username": username, "password": password})
    if org is not None:
        req(s, "POST", "/orgs/select", {"org_id": org})


def create_org(s, username, orgname):
    req(s, "POST", "/register", {"username": username, "display_name": username.title(), "password": "pass1234"})
    req(s, "POST", "/orgs/create", {"name": orgname, "industry": "Manufacturing"})
    return scalar("SELECT id FROM organizations WHERE name=?", (orgname,))


INVENTORY = {"name": "Team coding agent", "category": "Coding assistant", "version": "",
             "criticality": "High", "capabilities": "ai_coding_agent, auto_install_packages"}


def main():
    env = {k: v for k, v in os.environ.items() if not k.startswith("CANARY_")}
    env.update(SAFE_EMAIL)
    subprocess.run([sys.executable, "run.py", "--reset"], cwd=ROOT, env=env, check=True,
                   capture_output=True, text=True)
    log = LOG.open("w", encoding="utf-8")
    proc = subprocess.Popen([sys.executable, "run.py"], cwd=ROOT, env=env, stdout=log,
                            stderr=subprocess.STDOUT)
    try:
        for _ in range(100):
            if proc.poll() is not None:
                raise RuntimeError(LOG.read_text(encoding="utf-8"))
            try:
                if requests.get(BASE + "/login", timeout=.5).status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(.1)
        else:
            raise RuntimeError("server did not start")

        w = requests.Session()
        fern = scalar("SELECT id FROM organizations WHERE name='Fernwood Labs'")
        prairie = scalar("SELECT id FROM organizations WHERE name='Prairie Valley Medical Center'")
        login(w, "wyatt", org=fern)
        req(w, "POST", "/sources/refresh")

        # A1/A2: inventory assessment is immediate and the new org can approve a plan.
        juniper = create_org(w, "final_dana", "Juniper Robotics")
        req(w, "POST", "/organization/inventory", INVENTORY)
        jun_alerts = rows("SELECT * FROM alerts WHERE org_id=?", (juniper,))
        rel = rows("SELECT match_state, priority FROM relevance WHERE org_id=?", (juniper,))
        assert len(jun_alerts) == 1 and rel and rel[0]["match_state"] == "possible", (len(jun_alerts), [dict(x) for x in rel])
        results["A1"] = f"PASS: inventory POST immediately produced {len(jun_alerts)} Possible alert without refresh."
        aid = jun_alerts[0]["id"]
        req(w, "POST", f"/alerts/{aid}/guide")
        gid = scalar("SELECT id FROM guides WHERE alert_id=?", (aid,))
        req(w, "POST", f"/guides/{gid}/plan")
        pid = scalar("SELECT id FROM plans WHERE guide_id=?", (gid,))
        req(w, "POST", f"/plans/{pid}/submit")
        req(w, "POST", f"/plans/{pid}/approve", {"confirm": "yes"})
        assert scalar("SELECT status FROM plans WHERE id=?", (pid,)) == "approved"
        results["A2"] = "PASS: guide -> plan -> submit -> approve ended in Approved as the new organization's Administrator."

        # C1: source labels in a guide created from the initial evidence.
        guide_html = w.get(BASE + f"/guides/{gid}", timeout=10).text
        assert all(x in guide_html for x in ("The Hacker News", "CSA research notes", "OWASP"))
        assert "Cited source" not in guide_html
        results["C1"] = "PASS: guide shows The Hacker News, CSA research notes, OWASP; no generic Cited source label."

        # A3: an org without inventory has no alerts and records no-match relevance.
        noinv = create_org(w, "final_lee", "No Inventory Works")
        noinv_rel = rows("SELECT match_state FROM relevance WHERE org_id=?", (noinv,))
        noinv_alerts = scalar("SELECT COUNT(*) FROM alerts WHERE org_id=?", (noinv,))
        assert noinv_rel and all(r["match_state"] == "no_match" for r in noinv_rel) and noinv_alerts == 0, ([dict(r) for r in noinv_rel], noinv_alerts)
        results["A3"] = f"PASS: {len(noinv_rel)} no_match relevance row(s), {noinv_alerts} alerts without inventory."

        # A4: disabling sources preserves known alerts; re-enabling CSA does not duplicate them.
        srcs = {r["key"]: r["id"] for r in rows("SELECT id,key FROM source_catalog")}
        for key in ("thehackernews", "csa"):
            req(w, "POST", f"/sources/{srcs[key]}/toggle")
        assert scalar("SELECT COUNT(*) FROM alerts WHERE org_id=?", (juniper,)) == 1
        req(w, "POST", f"/sources/{srcs['csa']}/toggle")
        assert scalar("SELECT COUNT(*) FROM alerts WHERE org_id=?", (juniper,)) == 1
        results["A4"] = "PASS: after THN/CSA disable and CSA re-enable, the existing finding/alert remained known and count stayed 1."

        # A5: cross-org read boundaries in both directions and seed org counts.
        fern_alert = scalar("SELECT id FROM alerts WHERE org_id=?", (fern,))
        assert scalar("SELECT COUNT(*) FROM alerts WHERE org_id=?", (fern,)) == 1
        assert scalar("SELECT COUNT(*) FROM alerts WHERE org_id=?", (prairie,)) == 0
        dana = requests.Session()
        login(dana, "final_dana", "pass1234", juniper)
        assert dana.get(BASE + f"/alerts/{aid}", timeout=10).status_code == 200
        assert dana.get(BASE + f"/alerts/{fern_alert}", timeout=10).status_code == 404
        login(w, "wyatt", org=fern)
        assert w.get(BASE + f"/alerts/{aid}", timeout=10).status_code == 404
        p = requests.Session()
        login(p, "priya", org=prairie)
        assert p.get(BASE + f"/alerts/{aid}", timeout=10).status_code == 404
        results["A5"] = "PASS: Fernwood=1 alert, Prairie=0; new alert accessible to its org and returned 404 for Wyatt/Priya."

        # A6: repeated refreshes do not duplicate alerts/relevance.
        login(w, "wyatt", org=fern)
        req(w, "POST", "/sources/refresh")
        req(w, "POST", "/sources/refresh")
        dup_alerts = rows("SELECT org_id,finding_id,COUNT(*) n FROM alerts GROUP BY org_id,finding_id HAVING COUNT(*)>1")
        dup_rel = rows("SELECT org_id,finding_id,COUNT(*) n FROM relevance GROUP BY org_id,finding_id HAVING COUNT(*)>1")
        assert not dup_alerts and not dup_rel
        results["A6"] = f"PASS: two refreshes; duplicate alert pairs={len(dup_alerts)}, duplicate relevance pairs={len(dup_rel)}."

        # B1: all six assets have image MIME type; five are <120 KB (512 logo exempt).
        assets = ("canary-logo-256.png", "canary-logo-512.png", "canary-mark-64.png", "favicon-32.png", "favicon.ico", "apple-touch-icon.png")
        asset_facts = []
        for name in assets:
            r = w.get(BASE + "/static/brand/" + name, timeout=10)
            assert r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image/"), (name, r.status_code, r.headers.get("Content-Type"))
            assert name == "canary-logo-512.png" or len(r.content) < 120_000, (name, len(r.content))
            asset_facts.append(f"{name}={len(r.content)}B/{r.headers['Content-Type']}")
        results["B1"] = "PASS: " + ", ".join(asset_facts)

        # B2: login/dashboard/alert route HTML accessibility markers.
        login_page = w.get(BASE + "/login", timeout=10).text
        assert 'rel="icon"' in login_page and 'brand/favicon-32.png' in login_page
        assert 'brand/canary-logo-256.png' in login_page and 'alt="Canary logo' in login_page
        dash = w.get(BASE + "/", timeout=10).text
        detail = w.get(BASE + f"/alerts/{fern_alert}", timeout=10).text
        for page in (dash, detail):
            assert 'rel="icon"' in page and 'brand/favicon-32.png' in page
            assert 'brand/canary-mark-64.png' in page and 'alt=""' in page
        results["B2"] = "PASS: favicon on /login, /, /alerts; login hero has descriptive alt; dashboard/alert header mark has empty decorative alt."

        # B3 is computed from literal CSS tokens separately by the caller.
        # C2: initial guide's source snapshot stays as-is; after follow-up a newly created guide cites it.
        req(w, "POST", "/sources/followup")
        second = create_org(w, "final_morgan", "Followup Evidence Co")
        req(w, "POST", "/organization/inventory", INVENTORY)
        second_alert = scalar("SELECT id FROM alerts WHERE org_id=?", (second,))
        req(w, "POST", f"/alerts/{second_alert}/guide")
        second_guide = scalar("SELECT id FROM guides WHERE alert_id=?", (second_alert,))
        fresh = w.get(BASE + f"/guides/{second_guide}", timeout=10).text
        assert "Additional evidence (demo follow-up)" in fresh and "The Hacker News" in fresh
        old = w.get(BASE + f"/guides/{gid}", timeout=10).text
        assert "Additional evidence (demo follow-up)" not in old
        results["C2"] = "PASS: guide created after follow-up cites Additional evidence (demo follow-up) and The Hacker News; earlier guide retained its stored labels."

        print(json.dumps(results, indent=2))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
        log.close()


if __name__ == "__main__":
    main()
