#!/usr/bin/env python3
"""Quick test script for APK extraction functionality.
This tests the basic APK loading and DEX detection.
"""

from pathlib import Path
import sys


# Try to import the Rust module
try:
    from playfast import core

    print("✓ Successfully imported playfast.core")
except ImportError as e:
    print(f"✗ Failed to import playfast.core: {e}")
    print("\nTo build the Rust extension, run:")
    print("  uv run maturin develop --release")
    sys.exit(1)

# Test with Instagram APK
apk_path = Path("../samples/com.instagram.android.apk")

if not apk_path.exists():
    print(f"✗ APK file not found: {apk_path}")
    print("Please ensure the Instagram APK is in the samples/ directory")
    sys.exit(1)

print(f"\nTesting with: {apk_path}")
print("=" * 60)

try:
    # Extract APK info
    dex_count, has_manifest, has_resources, dex_files = core.extract_apk_info(
        str(apk_path)
    )

    print("\n📦 APK Information:")
    print(f"   DEX Count: {dex_count}")
    print(f"   Has Manifest: {has_manifest}")
    print(f"   Has Resources: {has_resources}")
    print("\n📄 DEX Files:")
    for i, dex_file in enumerate(dex_files, 1):
        print(f"   {i}. {dex_file}")

    print("\n✓ APK extraction successful!")

    # Try to extract manifest
    print("\n🔍 Extracting AndroidManifest.xml...")
    manifest_data = core.extract_manifest_raw(str(apk_path))
    print(f"   Manifest size: {len(manifest_data)} bytes")
    print(f"   First 20 bytes (hex): {manifest_data[:20].hex()}")

    print("\n✓ All tests passed!")

except Exception as e:
    print(f"\n✗ Error during testing: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
