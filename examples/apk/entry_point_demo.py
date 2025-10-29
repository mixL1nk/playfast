#!/usr/bin/env python3
"""
Entry Point Analysis Demo - Phase 1 of WebView Call Flow

This demonstrates how to use the entry point analyzer to:
1. Link AndroidManifest.xml components with DEX classes
2. Identify deeplink handlers
3. Find WebView-related entry points

Usage:
    python examples/entry_point_analysis_demo.py <path_to_apk>
"""

import sys
from playfast import core


def main():
    if len(sys.argv) < 2:
        print("Usage: python entry_point_analysis_demo.py <path_to_apk>")
        print("\nThis script demonstrates Phase 1 of WebView call flow analysis:")
        print("  - Links manifest components (Activity, Service, etc.) with DEX classes")
        print("  - Identifies deeplink handlers")
        print("  - Shows which components have code vs. declared-only")
        return

    apk_path = sys.argv[1]

    print("\n" + "="*70)
    print("Entry Point Analysis - Phase 1 Demo")
    print("="*70)
    print(f"APK: {apk_path}\n")

    # Step 1: Analyze entry points
    print("[1/3] Analyzing entry points...")
    analyzer = core.analyze_entry_points_from_apk(apk_path)
    entry_points = analyzer.get_all_entry_points()

    print(f"      Found {len(entry_points)} entry points\n")

    # Step 2: Show component breakdown
    print("[2/3] Component breakdown:")
    for component_type in [
        core.ComponentType.Activity,
        core.ComponentType.Service,
        core.ComponentType.BroadcastReceiver,
        core.ComponentType.ContentProvider
    ]:
        components = [ep for ep in entry_points if ep.component_type == component_type]
        type_name = str(component_type).split('.')[-1]
        print(f"      {type_name:20s}: {len(components):3d}")

    # Step 3: Find deeplink handlers
    print("\n[3/3] Deeplink handlers:")
    deeplink_handlers = analyzer.get_deeplink_handlers()

    if deeplink_handlers:
        print(f"      Found {len(deeplink_handlers)} deeplink handler(s)\n")

        for handler in deeplink_handlers:
            print(f"      📱 {handler.class_name}")
            for intent_filter in handler.intent_filters:
                if intent_filter.is_deeplink():
                    for data in intent_filter.data_filters:
                        scheme = data.get('scheme', '')
                        host = data.get('host', '')
                        path = data.get('pathPrefix', data.get('path', ''))

                        if scheme or host:
                            url = f"{scheme}://{host}{path}"
                            print(f"         🔗 {url}")
    else:
        print("      No deeplink handlers found")

    # Bonus: Find WebView-related activities
    print("\n" + "="*70)
    print("WebView-related Activities (if any):")
    print("="*70)

    webview_activities = [
        ep for ep in entry_points
        if ep.component_type == core.ComponentType.Activity
        and ('webview' in ep.class_name.lower() or 'web' in ep.class_name.lower())
    ]

    if webview_activities:
        for activity in webview_activities:
            print(f"\n📱 {activity.class_name}")
            print(f"   Code found: {'✅' if activity.class_found else '❌'}")
            print(f"   Intent filters: {len(activity.intent_filters)}")

            # Try to get the decompiled class
            result = analyzer.get_entry_point_with_class(activity.class_name)
            if result:
                _, decompiled_class = result
                print(f"   Methods: {len(decompiled_class.methods)}")

                # Show lifecycle methods
                lifecycle = ['onCreate', 'onResume', 'onNewIntent', 'onStart', 'onPause', 'onStop']
                lifecycle_methods = [m for m in decompiled_class.methods if m.name in lifecycle]

                if lifecycle_methods:
                    print("   Lifecycle methods:")
                    for method in lifecycle_methods:
                        print(f"      - {method.name}")
    else:
        print("   No WebView-related activities found")

    print("\n" + "="*70)
    print("✅ Phase 1 Complete")
    print("="*70)

    print("\nNext steps:")
    print("  • Phase 2: Build call graph (method-to-method relationships)")
    print("  • Phase 3: Track data flow from entry points to WebView.loadUrl()")
    print("  • Phase 4: Analyze deeplink handling and intent data processing")


if __name__ == "__main__":
    main()
