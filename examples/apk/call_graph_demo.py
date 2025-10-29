#!/usr/bin/env python3
"""
Call Graph Demo - Phase 2 of WebView Call Flow

This demonstrates how to use the call graph builder to:
1. Build method-to-method call relationships
2. Find paths from entry points to specific APIs (e.g., WebView.loadUrl)
3. Analyze call chains

Usage:
    python examples/call_graph_demo.py <path_to_apk>
"""

import sys
from playfast import core


def main():
    if len(sys.argv) < 2:
        print("Usage: python call_graph_demo.py <path_to_apk>")
        print("\nThis script demonstrates Phase 2 of WebView call flow analysis:")
        print("  - Builds a call graph showing method-to-method relationships")
        print("  - Finds paths from entry points to WebView APIs")
        print("  - Analyzes call chains and dependencies")
        return

    apk_path = sys.argv[1]

    print("\n" + "="*70)
    print("Call Graph Analysis - Phase 2 Demo")
    print("="*70)
    print(f"APK: {apk_path}\n")

    # Step 1: Build call graph (optionally filter to specific packages)
    print("[1/4] Building call graph...")
    print("      (This may take a while for large APKs)")

    # Filter to app package to reduce graph size
    # Adjust the filter based on your app's package name
    call_graph = core.build_call_graph_from_apk(apk_path, None)  # None = all classes

    stats = call_graph.get_stats()
    print(f"      Methods: {stats['total_methods']}")
    print(f"      Call edges: {stats['total_edges']}")

    # Step 2: Find WebView-related methods
    print("\n[2/4] Finding WebView-related methods...")
    webview_methods = call_graph.find_methods("WebView")

    if webview_methods:
        print(f"      Found {len(webview_methods)} WebView method(s):\n")
        for method in webview_methods[:10]:  # Show first 10
            print(f"      - {method}")
        if len(webview_methods) > 10:
            print(f"      ... and {len(webview_methods) - 10} more")
    else:
        print("      No WebView methods found")

    # Step 3: Find loadUrl methods specifically
    print("\n[3/4] Finding WebView.loadUrl calls...")
    loadurl_methods = call_graph.find_methods("loadUrl")

    if loadurl_methods:
        print(f"      Found {len(loadurl_methods)} loadUrl call(s):\n")
        for method in loadurl_methods:
            print(f"      📍 {method}")

            # Find callers of this method
            callers = call_graph.get_callers(method)
            if callers:
                print(f"         Called by {len(callers)} method(s):")
                for caller in callers[:5]:  # Show first 5 callers
                    print(f"           ← {caller}")
                if len(callers) > 5:
                    print(f"           ... and {len(callers) - 5} more")
    else:
        print("      No loadUrl calls found")

    # Step 4: Find paths from onCreate to loadUrl (example)
    print("\n[4/4] Finding call paths...")

    # Look for onCreate methods as entry points
    oncreate_methods = call_graph.find_methods("onCreate")

    if oncreate_methods and loadurl_methods:
        print(f"      Searching paths from onCreate to loadUrl...")

        paths_found = 0
        for oncreate in oncreate_methods[:3]:  # Check first 3 onCreate methods
            for loadurl in loadurl_methods[:2]:  # Check first 2 loadUrl methods
                paths = call_graph.find_paths(oncreate, loadurl, max_depth=8)

                if paths:
                    paths_found += len(paths)
                    print(f"\n      Path from {oncreate.split('.')[-1]} → loadUrl:")
                    for path in paths[:2]:  # Show first 2 paths
                        print(f"         Depth: {path.length}")
                        print(f"         Route: {' → '.join([m.split('.')[-1] for m in path.methods])}")

        if paths_found == 0:
            print("      No direct paths found (may require deeper search or different entry points)")
    else:
        print("      Insufficient methods for path finding")

    # Step 5: Show some statistics
    print("\n" + "="*70)
    print("Call Graph Statistics")
    print("="*70)
    print(f"Total methods analyzed: {stats['total_methods']}")
    print(f"Total method calls: {stats['total_edges']}")

    if stats['total_methods'] > 0:
        avg_calls = stats['total_edges'] / stats['total_methods']
        print(f"Average calls per method: {avg_calls:.2f}")

    print("\n" + "="*70)
    print("✅ Phase 2 Complete")
    print("="*70)

    print("\nInterpretation:")
    print("  • The call graph shows method-to-method relationships")
    print("  • Paths from onCreate to loadUrl indicate how WebView is initialized")
    print("  • Long paths (depth > 5) may indicate complex initialization logic")
    print("  • Multiple paths suggest different code paths leading to WebView")

    print("\nNext steps:")
    print("  • Phase 3: Track data flow from Intent extras to WebView.loadUrl()")
    print("  • Phase 4: Integrate with entry point analysis for complete flow")


if __name__ == "__main__":
    main()
