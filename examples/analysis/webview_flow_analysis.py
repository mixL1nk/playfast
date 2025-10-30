#!/usr/bin/env python3
"""
Integration test for WebView Flow Analysis

Tests the complete pipeline from entry point analysis to data flow tracking.
"""

import os
import sys
from playfast import core


def test_phase1_entry_point_analysis():
    """Test Phase 1: Entry point analysis"""
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        print("⏭️  Skipping Phase 1 test (no APK provided)")
        return False

    apk_path = sys.argv[1]
    print("\n" + "="*60)
    print("Phase 1: Entry Point Analysis")
    print("="*60)

    try:
        analyzer = core.analyze_entry_points_from_apk(apk_path)
        entry_points = analyzer.get_all_entry_points()

        print(f"✅ Found {len(entry_points)} entry points")

        deeplink_handlers = analyzer.get_deeplink_handlers()
        print(f"✅ Found {len(deeplink_handlers)} deeplink handlers")

        return True
    except Exception as e:
        print(f"❌ Phase 1 failed: {e}")
        return False


def test_phase2_call_graph():
    """Test Phase 2: Call graph construction"""
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        print("⏭️  Skipping Phase 2 test (no APK provided)")
        return False

    apk_path = sys.argv[1]
    print("\n" + "="*60)
    print("Phase 2: Call Graph Construction")
    print("="*60)

    try:
        # Build with no filter for comprehensive test
        call_graph = core.build_call_graph_from_apk(apk_path, None)
        stats = call_graph.get_stats()

        print(f"✅ Built call graph: {stats['total_methods']} methods, {stats['total_edges']} edges")

        # Test method finding
        webview_methods = call_graph.find_methods("WebView")
        print(f"✅ Found {len(webview_methods)} WebView-related methods")

        return True
    except Exception as e:
        print(f"❌ Phase 2 failed: {e}")
        return False


def test_phase3_webview_flow():
    """Test Phase 3: WebView flow analysis"""
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        print("⏭️  Skipping Phase 3 test (no APK provided)")
        return False

    apk_path = sys.argv[1]
    print("\n" + "="*60)
    print("Phase 3: WebView Flow Analysis")
    print("="*60)

    try:
        # Quick method
        flows = core.analyze_webview_flows_from_apk(apk_path, max_depth=8)
        print(f"✅ Quick analysis: {len(flows)} flows found")

        # Detailed method
        analyzer = core.create_webview_analyzer_from_apk(apk_path)
        stats = analyzer.get_stats()

        print(f"✅ Analyzer created:")
        print(f"   Entry points: {stats.get('entry_points', 0)}")
        print(f"   Deeplink handlers: {stats.get('deeplink_handlers', 0)}")
        print(f"   WebView methods: {stats.get('webview_methods', 0)}")

        # Analyze flows
        all_flows = analyzer.analyze_flows(max_depth=8)
        print(f"✅ Detailed analysis: {len(all_flows)} flows found")

        # Find deeplink flows
        deeplink_flows = analyzer.find_deeplink_flows(max_depth=8)
        print(f"✅ Deeplink flows: {len(deeplink_flows)} found")

        # Analyze data flows
        if all_flows:
            data_flows = analyzer.analyze_data_flows(all_flows)
            high_conf = [df for df in data_flows if df.confidence >= 0.7]
            print(f"✅ Data flows: {len(data_flows)} total, {len(high_conf)} high confidence")

        return True
    except Exception as e:
        print(f"❌ Phase 3 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_functionality():
    """Test basic API functionality without APK"""
    print("\n" + "="*60)
    print("API Functionality Tests")
    print("="*60)

    try:
        # Test that classes are importable
        from playfast.core import (
            EntryPoint,
            ComponentType,
            CallGraph,
            CallPath,
            MethodCall,
            WebViewFlow,
            DataFlow,
            WebViewFlowAnalyzer,
        )

        print("✅ All classes importable")

        # Test that functions exist
        assert hasattr(core, 'analyze_entry_points_from_apk')
        assert hasattr(core, 'build_call_graph_from_apk')
        assert hasattr(core, 'analyze_webview_flows_from_apk')
        assert hasattr(core, 'create_webview_analyzer_from_apk')

        print("✅ All functions available")

        return True
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def main():
    print("\n" + "="*60)
    print("WebView Flow Analysis - Integration Test")
    print("="*60)

    if len(sys.argv) < 2:
        print("\n⚠️  No APK provided")
        print("Usage: python test_webview_flow_integration.py <path_to_apk>")
        print("\nRunning API tests only...\n")

    results = {
        "API Functionality": test_api_functionality(),
    }

    if len(sys.argv) >= 2 and os.path.exists(sys.argv[1]):
        apk_path = sys.argv[1]
        print(f"\n📱 Testing with APK: {apk_path}")

        results["Phase 1: Entry Points"] = test_phase1_entry_point_analysis()
        results["Phase 2: Call Graph"] = test_phase2_call_graph()
        results["Phase 3: WebView Flow"] = test_phase3_webview_flow()

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "="*60)
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total} passed)")
    print("="*60)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
