#!/usr/bin/env python3
"""
Test Filtered Analysis - Immediate Optimization

Compares full analysis vs entry-point-filtered analysis
to demonstrate immediate performance improvement without code changes.
"""

import sys
import time
from playfast import core


def extract_packages_from_entry_points(entry_points, depth=2):
    """
    Extract unique packages from entry points.

    Args:
        entry_points: List of EntryPoint objects
        depth: Package depth (2 = com.example, 3 = com.example.app)

    Returns:
        List of package prefixes (in dot notation for DEX filtering)
    """
    packages = set()

    for ep in entry_points:
        # EntryPoint is an object with .class_name attribute
        # Format: "com.woowahan.baemincall.system.notification.NotificationTrampolineActivity"
        class_name = ep.class_name

        # Split by dots and take first N parts
        parts = class_name.split('.')
        if len(parts) >= depth:
            # Get first N parts (e.g., "com.woowahan")
            pkg = '.'.join(parts[:depth])
            packages.add(pkg)

    return list(packages)


def test_filtered_analysis(apk_path):
    print("="*70)
    print("Entry-Point Filtered Analysis Test")
    print("="*70)
    print(f"APK: {apk_path}\n")

    # Step 1: Analyze entry points
    print("[1/3] Analyzing entry points...")
    start = time.time()
    entry_analyzer = core.analyze_entry_points_from_apk(apk_path)
    entry_points = entry_analyzer.analyze()
    entry_time = time.time() - start

    print(f"      ✅ Found {len(entry_points)} entry points in {entry_time:.1f}s")

    # Show sample entry points
    print(f"      Sample entry points:")
    for ep in entry_points[:3]:
        print(f"        - {ep.class_name} ({ep.component_type})")
    print()

    # Extract packages at different depths
    packages_2 = extract_packages_from_entry_points(entry_points, depth=2)
    packages_3 = extract_packages_from_entry_points(entry_points, depth=3)

    print(f"      Packages (depth=2): {len(packages_2)} packages")
    for pkg in sorted(packages_2)[:5]:
        print(f"        - {pkg}")
    if len(packages_2) > 5:
        print(f"        ... and {len(packages_2) - 5} more")
    print()

    # Step 2: Full analysis (baseline)
    print("[2/3] Full analysis (baseline)...")
    start = time.time()
    graph_full = core.build_call_graph_from_apk_parallel(apk_path, None)
    time_full = time.time() - start
    stats_full = graph_full.get_stats()

    print(f"      ✅ Completed in {time_full:.1f}s")
    print(f"      Total methods: {stats_full['total_methods']}")
    print(f"      Total edges: {stats_full['total_edges']}")
    print()

    # Step 3: Filtered analysis (depth=2)
    print("[3/3] Filtered analysis (entry point packages)...")
    start = time.time()
    graph_filtered = core.build_call_graph_from_apk_parallel(apk_path, packages_2)
    time_filtered = time.time() - start
    stats_filtered = graph_filtered.get_stats()

    print(f"      ✅ Completed in {time_filtered:.1f}s")
    print(f"      Total methods: {stats_filtered['total_methods']}")
    print(f"      Total edges: {stats_filtered['total_edges']}")
    print()

    # Results comparison
    print("="*70)
    print("Performance Comparison")
    print("="*70)

    speedup = time_full / time_filtered if time_filtered > 0 else 0
    time_saved = time_full - time_filtered
    methods_reduced = stats_full['total_methods'] - stats_filtered['total_methods']

    print(f"Full Analysis:")
    print(f"  Time:    {time_full:.1f}s")
    print(f"  Methods: {stats_full['total_methods']}")
    print()

    print(f"Filtered Analysis:")
    print(f"  Time:    {time_filtered:.1f}s")
    print(f"  Methods: {stats_filtered['total_methods']}")
    print()

    print(f"Improvement:")
    print(f"  ⚡ Speedup:        {speedup:.2f}x")
    print(f"  ⏱️  Time saved:     {time_saved:.1f}s ({time_saved/time_full*100:.0f}%)")
    print(f"  📉 Methods reduced: {methods_reduced} ({methods_reduced/stats_full['total_methods']*100:.0f}%)")

    # Analysis
    print()
    print("Analysis:")
    if speedup >= 2.0:
        print("  🎉 Excellent! 2x+ speedup with filtered analysis")
    elif speedup >= 1.5:
        print("  ✅ Great! Significant improvement with filtered analysis")
    elif speedup >= 1.2:
        print("  👍 Good! Noticeable improvement with filtered analysis")
    else:
        print("  ℹ️  Minimal improvement - most methods are in entry point packages")

    print()
    print("💡 Recommendation:")
    print(f"  Use filtered analysis with {len(packages_2)} packages for WebView flows")
    print(f"  This covers all entry points while excluding library code")

    print("="*70)

    return {
        'full_time': time_full,
        'filtered_time': time_filtered,
        'speedup': speedup,
        'methods_reduced': methods_reduced,
        'packages': packages_2
    }


def quick_test(apk_path):
    """Quick test showing just the key metrics"""
    print("="*70)
    print("Quick Filtered Analysis Test")
    print("="*70)
    print(f"APK: {apk_path}\n")

    # Get entry points
    entry_analyzer = core.analyze_entry_points_from_apk(apk_path)
    entry_points = entry_analyzer.analyze()
    packages = extract_packages_from_entry_points(entry_points, depth=2)

    print(f"Entry points: {len(entry_points)}")
    print(f"Packages:     {len(packages)}")
    print()

    # Test both
    print("Testing full analysis...")
    start = time.time()
    graph_full = core.build_call_graph_from_apk_parallel(apk_path, None)
    time_full = time.time() - start

    print("Testing filtered analysis...")
    start = time.time()
    graph_filtered = core.build_call_graph_from_apk_parallel(apk_path, packages)
    time_filtered = time.time() - start

    # Results
    stats_full = graph_full.get_stats()
    stats_filtered = graph_filtered.get_stats()

    print()
    print(f"Full:     {time_full:.1f}s ({stats_full['total_methods']} methods)")
    print(f"Filtered: {time_filtered:.1f}s ({stats_filtered['total_methods']} methods)")
    print(f"Speedup:  {time_full/time_filtered:.2f}x")
    print("="*70)


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_filtered_analysis.py <apk> [--quick]")
        print("\nExample:")
        print("  python test_filtered_analysis.py app.apk")
        print("  python test_filtered_analysis.py app.apk --quick")
        return

    apk_path = sys.argv[1]
    quick = "--quick" in sys.argv

    if quick:
        quick_test(apk_path)
    else:
        test_filtered_analysis(apk_path)


if __name__ == "__main__":
    main()
