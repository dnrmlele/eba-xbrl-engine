"""CLI wrapper for Streamlit app."""

import os
import subprocess
import sys


def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    app_path = os.path.join(root, "app.py")
    if not os.path.exists(app_path):
        raise FileNotFoundError(f"app.py not found at {app_path}")

    cmd = ["streamlit", "run", app_path] + sys.argv[1:]
    return subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
