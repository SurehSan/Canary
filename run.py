"""Start the Canary local demo: python run.py  (then open http://127.0.0.1:5000)

Reset to seed state: python run.py --reset
"""
import sys

from canary import create_app


def main():
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
