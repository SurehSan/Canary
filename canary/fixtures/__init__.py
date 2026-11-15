"""Seeded demo data: source catalog and offline source records.

Demo scenario: PHP2Shell (CVE-2026-109618, CVE-2026-109619). Source records point at REAL public pages.
Titles, URLs, and dates are preserved exactly; excerpts are short paraphrases written for this demo, not
copies. Everything about Fernwood Labs and Prairie Valley Medical Center is fictional.

Sources checked 2026-11-14:
- php.net 2026 news archive: security releases 8.5.12 / 8.4.27 / 8.3.36 / 8.2.35 on 21 Oct 2026.
- php/php-src GitHub security advisories GHSA-w8hw-w9fx-j79w and GHSA-6wmf-4rv5-p3rp.
- The Hacker News, 21 Oct 2026 (Swati Khandelwal): exploit *attempts* reported by Cloudflare and watchTowr;
  no confirmed break-in reported at the time.
- Check Point, 12 Nov 2026 (Lotem Finkelstein): confirmed in-the-wild exploitation, 30 Oct - 4 Nov 2026.
"""

# CAN-REQ-003: fixed starter catalog (global), collected in this order. Tier: A primary/standards,
# B reputable press or secondary research, C vendor blog.
SOURCE_CATALOG = [
    {"key": "php-net", "name": "PHP security announcements", "type": "Atom feed",
     "url": "https://www.php.net/feed.atom", "tier": "A",
     "topics": "PHP releases and security advisories", "method": "Public Atom feed"},
    {"key": "thehackernews", "name": "The Hacker News", "type": "RSS",
     "url": "https://feeds.feedburner.com/TheHackersNews", "tier": "B",
     "topics": "Security news, AI threats", "method": "Public RSS feed"},
    {"key": "csa", "name": "CSA research notes", "type": "Public web",
     "url": "https://labs.cloudsecurityalliance.org/", "tier": "B",
     "topics": "AI safety and cloud security research", "method": "Public research index"},
    {"key": "ghsa", "name": "GitHub Security Advisories", "type": "API",
     "url": "https://api.github.com/advisories", "tier": "A",
     "topics": "Software and package advisories", "method": "Documented public REST API (unauthenticated, rate-limited)"},
    {"key": "owasp-genai", "name": "OWASP GenAI Security Project", "type": "Public web",
     "url": "https://genai.owasp.org/", "tier": "A",
     "topics": "OWASP Top 10 for LLM Applications", "method": "Public project pages"},
]

PHP_NET_URL = "https://www.php.net/archive/2026.php#2026-10-21-5"
THN_URL = "https://thehackernews.com/2026/10/php-issues-emergency-patches-for-two.html"
GHSA_OOM_URL = "https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w"
GHSA_STATE_URL = "https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp"
CHECK_POINT_URL = ("https://blog.checkpoint.com/security/"
                   "security-advisory-active-exploitation-of-php2shell-and-local-privilege-escalation/")

# Offline fixture records returned by the demo collector (no network needed).
SOURCE_ITEMS = [
    {"source_key": "php-net", "url": PHP_NET_URL,
     "title": "Critical remote code execution vulnerabilities, update now",
     "published_at": "2026-10-21",
     "excerpt": "PHP 8.5.12, 8.4.27, 8.3.36 and 8.2.35 fix two critical vulnerabilities (CVE-2026-109618, "
                "CVE-2026-109619) that can allow unauthenticated remote code execution. No complete "
                "mitigations exist; PHP 8.1 and older no longer receive updates from the PHP project.",
     "source_note": None},
    {"source_key": "thehackernews", "url": THN_URL,
     "title": "PHP Issues Emergency Patches for Two Critical PHP2Shell RCE Flaws as Exploit Attempts Emerge",
     "published_at": "2026-10-21",
     "excerpt": "News report on the PHP2Shell security release. Cloudflare and watchTowr reported exploitation "
                "attempts; no confirmed break-in of a specific server had been reported at publication.",
     "source_note": "News coverage; exploitation claims are attributed to third parties."},
    {"source_key": "ghsa", "url": GHSA_OOM_URL,
     "title": "RCE via OOM corruption (CVE-2026-109618)",
     "published_at": "2026-10-21",
     "excerpt": "Out-of-memory handling can interrupt PHP while internal request data is only partially "
                "initialized; request cleanup may then treat the invalid data as valid.",
     "source_note": None},
    {"source_key": "ghsa", "url": GHSA_STATE_URL,
     "title": "RCE via stale global state (CVE-2026-109619)",
     "published_at": "2026-10-21",
     "excerpt": "Request-owned internal state can survive after its memory is freed, and a later request on "
                "the same worker may use it before normal initialization resets it.",
     "source_note": None},
]

# Follow-up evidence introduced later in the walkthrough (CAN-REQ-005 update -> P1 escalation).
FOLLOWUP_ITEMS = [
    {"source_key": "followup", "url": CHECK_POINT_URL, "tier": "B",
     "label": "Additional evidence (follow-up report)",
     "title": "Security Advisory: Active Exploitation of PHP2Shell and Local Privilege Escalation",
     "published_at": "2026-11-12",
     "excerpt": "Check Point Research reports active in-the-wild exploitation of PHP2Shell (CVE-2026-109618, "
                "CVE-2026-109619) between October 30 and November 4, 2026, used for initial access to "
                "internet-facing gateways.",
     "source_note": "Vendor security advisory describing attacks it observed against its own customers' systems."},
]
