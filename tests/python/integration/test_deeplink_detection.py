#!/usr/bin/env python3
"""Test deeplink detection in APK manifest"""

from pathlib import Path
from playfast import core
import time

def analyze_manifest_raw(apk_path):
    """Analyze raw manifest to see available data"""
    print("🔍 Raw Manifest Analysis")
    print("=" * 70)

    manifest = core.parse_manifest_from_apk(str(apk_path))

    print(f"Package: {manifest.package_name}")
    print(f"Activities: {len(manifest.activities)}")
    print()

    # Print first few activities to see structure
    print("Sample activities:")
    for activity in manifest.activities[:5]:
        print(f"  - {activity}")
    print()

    return manifest

def test_instagram():
    """Test Instagram APK"""
    apk_path = Path("../samples/com.instagram.android.apk")

    print("\n" + "=" * 70)
    print("📱 Instagram APK")
    print("=" * 70)

    manifest = analyze_manifest_raw(apk_path)

    # Known Instagram deeplinks (for reference)
    print("Known Instagram deeplink patterns:")
    print("  - instagram://user?username=xxx")
    print("  - instagram://media?id=xxx")
    print("  - https://instagram.com/xxx")
    print()

def test_baemin():
    """Test Baemin APK"""
    apk_path = Path("../samples/com.sampleapp.apk")

    print("\n" + "=" * 70)
    print("📱 Baemin APK (com.sampleapp)")
    print("=" * 70)

    manifest = analyze_manifest_raw(apk_path)

    # Check for common deeplink activities
    deeplink_keywords = ['deep', 'link', 'uri', 'url', 'intent', 'scheme']
    potential_deeplink_activities = []

    for activity in manifest.activities:
        activity_lower = activity.lower()
        if any(keyword in activity_lower for keyword in deeplink_keywords):
            potential_deeplink_activities.append(activity)

    if potential_deeplink_activities:
        print(f"✅ Found {len(potential_deeplink_activities)} potential deeplink-related activities:")
        for activity in potential_deeplink_activities[:10]:
            print(f"  - {activity}")
        if len(potential_deeplink_activities) > 10:
            print(f"  ... and {len(potential_deeplink_activities) - 10} more")
    else:
        print("❌ No obvious deeplink-related activities found")
    print()

def check_manifest_xml_access():
    """Check if we can access raw manifest XML"""
    print("\n" + "=" * 70)
    print("🔧 Manifest XML Access Test")
    print("=" * 70)

    apk_path = Path("../samples/com.sampleapp.apk")

    try:
        # Try to get raw manifest
        raw_manifest = core.extract_manifest_raw(str(apk_path))
        print(f"✅ Raw manifest extracted: {len(raw_manifest)} bytes")
        print()

        # Note: raw_manifest is binary AXML format
        # To get deeplinks, we'd need to parse intent-filter and data tags
        print("Note: Raw manifest is in binary AXML format")
        print("      Need to parse <intent-filter> and <data> tags for deeplinks")
        print()

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🔍 Deeplink Detection Capability Analysis")
    print("=" * 70)

    # Test manifest access
    can_access = check_manifest_xml_access()

    if can_access:
        # Test on actual APKs
        test_baemin()
        test_instagram()

        print("\n" + "=" * 70)
        print("📋 CONCLUSION")
        print("=" * 70)
        print()
        print("Current Capabilities:")
        print("  ✅ Can extract raw AndroidManifest.xml (binary AXML)")
        print("  ✅ Can parse basic manifest info (package, activities, etc.)")
        print("  ❌ Cannot parse <intent-filter> yet (not implemented)")
        print("  ❌ Cannot parse <data> tags yet (not implemented)")
        print()
        print("What's Needed for Full Deeplink Analysis:")
        print("  1. Parse <intent-filter> tags from manifest")
        print("  2. Extract <data> tags (scheme, host, path)")
        print("  3. Identify VIEW intents with http/https schemes")
        print("  4. Extract custom URL schemes (instagram://, etc.)")
        print()
        print("Workaround:")
        print("  - Use rusty-axml to parse full XML tree")
        print("  - Look for 'intent-filter' nodes")
        print("  - Extract 'data' child nodes with scheme/host attributes")
        print()

if __name__ == "__main__":
    main()
