#!/usr/bin/env python3
"""Test WebView search on com.sampleapp.apk"""

from pathlib import Path
from playfast import ApkAnalyzer
import time

def main():
    apk_path = Path("../samples/com.sampleapp.apk")

    if not apk_path.exists():
        print(f"❌ APK file not found: {apk_path}")
        return

    print("=" * 70)
    print(f"🔍 WebView Analysis: {apk_path.name}")
    print("=" * 70)

    # Initialize analyzer
    start = time.time()
    analyzer = ApkAnalyzer(str(apk_path))
    init_time = time.time() - start

    print(f"\n✅ APK loaded in {init_time*1000:.2f}ms")
    print()

    # Basic info
    manifest = analyzer.manifest
    print("📱 Basic Information:")
    print(f"  Package:     {manifest.package_name}")
    print(f"  Version:     {manifest.version_name}")
    print(f"  DEX files:   {analyzer.dex_count}")
    print()

    # Get statistics
    stats = analyzer.get_statistics()
    print("📊 Statistics:")
    print(f"  Classes:     {stats['class_count']:,}")
    print(f"  Methods:     {stats['method_count']:,}")
    print(f"  Activities:  {stats['activity_count']}")
    print(f"  Services:    {stats['service_count']}")
    print()

    # WebView analysis
    print("🌐 WebView Usage Analysis:")
    print("-" * 70)

    start = time.time()
    webview_usage = analyzer.find_webview_usage()
    search_time = time.time() - start

    print(f"Search completed in {search_time*1000:.2f}ms")
    print()

    print(f"WebView Classes:  {webview_usage['class_count']}")
    print(f"WebView Methods:  {webview_usage['method_count']}")
    print()

    if webview_usage['classes']:
        print("📋 WebView Classes:")
        for cls in webview_usage['classes']:
            print(f"  - {cls}")
        print()

    if webview_usage['methods']:
        print(f"📋 Methods using WebView (showing first 20):")
        for i, method_info in enumerate(webview_usage['methods'][:20], 1):
            params = ', '.join(method_info['parameters']) if method_info['parameters'] else ''
            print(f"\n  {i}. {method_info['class']}")
            print(f"     {method_info['method']}({params})")
            print(f"     -> {method_info['return_type']}")

        if len(webview_usage['methods']) > 20:
            print(f"\n  ... and {len(webview_usage['methods']) - 20} more methods")
        print()

    # Package analysis
    print("📦 Package Analysis:")
    print("-" * 70)

    packages = analyzer.get_all_packages()
    print(f"Total packages: {len(packages):,}")
    print()

    groups = analyzer.get_package_groups()
    print("Top 10 package groups:")
    for domain, pkgs in sorted(groups.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"  {domain:35s} {len(pkgs):4,} packages")
    print()

    # Third-party libraries
    libs = analyzer.get_third_party_libraries()
    if libs:
        print("📚 Third-Party Libraries:")
        print(f"Detected {len(libs)} libraries:")
        for lib, count in sorted(libs.items(), key=lambda x: -x[1])[:15]:
            print(f"  - {lib:40s} {count:4,} packages")
        print()

    # Security recommendations
    if webview_usage['class_count'] > 0 or webview_usage['method_count'] > 0:
        print("⚠️  WebView Security Recommendations:")
        print("-" * 70)
        print("  1. ✅ Disable JavaScript if not needed:")
        print("     webView.getSettings().setJavaScriptEnabled(false)")
        print()
        print("  2. ✅ Disable file access:")
        print("     webView.getSettings().setAllowFileAccess(false)")
        print()
        print("  3. ✅ Implement secure WebViewClient:")
        print("     - Override onReceivedSslError() properly")
        print("     - Validate SSL certificates")
        print()
        print("  4. ✅ Validate all URLs before loading:")
        print("     - Whitelist allowed domains")
        print("     - Block dangerous schemes (file://, javascript:)")
        print()
        print("  5. ✅ Use HTTPS for all content")
        print()
    else:
        print("✅ No WebView usage detected - Good!")
        print()

    print("=" * 70)
    print("✅ Analysis complete!")

if __name__ == "__main__":
    main()
