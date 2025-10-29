#!/usr/bin/env python3
"""
Analyze Call Graph Coverage - Entry Point vs Full Analysis

This script compares:
1. How many classes are in the full call graph
2. How many classes are actually reachable from entry points
3. The performance difference
"""

import sys
import time
from playfast import core


def analyze_coverage(apk_path):
    print("="*70)
    print("Call Graph Coverage Analysis")
    print("="*70)
    print(f"APK: {apk_path}\n")

    # Step 1: Analyze entry points
    print("[1/3] Analyzing entry points...")
    start = time.time()
    entry_analyzer = core.analyze_entry_points_from_apk(apk_path)
    entry_points = entry_analyzer.analyze()
    entry_time = time.time() - start

    print(f"      ✅ Found {len(entry_points)} entry points in {entry_time:.1f}s")
    print(f"      Entry points:")
    for ep in entry_points[:5]:  # Show first 5
        print(f"        - {ep['class_name']} ({ep['component_type']})")
    if len(entry_points) > 5:
        print(f"        ... and {len(entry_points) - 5} more")
    print()

    # Step 2: Build full call graph
    print("[2/3] Building full call graph...")
    start = time.time()
    call_graph = core.build_call_graph_from_apk_parallel(apk_path, None)
    graph_time = time.time() - start

    stats = call_graph.get_stats()
    print(f"      ✅ Built graph in {graph_time:.1f}s")
    print(f"      Total methods in graph: {stats['total_methods']}")
    print(f"      Total edges: {stats['total_edges']}")
    print()

    # Step 3: Find reachable methods from entry points
    print("[3/3] Finding reachable methods from entry points...")
    start = time.time()

    reachable_methods = set()
    lifecycle_methods = ["onCreate", "onStart", "onResume", "onNewIntent",
                         "onActivityResult", "onBind", "onReceive"]

    for ep in entry_points:
        for lifecycle in lifecycle_methods:
            source = f"{ep['class_name']}.{lifecycle}"

            # Find all methods reachable from this entry point
            # Using max_depth=15 to be thorough
            for method in stats.get('methods', []):
                paths = call_graph.find_paths(source, method, 15)
                if paths:
                    reachable_methods.add(method)
                    # Also add all intermediate methods in paths
                    for path in paths:
                        for m in path.methods:
                            reachable_methods.add(m)

    reachable_time = time.time() - start
    print(f"      ✅ Analysis complete in {reachable_time:.1f}s")
    print()

    # Results
    print("="*70)
    print("Results")
    print("="*70)

    total_methods = stats['total_methods']
    reachable_count = len(reachable_methods)
    unreachable_count = total_methods - reachable_count

    print(f"Total methods in call graph:  {total_methods}")
    print(f"Reachable from entry points:  {reachable_count} ({reachable_count/total_methods*100:.1f}%)")
    print(f"Unreachable (dead code):      {unreachable_count} ({unreachable_count/total_methods*100:.1f}%)")
    print()

    print(f"⏱️  Time breakdown:")
    print(f"  Entry point analysis: {entry_time:.1f}s")
    print(f"  Full call graph:      {graph_time:.1f}s")
    print(f"  Reachability check:   {reachable_time:.1f}s")
    print(f"  Total:                {entry_time + graph_time + reachable_time:.1f}s")
    print()

    print("💡 Optimization Opportunity:")
    if unreachable_count > total_methods * 0.3:  # More than 30% unreachable
        saved_time = graph_time * (unreachable_count / total_methods)
        print(f"   If we only analyzed reachable methods, we could save ~{saved_time:.1f}s")
        print(f"   That's a potential {saved_time/graph_time*100:.0f}% speedup!")
    else:
        print(f"   Most methods are reachable, full analysis is appropriate")

    print("="*70)

    return {
        'total_methods': total_methods,
        'reachable': reachable_count,
        'unreachable': unreachable_count,
        'graph_time': graph_time,
        'entry_points': len(entry_points)
    }


def quick_stats(apk_path):
    """Quick version that just counts classes"""
    print("="*70)
    print("Quick Call Graph Statistics")
    print("="*70)
    print(f"APK: {apk_path}\n")

    # Entry points
    print("[1/2] Entry points...")
    entry_analyzer = core.analyze_entry_points_from_apk(apk_path)
    entry_points = entry_analyzer.analyze()
    print(f"      ✅ {len(entry_points)} entry points")

    # Full graph
    print("[2/2] Full call graph...")
    start = time.time()
    call_graph = core.build_call_graph_from_apk_parallel(apk_path, None)
    elapsed = time.time() - start

    stats = call_graph.get_stats()
    print(f"      ✅ {stats['total_methods']} methods in {elapsed:.1f}s")
    print()

    print("Summary:")
    print(f"  Entry points:    {len(entry_points)}")
    print(f"  Total methods:   {stats['total_methods']}")
    print(f"  Methods/entry:   {stats['total_methods'] / len(entry_points):.0f}")
    print(f"  Build time:      {elapsed:.1f}s")
    print("="*70)


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_call_graph_coverage.py <apk> [--quick]")
        print("\nExample:")
        print("  python analyze_call_graph_coverage.py app.apk")
        print("  python analyze_call_graph_coverage.py app.apk --quick")
        return

    apk_path = sys.argv[1]
    quick = "--quick" in sys.argv

    if quick:
        quick_stats(apk_path)
    else:
        analyze_coverage(apk_path)


if __name__ == "__main__":
    main()
