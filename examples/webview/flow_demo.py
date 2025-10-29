#!/usr/bin/env python3
"""
WebView Flow Analysis Demo - Phase 3 (Complete Integration)

This demonstrates the complete WebView flow analysis including:
1. Entry point analysis (Activities, Services, etc.)
2. Call graph construction (method-to-method relationships)
3. WebView flow tracking (entry → WebView paths)
4. Data flow analysis (Intent → WebView.loadUrl)

Usage:
    python examples/webview_flow_demo.py <path_to_apk>
"""

import sys
from playfast import core


def main():
    if len(sys.argv) < 2:
        print("Usage: python webview_flow_demo.py <path_to_apk>")
        print("\nThis script demonstrates complete WebView call flow analysis:")
        print("  - Phase 1: Entry point identification (Activities, deeplinks)")
        print("  - Phase 2: Call graph construction (method relationships)")
        print("  - Phase 3: WebView flow analysis (entry → WebView paths)")
        print("  - Data flow tracking (Intent data → WebView)")
        return

    apk_path = sys.argv[1]

    print("\n" + "="*70)
    print("WebView Flow Analysis - Complete Integration")
    print("="*70)
    print(f"APK: {apk_path}\n")

    # ==================================================================
    # Method 1: Quick analysis - Direct API call
    # ==================================================================
    print("[Method 1] Quick Analysis")
    print("-" * 70)

    try:
        flows = core.analyze_webview_flows_from_apk(apk_path, max_depth=10)

        if flows:
            print(f"✅ Found {len(flows)} WebView flow(s)\n")

            # Show summary
            deeplink_flows = [f for f in flows if f.is_deeplink_handler]
            print(f"   Deeplink handlers leading to WebView: {len(deeplink_flows)}")
            print(f"   Other entry points to WebView: {len(flows) - len(deeplink_flows)}")

            # Show first few flows
            print(f"\n   Sample flows:")
            for flow in flows[:5]:
                print(f"   • {flow.entry_point} → {flow.webview_method}")
                print(f"     Paths: {flow.path_count}, Min depth: {flow.min_path_length}")
                if flow.is_deeplink_handler:
                    print(f"     🔗 DEEPLINK HANDLER")
        else:
            print("   No WebView flows found")
            print("   (This may mean the app doesn't use WebView, or uses it in complex ways)")

    except Exception as e:
        print(f"   Error during analysis: {e}")

    # ==================================================================
    # Method 2: Detailed analysis - Step by step
    # ==================================================================
    print("\n[Method 2] Detailed Analysis")
    print("-" * 70)

    try:
        # Create analyzer
        print("[1/4] Creating WebView flow analyzer...")
        analyzer = core.create_webview_analyzer_from_apk(apk_path)

        # Get statistics
        stats = analyzer.get_stats()
        print(f"      Entry points: {stats.get('entry_points', 0)}")
        print(f"      Deeplink handlers: {stats.get('deeplink_handlers', 0)}")
        print(f"      WebView methods: {stats.get('webview_methods', 0)}")

        # Analyze all flows
        print("\n[2/4] Analyzing all WebView flows...")
        all_flows = analyzer.analyze_flows(max_depth=10)

        if all_flows:
            print(f"      Found {len(all_flows)} flow(s)\n")

            # Group by entry point
            entry_point_groups = {}
            for flow in all_flows:
                ep = flow.entry_point
                if ep not in entry_point_groups:
                    entry_point_groups[ep] = []
                entry_point_groups[ep].append(flow)

            print(f"      Entry points with WebView access:")
            for ep, ep_flows in list(entry_point_groups.items())[:10]:
                wv_methods = set(f.webview_method.split('.')[-1] for f in ep_flows)
                print(f"      • {ep.split('.')[-1]}")
                print(f"        Methods: {', '.join(list(wv_methods)[:3])}")
                print(f"        Paths: {sum(f.path_count for f in ep_flows)}")
        else:
            print("      No flows found")

        # Find deeplink flows specifically
        print("\n[3/4] Finding deeplink → WebView flows...")
        deeplink_flows = analyzer.find_deeplink_flows(max_depth=10)

        if deeplink_flows:
            print(f"      Found {len(deeplink_flows)} deeplink flow(s)\n")

            for flow in deeplink_flows[:3]:
                print(f"      🔗 {flow.entry_point.split('.')[-1]}")
                print(f"         → {flow.webview_method.split('.')[-1]}")
                print(f"         Paths: {flow.path_count}, Min depth: {flow.min_path_length}")

                # Show shortest path
                shortest = flow.get_shortest_path()
                if shortest and shortest.methods:
                    method_names = [m.split('.')[-1] for m in shortest.methods]
                    path_str = " → ".join(method_names[:5])
                    if len(method_names) > 5:
                        path_str += f" ... ({len(method_names)} total)"
                    print(f"         Path: {path_str}")

                # Show lifecycle methods involved
                lifecycle = flow.get_lifecycle_methods()
                if lifecycle:
                    lc_names = [m.split('.')[-1] for m in lifecycle]
                    print(f"         Lifecycle: {', '.join(lc_names)}")

                print()
        else:
            print("      No deeplink flows found")

        # Analyze data flows
        print("[4/4] Analyzing data flows (Intent → WebView)...")
        if all_flows:
            data_flows = analyzer.analyze_data_flows(all_flows)

            if data_flows:
                print(f"      Found {len(data_flows)} potential data flow(s)\n")

                # Group by confidence
                high_conf = [df for df in data_flows if df.confidence >= 0.7]
                medium_conf = [df for df in data_flows if 0.4 <= df.confidence < 0.7]
                low_conf = [df for df in data_flows if df.confidence < 0.4]

                print(f"      Confidence breakdown:")
                print(f"      • High (≥0.7):   {len(high_conf)} flows")
                print(f"      • Medium (0.4-0.7): {len(medium_conf)} flows")
                print(f"      • Low (<0.4):    {len(low_conf)} flows")

                # Show high confidence flows
                if high_conf:
                    print(f"\n      High confidence data flows:")
                    for df in high_conf[:3]:
                        source_method = df.source.split('.')[-1]
                        sink_method = df.sink.split('.')[-1]
                        print(f"      • {source_method} → {sink_method}")
                        print(f"        Confidence: {df.confidence:.2f}")
                        print(f"        Hops: {len(df.flow_path)}")
            else:
                print("      No Intent→WebView data flows detected")
                print("      (WebView may use hardcoded URLs or other data sources)")
        else:
            print("      Skipped (no flows to analyze)")

    except Exception as e:
        print(f"   Error during detailed analysis: {e}")
        import traceback
        traceback.print_exc()

    # ==================================================================
    # Summary and Recommendations
    # ==================================================================
    print("\n" + "="*70)
    print("Analysis Summary")
    print("="*70)

    if flows and any(f.is_deeplink_handler for f in flows):
        print("⚠️  SECURITY CONSIDERATIONS:")
        print("   • Deeplink handlers can load URLs in WebView")
        print("   • Review if Intent data is properly validated before WebView.loadUrl()")
        print("   • Check for URL scheme validation (http/https only)")
        print("   • Verify JavaScript interface security if addJavascriptInterface is used")

    print("\n📊 What this analysis shows:")
    print("   1. Which Activities/Components can trigger WebView")
    print("   2. Call paths from entry points to WebView APIs")
    print("   3. Deeplink handlers that may load untrusted URLs")
    print("   4. Data flow from Intent extras to WebView.loadUrl()")

    print("\n🔍 For security review:")
    print("   • Focus on deeplink handlers with high-confidence data flows")
    print("   • Check if URL validation exists in the call path")
    print("   • Review JavaScript interface usage")
    print("   • Test with malicious deeplink URLs")

    print("\n" + "="*70)
    print("✅ Analysis Complete")
    print("="*70)


if __name__ == "__main__":
    main()
