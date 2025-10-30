#!/usr/bin/env python3
"""
Batch APK Download Example

Shows different strategies for downloading multiple APKs efficiently.
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from playfast import ApkDownloader


def download_sequential(client: ApkDownloader, packages: list[str], output_dir: str):
    """
    Strategy 1: Sequential download (slowest, simplest)

    Downloads one APK at a time.
    Good for: Small number of APKs, debugging
    """
    print("=" * 60)
    print("Strategy 1: Sequential Download")
    print("=" * 60)

    results = []
    start_time = time.time()

    for i, package_id in enumerate(packages, 1):
        print(f"\n[{i}/{len(packages)}] Downloading {package_id}...")
        try:
            apk_path = client.download_apk(package_id, output_dir)
            results.append((package_id, apk_path, None))
            print(f"  ✅ Success: {apk_path}")
        except Exception as e:
            results.append((package_id, None, str(e)))
            print(f"  ❌ Failed: {e}")

    elapsed = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed:.2f}s")
    return results


def download_parallel_threads(
    client: ApkDownloader,
    packages: list[str],
    output_dir: str,
    max_workers: int = 5
):
    """
    Strategy 2: Parallel download with ThreadPoolExecutor (recommended)

    Downloads multiple APKs concurrently using threads.
    Good for: Most use cases, balance of speed and resource usage

    Note: Each thread creates its own tokio runtime, but Rust releases
    the GIL during actual download, so threads can run truly in parallel.
    """
    print("=" * 60)
    print(f"Strategy 2: Parallel Download ({max_workers} workers)")
    print("=" * 60)

    def download_one(package_id: str):
        try:
            apk_path = client.download_apk(package_id, output_dir)
            return (package_id, apk_path, None)
        except Exception as e:
            return (package_id, None, str(e))

    results = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(download_one, pkg): pkg
            for pkg in packages
        }

        # Process as they complete
        for i, future in enumerate(as_completed(futures), 1):
            package_id = futures[future]
            result = future.result()
            results.append(result)

            if result[2] is None:  # No error
                print(f"[{i}/{len(packages)}] ✅ {package_id}")
            else:
                print(f"[{i}/{len(packages)}] ❌ {package_id}: {result[2]}")

    elapsed = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed:.2f}s")
    print(f"📊 Speedup: {len(packages) / elapsed:.2f}x downloads/second")
    return results


def download_with_retry(
    client: ApkDownloader,
    packages: list[str],
    output_dir: str,
    max_workers: int = 5,
    max_retries: int = 3
):
    """
    Strategy 3: Parallel download with retry logic

    Same as Strategy 2 but retries failed downloads.
    Good for: Production use, unreliable network
    """
    print("=" * 60)
    print(f"Strategy 3: Parallel with Retry ({max_workers} workers, {max_retries} retries)")
    print("=" * 60)

    def download_with_retry_inner(package_id: str):
        last_error = None
        for attempt in range(max_retries):
            try:
                apk_path = client.download_apk(package_id, output_dir)
                if attempt > 0:
                    print(f"  ✅ {package_id} succeeded on retry {attempt + 1}")
                return (package_id, apk_path, None)
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    print(f"  ⚠️  {package_id} failed (attempt {attempt + 1}), retrying...")
                    time.sleep(1)  # Brief delay before retry

        return (package_id, None, f"Failed after {max_retries} attempts: {last_error}")

    results = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(download_with_retry_inner, pkg): pkg
            for pkg in packages
        }

        for i, future in enumerate(as_completed(futures), 1):
            package_id = futures[future]
            result = future.result()
            results.append(result)

            if result[2] is None:
                print(f"[{i}/{len(packages)}] ✅ {package_id}")
            else:
                print(f"[{i}/{len(packages)}] ❌ {package_id}: {result[2]}")

    elapsed = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed:.2f}s")
    return results


def print_summary(results: list[tuple[str, str, str]]):
    """Print download summary"""
    print("\n" + "=" * 60)
    print("Download Summary")
    print("=" * 60)

    success = [r for r in results if r[2] is None]
    failed = [r for r in results if r[2] is not None]

    print(f"✅ Successful: {len(success)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")

    if failed:
        print("\nFailed packages:")
        for package_id, _, error in failed:
            print(f"  - {package_id}: {error}")


def main():
    """Demo all download strategies"""

    # Example package list (10 popular apps)
    packages = [
        "com.instagram.android",
        "com.spotify.music",
        "com.whatsapp",
        "com.facebook.katana",
        "com.twitter.android",
        "com.snapchat.android",
        "com.netflix.mediaclient",
        "com.amazon.mShop.android.shopping",
        "com.ubercab",
        "com.airbnb.android",
    ]

    credentials_path = os.path.expanduser("~/.playfast/credentials.json")
    output_dir = "/tmp/playfast_batch_download"

    # Check credentials exist
    if not Path(credentials_path).exists():
        print(f"❌ Credentials not found: {credentials_path}")
        print("\n💡 Run auth_setup.py first to set up authentication")
        return

    print("Loading credentials...")
    client = ApkDownloader.from_credentials(credentials_path)
    print(f"✅ Logged in as: {client.email}\n")

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Choose strategy
    print("Choose download strategy:")
    print("  1. Sequential (slowest, for debugging)")
    print("  2. Parallel with 5 workers (recommended)")
    print("  3. Parallel with 10 workers (faster, more resource intensive)")
    print("  4. Parallel with retry logic (production)")
    print()

    choice = input("Enter choice (1-4) [default: 2]: ").strip() or "2"

    if choice == "1":
        results = download_sequential(client, packages, output_dir)
    elif choice == "2":
        results = download_parallel_threads(client, packages, output_dir, max_workers=5)
    elif choice == "3":
        results = download_parallel_threads(client, packages, output_dir, max_workers=10)
    elif choice == "4":
        results = download_with_retry(client, packages, output_dir, max_workers=5, max_retries=3)
    else:
        print("Invalid choice")
        return

    print_summary(results)
    print(f"\n📁 APKs saved to: {output_dir}")


if __name__ == "__main__":
    main()
