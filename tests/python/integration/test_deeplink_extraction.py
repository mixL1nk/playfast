#!/usr/bin/env python3
"""Test deeplink extraction from APK manifests."""

from pathlib import Path
import time

from playfast import core


def analyze_deeplinks(apk_name, apk_path):
    """Analyze deeplinks in an APK."""
    print(f"\n{'=' * 70}")
    print(f"🔍 Deeplink Analysis: {apk_name}")
    print(f"{'=' * 70}\n")

    start = time.time()
    manifest = core.parse_manifest_from_apk(str(apk_path))
    parse_time = time.time() - start

    print(f"✅ Manifest parsed in {parse_time * 1000:.2f}ms")
    print(f"Package: {manifest.package_name}")
    print(f"Intent filters found: {len(manifest.intent_filters)}")
    print()

    if not manifest.intent_filters:
        print("❌ No intent filters found")
        return

    # Get deeplink-specific filters
    deeplinks = manifest.get_deeplinks()
    print(f"🔗 Deeplink intent filters: {len(deeplinks)}")
    print()

    # Categorize deeplinks
    http_deeplinks = []
    https_deeplinks = []
    custom_schemes = []

    for intent_filter in deeplinks:
        print(f"Activity: {intent_filter.activity}")
        print(f"  Actions: {', '.join(intent_filter.actions)}")
        print(f"  Categories: {', '.join(intent_filter.categories)}")

        if intent_filter.data:
            print(f"  Data ({len(intent_filter.data)} entries):")
            for data in intent_filter.data:
                parts = []
                if data.scheme:
                    parts.append(f"scheme={data.scheme}")

                    # Categorize by scheme
                    if data.scheme == "http":
                        http_deeplinks.append(intent_filter)
                    elif data.scheme == "https":
                        https_deeplinks.append(intent_filter)
                    else:
                        custom_schemes.append((data.scheme, intent_filter))

                if data.host:
                    parts.append(f"host={data.host}")
                if data.path:
                    parts.append(f"path={data.path}")
                if data.path_prefix:
                    parts.append(f"pathPrefix={data.path_prefix}")
                if data.path_pattern:
                    parts.append(f"pathPattern={data.path_pattern}")

                print(f"    - {', '.join(parts)}")
        print()

    # Summary
    print("=" * 70)
    print("📊 Deeplink Summary:")
    print(f"  HTTP deeplinks:   {len(set(http_deeplinks))}")
    print(f"  HTTPS deeplinks:  {len(set(https_deeplinks))}")
    print(f"  Custom schemes:   {len({s for s, _ in custom_schemes})}")

    if custom_schemes:
        unique_schemes = {s for s, _ in custom_schemes}
        print("\n  Custom URL schemes:")
        for scheme in sorted(unique_schemes):
            print(f"    - {scheme}://")

    print()

    # Security recommendations
    if http_deeplinks:
        print("⚠️  Security Warning:")
        print("  Found HTTP deeplinks (unencrypted)")
        print("  Recommendation: Use HTTPS instead")
        print()


def main():
    print("🔍 Deeplink Extraction Test")
    print("=" * 70)

    apks = [
        ("Baemin (com.sampleapp.apk)", Path("../samples/com.sampleapp.apk")),
        ("Instagram", Path("../samples/com.instagram.android.apk")),
    ]

    for apk_name, apk_path in apks:
        if not apk_path.exists():
            print(f"⚠️  {apk_name} not found: {apk_path}")
            continue

        try:
            analyze_deeplinks(apk_name, apk_path)
        except Exception as e:
            print(f"❌ Error analyzing {apk_name}: {e}")
            import traceback

            traceback.print_exc()

    print("=" * 70)
    print("✅ Deeplink extraction test complete!")


if __name__ == "__main__":
    main()
