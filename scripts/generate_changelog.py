#!/usr/bin/env python
"""Generate CHANGELOG using git-cliff."""

import os
import subprocess
import sys

if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "unreleased"

    # Set UTF-8 encoding for subprocess
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    # Run git-cliff via uv and capture output
    result = subprocess.run(
        ["uv", "run", "git-cliff", "--tag", f"v{version}"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True,
        env=env,
    )

    # Write to CHANGELOG.md
    with open("CHANGELOG.md", "w", encoding="utf-8") as f:
        f.write(result.stdout)

    print(f"Generated CHANGELOG.md for v{version}")
