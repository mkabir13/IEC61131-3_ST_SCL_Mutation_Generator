"""Run from tools/: python3 run_dashboard.py
(or just use ./start.sh, which handles the venv and this for you)

Binds to 127.0.0.1 by default. To make it reachable from other machines
on your network (e.g. at your LAN IP), set DASHBOARD_HOST=0.0.0.0:

    DASHBOARD_HOST=0.0.0.0 python3 run_dashboard.py
"""

import os
from dashboard.app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.environ.get("DASHBOARD_PORT", "5050"))
    debug = os.environ.get("DASHBOARD_DEBUG", "1") == "1"
    print(f" * ST Mutation Dashboard starting on http://{host}:{port}")
    # threaded=True: Compile and Run now runs in a background thread (see
    # dashboard/job_runner.py) so the Stop button and page auto-refresh
    # can be served WHILE it's running, instead of the whole dev server
    # blocking on that one request.
    app.run(host=host, port=port, debug=debug, threaded=True)
