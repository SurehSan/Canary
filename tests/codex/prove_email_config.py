"""Prove both helper subprocess environments neutralize personal .env SMTP values."""
import os
import subprocess
import sys


CHILD = (
    "import run; run.load_dotenv(); from canary import create_app; "
    "a = create_app({'START_SCHEDULER': False, 'DATABASE': ':memory:'}); "
    "print(a.config['SMTP_HOST'], bool(a.config['SMTP_PASSWORD']), a.config['EMAIL_ALLOWLIST'])"
)


def probe(overrides, expected):
    env = {k: v for k, v in os.environ.items() if not k.startswith("CANARY_")}
    env.update({"CANARY_DATABASE": ":memory:", "CANARY_SCHEDULER": "0", "CANARY_LIVE_SOURCES": "0",
                "CANARY_SMTP_USERNAME": "", "CANARY_SMTP_PASSWORD": "", "CANARY_SMTP_STARTTLS": "0",
                "CANARY_SMTP_SSL": "0"})
    env.update(overrides)
    result = subprocess.run([sys.executable, "-c", CHILD], env=env, capture_output=True, text=True, check=True)
    line = result.stdout.strip().splitlines()[-1]
    assert line == expected, (line, expected, result.stderr)
    return line


no_smtp = probe({"CANARY_SMTP_HOST": "", "CANARY_SMTP_PORT": "", "CANARY_MAIL_FROM": "",
                 "CANARY_EMAIL_ALLOWLIST": "", "CANARY_TEST_RECIPIENTS": ""}, "None False set()")
capture = probe({"CANARY_SMTP_HOST": "127.0.0.1", "CANARY_SMTP_PORT": "2525",
                 "CANARY_MAIL_FROM": "canary-demo@team.example",
                 "CANARY_EMAIL_ALLOWLIST": "sureh-test@team.example",
                 "CANARY_TEST_RECIPIENTS": "sureh=sureh-test@team.example"},
                "127.0.0.1 False {'sureh-test@team.example'}")
print("No-SMTP proof:", no_smtp)
print("Capture proof:", capture)
