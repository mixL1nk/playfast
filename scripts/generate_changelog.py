#!/usr/bin/env python
"""Generate CHANGELOG using git-cliff."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

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
    changelog_path = Path("CHANGELOG.md")
    changelog_path.write_text(result.stdout, encoding="utf-8")

    # Copy to docs folder
    docs_path = Path("docs/changelog.md")
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(changelog_path, docs_path)

    print(f"Generated CHANGELOG.md and docs/changelog.md for v{version}")
