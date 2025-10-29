#!/usr/bin/env python3
"""APK comparison example.

This example demonstrates how to compare two versions of an APK
to identify changes in:
- Method count (DEX method count limit is 64K per DEX)
- Class count
- Permissions
- Components
"""

from playfast import ApkAnalyzer
from typing import Set, Dict, Any


def compare_statistics(apk1: ApkAnalyzer, apk2: ApkAnalyzer) -> None:
    """Compare basic statistics between two APKs."""
    print("📊 Statistics Comparison")
    print("-" * 70)

    stats1 = apk1.get_statistics()
    stats2 = apk2.get_statistics()

    metrics = [
        ("class_count", "Classes"),
        ("method_count", "Methods"),
        ("field_count", "Fields"),
        ("dex_count", "DEX files"),
        ("activity_count", "Activities"),
        ("service_count", "Services"),
        ("receiver_count", "Receivers"),
        ("provider_count", "Providers"),
        ("permission_count", "Permissions"),
    ]

    for key, label in metrics:
        val1 = stats1[key]
        val2 = stats2[key]
        diff = val2 - val1
        pct = (diff / val1 * 100) if val1 > 0 else 0

        sign = "+" if diff > 0 else ""
        icon = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"

        print(f"{icon} {label:15s}: {val1:8,} → {val2:8,}  ({sign}{diff:,} / {pct:+.1f}%)")

    print()


def compare_permissions(apk1: ApkAnalyzer, apk2: ApkAnalyzer) -> None:
    """Compare permissions between two APKs."""
    print("🔒 Permission Changes")
    print("-" * 70)

    perms1 = set(apk1.manifest.permissions)
    perms2 = set(apk2.manifest.permissions)

    added = perms2 - perms1
    removed = perms1 - perms2
    unchanged = perms1 & perms2

    if added:
        print(f"✅ Added permissions ({len(added)}):")
        for perm in sorted(added):
            print(f"  + {perm}")
        print()

    if removed:
        print(f"❌ Removed permissions ({len(removed)}):")
        for perm in sorted(removed):
            print(f"  - {perm}")
        print()

    if not added and not removed:
        print("➡️  No permission changes")
        print()

    print(f"📊 Summary: {len(unchanged)} unchanged, {len(added)} added, {len(removed)} removed")
    print()


def compare_components(apk1: ApkAnalyzer, apk2: ApkAnalyzer) -> None:
    """Compare components between two APKs."""
    print("📱 Component Changes")
    print("-" * 70)

    components = [
        ("activities", "Activities"),
        ("services", "Services"),
        ("receivers", "Receivers"),
        ("providers", "Providers"),
    ]

    for attr, label in components:
        set1 = set(getattr(apk1.manifest, attr))
        set2 = set(getattr(apk2.manifest, attr))

        added = set2 - set1
        removed = set1 - set2

        if added or removed:
            print(f"{label}:")
            if added:
                print(f"  ✅ Added: {len(added)}")
                for comp in sorted(added)[:3]:
                    print(f"     + {comp}")
                if len(added) > 3:
                    print(f"     ... and {len(added) - 3} more")

            if removed:
                print(f"  ❌ Removed: {len(removed)}")
                for comp in sorted(removed)[:3]:
                    print(f"     - {comp}")
                if len(removed) > 3:
                    print(f"     ... and {len(removed) - 3} more")
            print()

    print()


def check_method_limit(analyzer: ApkAnalyzer) -> None:
    """Check if APK is approaching the 64K DEX method limit."""
    print("⚠️  DEX Method Limit Analysis")
    print("-" * 70)

    stats = analyzer.get_statistics()
    method_count = stats['method_count']
    dex_count = stats['dex_count']

    # DEX limit is 65,536 methods per DEX file
    DEX_LIMIT = 65536
    avg_per_dex = method_count / dex_count

    print(f"Total methods: {method_count:,}")
    print(f"DEX files:     {dex_count}")
    print(f"Avg per DEX:   {avg_per_dex:,.0f}")

    if avg_per_dex > DEX_LIMIT * 0.9:
        print(f"⚠️  WARNING: Approaching DEX method limit ({avg_per_dex / DEX_LIMIT * 100:.1f}%)")
        print("   Consider:")
        print("   - Enabling ProGuard/R8 for code shrinking")
        print("   - Removing unused dependencies")
        print("   - Using Android App Bundles")
    elif avg_per_dex > DEX_LIMIT * 0.7:
        print(f"⚡ Getting close to DEX limit ({avg_per_dex / DEX_LIMIT * 100:.1f}%)")
    else:
        print(f"✅ Healthy method count ({avg_per_dex / DEX_LIMIT * 100:.1f}% of limit)")

    print()


def generate_comparison_report(apk1: ApkAnalyzer, apk2: ApkAnalyzer) -> None:
    """Generate a summary comparison report."""
    print("=" * 70)
    print("📋 COMPARISON SUMMARY")
    print("=" * 70)

    m1 = apk1.manifest
    m2 = apk2.manifest

    print(f"Package: {m1.package_name}")
    print(f"Version: {m1.version_name} → {m2.version_name}")
    print()

    stats1 = apk1.get_statistics()
    stats2 = apk2.get_statistics()

    # Calculate significant changes
    method_diff = stats2['method_count'] - stats1['method_count']
    class_diff = stats2['class_count'] - stats1['class_count']
    perm_diff = len(m2.permissions) - len(m1.permissions)

    print("Key Changes:")
    print(f"  📊 Methods:     {method_diff:+,} ({method_diff / stats1['method_count'] * 100:+.1f}%)")
    print(f"  📊 Classes:     {class_diff:+,} ({class_diff / stats1['class_count'] * 100:+.1f}%)")
    print(f"  🔒 Permissions: {perm_diff:+}")

    print()
    print("Impact Assessment:")

    # Method count impact
    if abs(method_diff) > 10000:
        print("  ⚠️  Significant method count change - verify build configuration")
    elif method_diff > 5000:
        print("  📈 Notable method increase - monitor APK size")
    elif method_diff < -5000:
        print("  ✅ Good method reduction - check for removed features")

    # Permission impact
    added_perms = set(m2.permissions) - set(m1.permissions)
    if added_perms:
        print(f"  🔒 New permissions added - update privacy policy")

    print()


def main():
    # For demonstration, we'll analyze the same APK twice
    # In practice, you would use two different versions
    apk_path = "../samples/com.instagram.android.apk"

    print("🔍 APK Version Comparison Tool")
    print("=" * 70)

    try:
        # Load both APKs (in real scenario, these would be different versions)
        print("Loading APK 1...")
        apk1 = ApkAnalyzer(apk_path)

        print("Loading APK 2...")
        apk2 = ApkAnalyzer(apk_path)  # Same APK for demo

        print()

        # Note: Since we're comparing the same APK, differences will be zero
        # This is just to demonstrate the API
        print("Note: Comparing same APK for demonstration")
        print("      In practice, use two different APK versions")
        print()

        compare_statistics(apk1, apk2)
        check_method_limit(apk1)
        compare_permissions(apk1, apk2)
        compare_components(apk1, apk2)
        generate_comparison_report(apk1, apk2)

        print("=" * 70)
        print("✅ Comparison complete!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
