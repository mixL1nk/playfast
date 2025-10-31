"""Finalize release by amending changelog and running formatters."""

import os
import subprocess
import sys


def run_command(
    cmd: list[str], check: bool = True, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    cmd_env = os.environ.copy()
    if env:
        cmd_env.update(env)
    return subprocess.run(cmd, check=check, capture_output=True, text=True, env=cmd_env)


def has_changes() -> bool:
    """Check if there are any uncommitted changes."""
    result = run_command(["git", "status", "--porcelain"], check=False)
    return bool(result.stdout.strip())


def main() -> None:
    """Finalize the release commit."""
    print("\n=== Finalizing Release ===\n")

    # Prepare environment to skip uv-lock hook
    env = {"SKIP": "uv-lock"}

    # Stage changelog files
    print("1. Staging changelog files...")
    run_command(["git", "add", "CHANGELOG.md", "docs/changelog.md"])

    # First amend without verification to include changelogs
    print("2. Amending commit with changelogs...")
    run_command(["git", "commit", "--amend", "--no-edit", "--no-verify"], env=env)

    # Run formatters (mdformat, etc.) - allow failure
    print("3. Running formatters on changelogs...")
    result = run_command(
        [
            "pre-commit",
            "run",
            "mdformat",
            "--files",
            "CHANGELOG.md",
            "docs/changelog.md",
        ],
        check=False,
        env=env,
    )
    if result.returncode != 0:
        print("   Formatters modified files")

    # Check if formatters made changes
    if has_changes():
        print("4. Formatters modified files, amending again...")
        run_command(["git", "add", "CHANGELOG.md", "docs/changelog.md"])
        run_command(["git", "commit", "--amend", "--no-edit", "--no-verify"], env=env)
        print("   OK: Changes incorporated into release commit")
    else:
        print("4. No additional changes needed")

    # Get final commit info
    result = run_command(["git", "log", "-1", "--oneline"])
    print(f"\nOK: Release finalized: {result.stdout.strip()}")

    # Check if previous commit has a tag (semantic-release creates it on previous commit)
    result = run_command(
        ["git", "describe", "--tags", "--exact-match", "HEAD~1"], check=False
    )
    if result.returncode == 0:
        old_tag = result.stdout.strip()
        print(f"\n5. Found tag '{old_tag}' on previous commit, moving to HEAD...")
        # Delete old tag
        run_command(["git", "tag", "-d", old_tag])
        # Create tag on current commit
        run_command(["git", "tag", old_tag])
        print(f"   OK: Tag '{old_tag}' moved to current commit")

        # Get final commit info
        result = run_command(["git", "log", "-1", "--oneline"])
        print(f"\nOK: Release finalized: {result.stdout.strip()}")
        print(f"OK: Tag: {old_tag}")
        print("\nNext steps:")
        print("  git push origin main")
        print(f"  git push origin {old_tag} --force")
    else:
        # Check if current commit has a tag
        result = run_command(
            ["git", "describe", "--tags", "--exact-match"], check=False
        )
        if result.returncode == 0:
            tag = result.stdout.strip()
            print(f"\nOK: Tag already on HEAD: {tag}")
            print("\nNext steps:")
            print("  git push origin main")
            print(f"  git push origin {tag} --force")
        else:
            print("\nWARNING: No tag found")
            print("This is unexpected - semantic-release should have created a tag")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        if e.stdout:
            print(f"stdout: {e.stdout}", file=sys.stderr)
        if e.stderr:
            print(f"stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
