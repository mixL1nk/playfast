#!/usr/bin/env python3
"""
Test Entry Point Analysis - Phase 1 of WebView Call Flow

This tests the ability to:
1. Link AndroidManifest.xml components with DEX classes
2. Identify deeplink handlers
3. Find which components have associated code
"""

import os
import sys
from playfast import core


def test_basic_entry_point_analysis():
    """Test basic entry point analysis from APK"""
    # Use APK path from argument or skip test
    if len(sys.argv) > 1:
        apk_path = sys.argv[1]
    else:
        print("\n⚠️  No APK path provided. Usage: python test_entry_point_analysis.py <path_to_apk>")
        print("Skipping test...")
        return

    if not os.path.exists(apk_path):
        print(f"\n❌ APK not found: {apk_path}")
        return

    print("\n" + "="*60)
    print("Phase 1: Entry Point Analysis Test")
    print("="*60)

    # Analyze entry points
    analyzer = core.analyze_entry_points_from_apk(apk_path)
    entry_points = analyzer.get_all_entry_points()

    print(f"\n📱 Total entry points found: {len(entry_points)}")

    # Group by component type
    activities = [ep for ep in entry_points if ep.component_type == core.ComponentType.Activity]
    services = [ep for ep in entry_points if ep.component_type == core.ComponentType.Service]
    receivers = [ep for ep in entry_points if ep.component_type == core.ComponentType.BroadcastReceiver]
    providers = [ep for ep in entry_points if ep.component_type == core.ComponentType.ContentProvider]

    print(f"\n📊 Component breakdown:")
    print(f"  Activities: {len(activities)}")
    print(f"  Services: {len(services)}")
    print(f"  BroadcastReceivers: {len(receivers)}")
    print(f"  ContentProviders: {len(providers)}")

    # Show activities with details
    print(f"\n🎯 Activities:")
    for ep in activities:
        status = "✅ Code found" if ep.class_found else "❌ Code missing"
        deeplink = "🔗 Deeplink" if ep.is_deeplink_handler else ""
        intent_count = len(ep.intent_filters)

        print(f"  {ep.class_name}")
        print(f"    {status}  {deeplink}")
        print(f"    Intent filters: {intent_count}")

        for intent_filter in ep.intent_filters[:3]:  # Show first 3
            if intent_filter.is_launcher():
                print(f"      🚀 LAUNCHER")
            if intent_filter.is_deeplink():
                print(f"      🔗 DEEPLINK:")
                for data in intent_filter.data_filters:
                    scheme = data.get('scheme', '')
                    host = data.get('host', '')
                    if scheme or host:
                        print(f"         {scheme}://{host}")

    # Find deeplink handlers
    print(f"\n🔗 Deeplink handlers:")
    deeplink_handlers = analyzer.get_deeplink_handlers()
    print(f"  Found {len(deeplink_handlers)} deeplink handler(s)")

    for handler in deeplink_handlers:
        print(f"\n  📍 {handler.class_name}")
        for intent_filter in handler.intent_filters:
            if intent_filter.is_deeplink():
                for data in intent_filter.data_filters:
                    scheme = data.get('scheme', '')
                    host = data.get('host', '')
                    path_prefix = data.get('pathPrefix', '')
                    if scheme or host:
                        url = f"{scheme}://{host}{path_prefix}"
                        print(f"     {url}")

    # Test get_entry_point_with_class for WebView activity
    print(f"\n🔍 Looking for WebView-related activities...")
    for ep in activities:
        if 'webview' in ep.class_name.lower() or 'web' in ep.class_name.lower():
            print(f"\n  Found: {ep.class_name}")

            result = analyzer.get_entry_point_with_class(ep.class_name)
            if result:
                entry_point, decompiled_class = result
                print(f"    Methods: {len(decompiled_class.methods)}")

                # Show lifecycle methods
                lifecycle_methods = [m for m in decompiled_class.methods
                                    if m.name in ['onCreate', 'onResume', 'onNewIntent', 'onStart']]
                if lifecycle_methods:
                    print(f"    Lifecycle methods found:")
                    for method in lifecycle_methods:
                        print(f"      - {method.name}")

    print("\n" + "="*60)
    print("✅ Phase 1 Test Complete")
    print("="*60)


def test_deeplink_detection():
    """Test deeplink detection accuracy"""
    if len(sys.argv) > 1:
        apk_path = sys.argv[1]
    else:
        return

    if not os.path.exists(apk_path):
        return

    print("\n" + "="*60)
    print("Deeplink Detection Test")
    print("="*60)

    analyzer = core.analyze_entry_points_from_apk(apk_path)
    deeplink_handlers = analyzer.get_deeplink_handlers()

    print(f"\nDeeplink handlers: {len(deeplink_handlers)}")

    for handler in deeplink_handlers:
        print(f"\n📱 {handler.class_name}")
        print(f"   Filters: {len(handler.intent_filters)}")

        for intent_filter in handler.intent_filters:
            if intent_filter.is_deeplink():
                print(f"   Actions: {intent_filter.actions}")
                print(f"   Categories: {intent_filter.categories}")
                print(f"   Data filters: {len(intent_filter.data_filters)}")

                for data in intent_filter.data_filters:
                    print(f"     {data}")


if __name__ == "__main__":
    test_basic_entry_point_analysis()
    print("\n")
    test_deeplink_detection()
