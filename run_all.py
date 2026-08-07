"""
Build the React frontend (first run only) and launch the FastAPI backend,
which serves BOTH the JSON API and the built dashboard on a single port.

    python run_all.py

Then open http://localhost:8000 — no separate dashboard process/port needed.

Requires Node.js/npm to be installed for the one-time frontend build. If
it's missing, this prints install instructions instead of crashing.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
IS_WINDOWS = os.name == "nt"


def ensure_frontend_built():
    if DIST.exists() and any(DIST.iterdir()):
        print("Frontend already built (frontend/dist exists) — skipping build.")
        print("(Delete the frontend/dist folder to force a rebuild.)")
        return

    npm = shutil.which("npm")
    if npm is None:
        print(
            "\nERROR: npm was not found on your PATH.\n"
            "The React dashboard needs Node.js/npm to build (one-time only).\n"
            "  1. Install Node.js LTS from https://nodejs.org\n"
            "  2. Close and reopen your terminal\n"
            "  3. Run `python run_all.py` again\n"
        )
        sys.exit(1)

    print("Building frontend (first run only, this can take a minute)...")
    # shell=True on Windows avoids a common WinError 193 when subprocess
    # tries to exec npm.cmd directly.
    subprocess.run([npm, "install"], cwd=str(FRONTEND), check=True, shell=IS_WINDOWS)
    subprocess.run([npm, "run", "build"], cwd=str(FRONTEND), check=True, shell=IS_WINDOWS)
    print("Frontend build complete.\n")


def main():
    ensure_frontend_built()
    print("Starting AI Traffic Signal Controller at http://localhost:8000")
    print("Press Ctrl+C to stop.")
    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=str(ROOT),
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
