#!/usr/bin/env python3
"""
WebView Flow Analysis - Quick Demo (High-level API)

This demonstrates the high-level ApkAnalyzer API with optimized performance.
"""

import sys
import time
from playfast import ApkAnalyzer


def main():
    if len(sys.argv) < 2:
        print("Usage: python webview_flow_quick_demo.py <path_to_apk>")
        print("\nExample:")
        print("  python webview_flow_quick_demo.py app.apk")
        return

    apk_path = sys.argv[1]

    print("\n" + "="*70)
    print("WebView Flow Analysis - Quick Mode (High-level API)")
    print("="*70)
    print(f"APK: {apk_path}")
    print()

    # Create analyzer (high-level, clean API!)
    print("[1/3] Initializing APK Analyzer...")
    start = time.time()
    apk = ApkAnalyzer(apk_path)
    elapsed = time.time() - start
    print(f"      ✅ Done in {elapsed:.1f}s")
    print(f"      {apk}")
    print()

    # Analyze entry points (one-liner!)
    print("[2/3] Analyzing entry points...")
    start = time.time()
    entry_analysis = apk.analyze_entry_points()
    elapsed = time.time() - start

    entry_points = entry_analysis['entry_points']
    deeplink_handlers = entry_analysis['deeplink_handlers']

    print(f"      ✅ Done in {elapsed:.1f}s")
    print(f"      Entry points: {len(entry_points)}")
    print(f"      Deeplink handlers: {len(deeplink_handlers)}")
    print()

    # Find WebView flows (one-liner with auto-optimization!)
    print("[3/3] Finding WebView flows (optimized, quick mode)...")
    start = time.time()
    flows = apk.find_webview_flows(max_depth=5)  # Shallow depth for quick demo
    elapsed = time.time() - start

    print(f"      ✅ Done in {elapsed:.1f}s")
    print(f"      Flows found: {len(flows)}")
    print()

    # Show results
    if flows:
        deeplink_flows = [f for f in flows if f.is_deeplink_handler]

        print("="*70)
        print("Results")
        print("="*70)
        print(f"Total flows: {len(flows)}")
        print(f"Deeplink → WebView: {len(deeplink_flows)}")
        print()

        if deeplink_flows:
            print("⚠️  Potential XSS Vulnerabilities (Deeplink → WebView):")
            for flow in deeplink_flows[:5]:
                entry_short = flow.entry_point.split('.')[-1]
                webview_short = flow.sink_method.split('.')[-1]
                print(f"   🔗 {entry_short} → {webview_short}")
                print(f"      Paths: {flow.path_count}, Min depth: {flow.min_path_length}")
            if len(deeplink_flows) > 5:
                print(f"   ... and {len(deeplink_flows) - 5} more")
            print()

        print("Sample WebView Flows:")
        for i, flow in enumerate(flows[:10], 1):
            entry_short = flow.entry_point.split('.')[-1]
            webview_short = flow.sink_method.split('.')[-1]
            marker = "🔗" if flow.is_deeplink_handler else "  "
            print(f"  {marker} {i}. {entry_short} → {webview_short}")
            print(f"       Paths: {flow.path_count}, Depth: {flow.min_path_length}")

        if len(flows) > 10:
            print(f"  ... and {len(flows) - 10} more")

    else:
        print("ℹ️  No WebView flows found")
        print("   This may mean:")
        print("   - App doesn't use WebView")
        print("   - Flows are deeper than max_depth=5")

    print("\n" + "="*70)
    print("✅ Quick Analysis Complete")
    print("="*70)
    print()
    print("💡 Try other analyses:")
    print(f"   # Deeper analysis (slower but more complete)")
    print(f"   flows = apk.find_webview_flows(max_depth=15)")
    print()
    print(f"   # Other flow types")
    print(f"   apk.find_file_flows()     # File I/O")
    print(f"   apk.find_network_flows()  # Network")
    print(f"   apk.find_sql_flows()      # SQL")


if __name__ == "__main__":
    main()
