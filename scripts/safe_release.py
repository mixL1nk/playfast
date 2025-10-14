"""Safe release workflow with conflict prevention."""

from pathlib import Path
import subprocess
import sys


def run(
    cmd: list[str],
    check: bool = True,
    cwd: Path | None = None,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run command and return result."""
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(
        cmd, check=check, capture_output=capture_output, text=True, cwd=cwd
    )


def run_interactive(
    cmd: list[str], check: bool = True, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run command with live output (no capture)."""
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check, text=True, cwd=cwd)
    return result


def main() -> None:
    """Execute safe release workflow."""
    print("\n=== Safe Release Workflow ===\n")

    # 0. Check we're in the right directory
    if not Path("pyproject.toml").exists():
        print("ERROR: Run this from project root!")
        sys.exit(1)

    # 1. Check clean working tree
    result = run(["git", "status", "--porcelain"], check=False)
    if result.stdout.strip():
        print("ERROR: Working tree is not clean!")
        print("Commit or stash changes first.")
        print(result.stdout)
        sys.exit(1)
    print("OK: Working tree is clean\n")

    # 2. Sync with remote
    print("Step 1: Syncing with remote...")
    run(["git", "fetch", "origin", "--tags"])

    # Check if behind
    local = run(["git", "rev-parse", "@"]).stdout.strip()
    try:
        remote = run(["git", "rev-parse", "@{u}"]).stdout.strip()
    except subprocess.CalledProcessError:
        print("WARNING: No upstream branch set")
        remote = local

    if local != remote:
        print("ERROR: Local branch is not in sync with remote!")
        print("Run: git pull --tags origin main")
        sys.exit(1)

    print("   OK: In sync with remote\n")

    # 3. Check for existing unreleased commits
    result = run(["git", "describe", "--tags", "--abbrev=0"], check=False)
    if result.returncode == 0:
        last_tag = result.stdout.strip()
        print(f"Step 2: Checking commits since {last_tag}")

        # Count commits since last tag
        result = run(["git", "rev-list", f"{last_tag}..HEAD", "--count"])
        commit_count = int(result.stdout.strip())

        if commit_count == 0:
            print("   No new commits since last release")
            print("   Nothing to release!")
            sys.exit(0)

        print(f"   {commit_count} new commit(s) to release\n")
    else:
        print("Step 2: No previous tags found (first release)\n")

    # 4. Preview next version
    print("Step 3: Calculating next version...")
    result = run(["semantic-release", "version", "--print"], check=False)
    if result.returncode != 0:
        print("ERROR: Failed to calculate next version")
        print(result.stderr)
        sys.exit(1)

    next_version = result.stdout.strip()
    print(f"   Next version: {next_version}\n")

    # 5. Confirm
    response = input(f"Create release {next_version}? [y/N]: ")
    if response.lower() != "y":
        print("Release cancelled")
        sys.exit(0)

    # 6. Create release (local only)
    print("\nStep 4: Creating release (local only)...")
    try:
        # Run the existing release command
        result = run(["poe", "release"])
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Release failed: {e}")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)

    # 7. Show what was created
    print("\nStep 5: Release created successfully!\n")
    result = run(["git", "log", "-1", "--oneline"])
    release_commit = result.stdout.strip()
    print(f"   Commit: {release_commit}")

    # 7.1. Check if tag was created
    result = run(["git", "describe", "--tags", "--exact-match"], check=False)
    created_tag = None
    if result.returncode == 0:
        created_tag = result.stdout.strip()
        print(f"   Tag: {created_tag}")
    else:
        # Tag not on HEAD, check if it's on previous commit
        result = run(
            ["git", "describe", "--tags", "--exact-match", "HEAD~1"], check=False
        )
        if result.returncode == 0:
            old_tag = result.stdout.strip()
            print(f"   WARNING: Tag '{old_tag}' is on previous commit, moving it...")
            # Move tag to current commit
            run(["git", "tag", "-d", old_tag])
            run(["git", "tag", old_tag])
            created_tag = old_tag
            print(f"   OK: Tag '{old_tag}' moved to current commit")
        else:
            print("   WARNING: No tag found")
            print("   This may happen if semantic-release failed")
            response = input("   Continue anyway? [y/N]: ")
            if response.lower() != "y":
                print("\nRelease cancelled. Manual investigation needed.")
                sys.exit(1)

    # 8. Final confirmation before push
    print("\n" + "=" * 50)
    response = input("\nPush to remote? [y/N]: ")
    if response.lower() == "y":
        print("\nStep 6: Pushing to remote...")

        # Try to push, handle conflicts
        try:
            run_interactive(["git", "push", "origin", "main"], check=True)
            push_main_success = True
        except subprocess.CalledProcessError:
            print("\nWARNING: Push failed (likely due to remote changes)")
            print("Attempting to resolve...")

            # Fetch and check divergence
            run(["git", "fetch", "origin"])
            local = run(["git", "rev-parse", "main"]).stdout.strip()
            remote = run(["git", "rev-parse", "origin/main"]).stdout.strip()

            if local == remote:
                print("ERROR: Unknown push error (not a divergence issue)")
                sys.exit(1)

            # Pull with merge
            print("\nAttempting to merge with remote...")
            try:
                run_interactive(["git", "pull", "origin", "main"], check=True)
                print("OK: Merged successfully")

                # If we had a tag, move it to the new merge commit
                if created_tag:
                    print(f"Moving tag '{created_tag}' to merge commit...")
                    run(["git", "tag", "-d", created_tag])
                    run(["git", "tag", created_tag])
                    print(f"OK: Tag '{created_tag}' moved to merge commit")

                # Retry push
                print("\nRetrying push...")
                run_interactive(["git", "push", "origin", "main"], check=True)
                push_main_success = True
            except subprocess.CalledProcessError as e:
                print(f"\nERROR: Failed to resolve conflict: {e}")
                print("\nManual resolution needed:")
                print("  1. git pull --rebase origin main")
                print("  2. Resolve conflicts")
                print("  3. git push origin main")
                if created_tag:
                    print(f"  4. git push origin {created_tag}")
                sys.exit(1)

        # Push tags
        if push_main_success and created_tag:
            print("\nPushing tags...")
            try:
                run_interactive(["git", "push", "origin", created_tag], check=True)
                print(f"\nOK: Tag '{created_tag}' pushed successfully!")
            except subprocess.CalledProcessError:
                print(f"\nWARNING: Failed to push tag '{created_tag}'")
                print("You may need to force push:")
                print(f"  git push origin {created_tag} --force")

        print("\nOK: Release pushed successfully!")
        print("\nNext step: Wait for CI to pass, then run:")
        print("  uv run poe release_publish")
    else:
        print("\nRelease created locally. Push manually when ready:")
        print("  git push origin main")
        if created_tag:
            print(f"  git push origin {created_tag}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Command failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nRelease cancelled by user")
        sys.exit(1)
