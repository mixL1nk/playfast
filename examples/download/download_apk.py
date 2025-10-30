#!/usr/bin/env python3
"""
Download APK from Google Play Store

This example shows how to download APK files from Google Play Store using playfast.

Prerequisites:
- Set up authentication first using auth_setup.py
- Have valid credentials saved in ~/.playfast/credentials.json

Usage:
    # Download specific app
    python download_apk.py com.instagram.android

    # Download with custom output directory
    python download_apk.py com.spotify.music --output /tmp/apks

    # Download specific version
    python download_apk.py com.whatsapp --version-code 450814

    # Use custom credentials file
    python download_apk.py com.telegram --credentials ~/my-creds.json
"""

import sys
import os
import argparse
from pathlib import Path
from playfast import ApkDownloader


def download_apk(
    package_id: str,
    credentials_path: str,
    output_dir: str,
    version_code: int = None
):
    """
    Download APK file from Google Play Store.

    Args:
        package_id: Package ID to download (e.g., "com.instagram.android")
        credentials_path: Path to credentials JSON file
        output_dir: Directory to save downloaded APK
        version_code: Specific version code (optional, defaults to latest)
    """
    print("=" * 60)
    print(f"Downloading APK: {package_id}")
    print("=" * 60)
    print()

    # Load client from credentials
    print(f"📂 Loading credentials from: {credentials_path}")
    try:
        client = ApkDownloader.from_credentials(credentials_path)
        print(f"✅ Logged in as: {client.email}")
    except Exception as e:
        print(f"❌ Failed to load credentials: {e}")
        print()
        print("💡 Tip: Run auth_setup.py first to set up authentication")
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {output_path.absolute()}")
    print()

    # Get package details to show size before downloading
    try:
        print("📊 Fetching package details...")
        details_str = client.get_package_details(package_id)

        # Extract download size from details (if available)
        import re
        size_match = re.search(r'info_download_size:\s*Some\(\s*(\d+)', details_str)
        if size_match:
            size_bytes = int(size_match.group(1))
            size_mb = size_bytes / (1024 * 1024)
            print(f"📏 APK size: {size_mb:.1f} MB ({size_bytes:,} bytes)")
        print()
    except Exception as e:
        # If details fetch fails, just continue
        print(f"⚠️  Could not fetch package details: {e}")
        print()

    # Download APK
    version_str = f"version {version_code}" if version_code else "latest version"
    print(f"⬇️  Downloading {package_id} ({version_str})...")
    print()

    try:
        apk_path = client.download(
            package_id=package_id,
            dest_path=str(output_path),
            version_code=version_code
        )

        print()
        print("✅ Download complete!")
        print(f"📦 APK saved to: {apk_path}")

        # Show file size
        file_size = Path(apk_path).stat().st_size
        size_mb = file_size / (1024 * 1024)
        print(f"📏 File size: {size_mb:.2f} MB")

        print()
        print("✨ Done! You can now analyze the APK using playfast:")
        print(f"   from playfast import ApkAnalyzer")
        print(f"   analyzer = ApkAnalyzer('{apk_path}')")

    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)


def get_package_details(package_id: str, credentials_path: str):
    """
    Get package details from Google Play Store.

    Args:
        package_id: Package ID to query
        credentials_path: Path to credentials JSON file
    """
    print("=" * 60)
    print(f"Package Details: {package_id}")
    print("=" * 60)
    print()

    # Load client from credentials
    print(f"📂 Loading credentials...")
    try:
        client = ApkDownloader.from_credentials(credentials_path)
    except Exception as e:
        print(f"❌ Failed to load credentials: {e}")
        sys.exit(1)

    # Get package details
    print(f"🔍 Fetching details for {package_id}...")
    print()

    try:
        details = client.get_package_details(package_id)
        print(details)

    except Exception as e:
        print(f"❌ Failed to get details: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Download APK files from Google Play Store",
        epilog="""
Examples:
  %(prog)s com.instagram.android
  %(prog)s com.spotify.music --output /tmp/apks
  %(prog)s com.whatsapp --version-code 450814
  %(prog)s com.telegram --details
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "package_id",
        help="Package ID (e.g., com.instagram.android)"
    )

    parser.add_argument(
        "-o", "--output",
        default="/tmp/playfast_apks",
        help="Output directory (default: /tmp/playfast_apks)"
    )

    parser.add_argument(
        "-c", "--credentials",
        default=os.path.expanduser("~/.config/playfast/creds.json"),
        help="Path to creds JSON file (default: ~/.config/playfast/creds.json)"
    )

    parser.add_argument(
        "-v", "--version-code",
        type=int,
        help="Specific version code to download (default: latest)"
    )

    parser.add_argument(
        "-d", "--details",
        action="store_true",
        help="Show package details instead of downloading"
    )

    args = parser.parse_args()

    # Check if credentials file exists
    if not Path(args.credentials).exists():
        print(f"❌ Credentials file not found: {args.credentials}")
        print()
        print("💡 Run auth_setup.py first to set up authentication:")
        print("   python examples/download/auth_setup.py")
        sys.exit(1)

    if args.details:
        get_package_details(args.package_id, args.credentials)
    else:
        download_apk(
            package_id=args.package_id,
            credentials_path=args.credentials,
            output_dir=args.output,
            version_code=args.version_code
        )


if __name__ == "__main__":
    main()
