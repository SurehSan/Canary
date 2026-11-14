"""Start the Canary local demo: python run.py  (then open http://127.0.0.1:5000)

Reset to seed state: python run.py --reset
"""
import os
import sys
from pathlib import Path


def load_dotenv(path=Path(__file__).with_name(".env")):
    """Read KEY=VALUE lines from a local, git-ignored .env. Existing environment variables win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main():
    load_dotenv()
    from canary import create_app
    if "--reset" in sys.argv:
        app = create_app({"START_SCHEDULER": False})
        with app.app_context():
            from canary.db import get_db
            from canary.seed import reset_demo
            reset_demo(get_db())
        print("Demo data reset to seed state.")
        return
    app = create_app()
    # Local only: bind to loopback, no reloader (it would start the scheduler twice).
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
