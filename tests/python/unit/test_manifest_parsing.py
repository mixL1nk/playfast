#!/usr/bin/env python3
"""Test script for AndroidManifest parsing functionality."""

from pathlib import Path
import time

from playfast import core


def test_manifest_parsing():
    """Test parsing AndroidManifest.xml from Instagram APK."""
    apk_path = Path("../samples/com.instagram.android.apk")

    if not apk_path.exists():
        print(f"❌ APK file not found: {apk_path}")
        return

    print(f"📦 Testing manifest parsing with: {apk_path.name}")
    print("=" * 70)

    try:
        # Parse manifest
        start_time = time.time()
        manifest = core.parse_manifest_from_apk(str(apk_path))
        elapsed = time.time() - start_time

        print(f"\n✅ Successfully parsed manifest in {elapsed * 1000:.2f}ms\n")

        # Display basic info
        print("📋 Basic Information:")
        print(f"  Package Name:      {manifest.package_name}")
        print(f"  Version Name:      {manifest.version_name or 'N/A'}")
        print(f"  Version Code:      {manifest.version_code or 'N/A'}")
        print(f"  Min SDK:           {manifest.min_sdk_version or 'N/A'}")
        print(f"  Target SDK:        {manifest.target_sdk_version or 'N/A'}")
        print(f"  Application Label: {manifest.application_label or 'N/A'}")

        # Display component counts
        print("\n🔧 Components:")
        print(f"  Activities:        {len(manifest.activities)}")
        print(f"  Services:          {len(manifest.services)}")
        print(f"  Receivers:         {len(manifest.receivers)}")
        print(f"  Providers:         {len(manifest.providers)}")
        print(f"  Permissions:       {len(manifest.permissions)}")

        # Show first few activities
        if manifest.activities:
            print("\n📱 Sample Activities (first 5):")
            for activity in manifest.activities[:5]:
                print(f"  - {activity}")

        # Show first few services
        if manifest.services:
            print("\n⚙️  Sample Services (first 5):")
            for service in manifest.services[:5]:
                print(f"  - {service}")

        # Show first few permissions
        if manifest.permissions:
            print("\n🔒 Sample Permissions (first 10):")
            for perm in manifest.permissions[:10]:
                print(f"  - {perm}")

        # Test __repr__
        print("\n📊 Manifest representation:")
        print(f"  {manifest!r}")

        # Test to_dict conversion
        print("\n📝 Testing to_dict() method...")
        manifest_dict = manifest.to_dict()
        print(f"  ✅ Successfully converted to dict with {len(manifest_dict)} keys")

        print("\n" + "=" * 70)
        print("✅ All tests passed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_manifest_parsing()
