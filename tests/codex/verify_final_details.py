"""Small independent checks for final-validation contrast and dotenv documentation."""
from pathlib import Path
import os
import sys
import tempfile

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))


def luminance(value):
    channels = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
    return sum(c * w for c, w in zip(linear, (.2126, .7152, .0722)))


def ratio(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + .05) / (lo + .05)


def contrast_report():
    modes = {
        "light": {"bg": "#fbf9ec", "surface": "#ffffff", "text": "#14213d", "muted": "#5d6578",
                  "link": "#1d4a8f", "navy": "#0a1a36", "canary": "#ffcc00", "amber": "#f2aa00",
                  "topbar": "#0a1a36", "nav_muted": "#b9c2d6", "nav_active": "#f6f2e2",
                  "badges": ["#c62828", "#d9480f", "#8f6b00", "#55657e"], "badge_text": "#ffffff"},
        "dark": {"bg": "#081428", "surface": "#0f2242", "text": "#eef0f5", "muted": "#a6b1c6",
                 "link": "#8fb8ff", "navy": "#0a1a36", "canary": "#ffcc00", "amber": "#f2aa00",
                 "topbar": "#050e1e", "nav_muted": "#8f9bb3", "nav_active": "#f6f2e2",
                 "badges": ["#ff6b61", "#ff9248", "#f2c94c", "#9db0c8"], "badge_text": "#081428"},
    }
    ok = True
    for mode, t in modes.items():
        pairs = [("body text/background", t["text"], t["bg"]), ("muted/background", t["muted"], t["bg"]),
                 ("muted/surface", t["muted"], t["surface"]), ("link/background", t["link"], t["bg"]),
                 ("link/surface", t["link"], t["surface"]), ("navy/canary banner + button", t["navy"], t["canary"]),
                 ("navy/amber button hover", t["navy"], t["amber"]), ("nav muted/topbar", t["nav_muted"], t["topbar"]),
                 ("nav active/topbar", t["nav_active"], t["topbar"])]
        pairs.extend((f"badge P{i}/text", t["badge_text"], color) for i, color in enumerate(t["badges"], 1))
        print(mode)
        for name, fg, bg in pairs:
            value = ratio(fg, bg)
            passed = value >= 4.5
            ok &= passed
            print(f"  {name}: {value:.2f}:1 {'PASS' if passed else 'FAIL'}")
    return ok


def dotenv_report():
    from run import load_dotenv
    keys = ("CANARY_MAIL_FROM", "CANARY_SMTP_HOST")
    old = {key: os.environ.pop(key, None) for key in keys}
    try:
        with tempfile.TemporaryDirectory(prefix="canary-dotenv-check-", dir=ROOT / "tests" / "codex") as scratch:
            sample = Path(scratch) / "sample.env"
            sample.write_text("CANARY_MAIL_FROM=\nCANARY_MAIL_FROM=second@example.test\nCANARY_SMTP_HOST=smtp.example.test # comment\n", encoding="utf-8")
            load_dotenv(sample)
            observed = {key: os.environ.get(key) for key in keys}
            expected = {"CANARY_MAIL_FROM": "", "CANARY_SMTP_HOST": "smtp.example.test # comment"}
            assert observed == expected, observed
            print(f"D2 PASS: first blank occurrence kept={observed['CANARY_MAIL_FROM']!r}; inline comment retained={observed['CANARY_SMTP_HOST']!r}")
    finally:
        for key in keys:
            os.environ.pop(key, None)
            if old[key] is not None:
                os.environ[key] = old[key]


if __name__ == "__main__":
    contrast_report()
    dotenv_report()
