"""CDX-4: WCAG 2.1 contrast for key text/background pairs, computed from the CSS tokens (light and dark)."""
import re
from pathlib import Path

import pytest

CSS = (Path(__file__).resolve().parent.parent / "canary" / "static" / "canary.css").read_text(encoding="utf-8")


def _block(text):
    start = text.index("{") + 1
    depth, i = 1, start
    while depth:
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        i += 1
    return text[start:i - 1]


def tokens(mode):
    light = dict(re.findall(r"(--[\w-]+):\s*([^;]+);", _block(CSS[CSS.index(":root"):])))
    if mode == "light":
        return light
    media = CSS[CSS.index("@media (prefers-color-scheme: dark)"):]
    dark_root = _block(_block(media)[_block(media).index(":root"):])
    return {**light, **dict(re.findall(r"(--[\w-]+):\s*([^;]+);", dark_root))}


def color(value, toks):
    value = value.strip()
    while value.startswith("var("):
        value = toks[value[4:-1].strip()].strip()
    return value


def luminance(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


BADGE_TEXT = {"light": "#ffffff", "dark": "#081428"}  # .prio color in each mode
PAIRS = [("--text", "--bg"), ("--text", "--surface"), ("--muted", "--bg"), ("--muted", "--surface"),
         ("--link", "--bg"), ("--link", "--surface"), ("--heading", "--bg"), ("--navy", "--canary"),
         ("--navy", "--canary-deep"), ("--topbar-text", "--topbar"), ("--topbar-muted", "--topbar")]


@pytest.mark.parametrize("mode", ["light", "dark"])
@pytest.mark.parametrize("fg,bg", PAIRS)
def test_text_pairs_meet_aa(mode, fg, bg):
    t = tokens(mode)
    r = ratio(color(t[fg], t), color(t[bg], t))
    assert r >= 4.5, f"{mode}: {fg} on {bg} = {r:.2f}:1"


@pytest.mark.parametrize("mode", ["light", "dark"])
@pytest.mark.parametrize("prio", ["--p1", "--p2", "--p3", "--p4"])
def test_priority_badges_meet_aa(mode, prio):
    t = tokens(mode)
    r = ratio(BADGE_TEXT[mode], color(t[prio], t))
    assert r >= 4.5, f"{mode}: badge text on {prio} = {r:.2f}:1"
