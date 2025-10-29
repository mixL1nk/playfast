#!/usr/bin/env python3
"""APK dependency and package analysis example.

This example demonstrates how to analyze an APK's dependencies,
including:
- All packages used in the app
- Third-party libraries
- WebView usage
- Package distribution
"""

from playfast import ApkAnalyzer


def analyze_packages(analyzer: ApkAnalyzer):
    """Analyze all packages in the APK."""
    print("📦 Package Analysis")
    print("=" * 70)

    packages = analyzer.get_all_packages()
    print(f"Total unique packages: {len(packages):,}")
    print()

    # Show package groups
    print("Package Distribution (Top 20):")
    print("-" * 70)
    groups = analyzer.get_package_groups()

    for top_level, pkgs in sorted(groups.items(), key=lambda x: -len(x[1]))[:20]:
        print(f"  {top_level:35s} {len(pkgs):5,} packages")

    print()


def analyze_third_party_libs(analyzer: ApkAnalyzer):
    """Analyze third-party library usage."""
    print("📚 Third-Party Library Analysis")
    print("=" * 70)

    libs = analyzer.get_third_party_libraries()

    if not libs:
        print("No third-party libraries detected")
        print()
        return

    print(f"Detected {len(libs)} third-party libraries:")
    print()

    # Group by vendor
    vendors = {
        'Google/Android': [],
        'Facebook/Meta': [],
        'Kotlin/JetBrains': [],
        'Other': []
    }

    for lib, count in libs.items():
        if any(lib.startswith(p) for p in ['com.google', 'androidx', 'android.support', 'com.android']):
            vendors['Google/Android'].append((lib, count))
        elif any(lib.startswith(p) for p in ['com.facebook', 'com.meta', 'com.fbpay', 'com.facebookpay']):
            vendors['Facebook/Meta'].append((lib, count))
        elif any(lib.startswith(p) for p in ['kotlinx', 'kotlin', 'org.jetbrains']):
            vendors['Kotlin/JetBrains'].append((lib, count))
        else:
            vendors['Other'].append((lib, count))

    for vendor, libs_list in vendors.items():
        if libs_list:
            print(f"{vendor}:")
            for lib, count in sorted(libs_list, key=lambda x: -x[1]):
                print(f"  - {lib:40s} {count:4,} packages")
            print()


def analyze_webview_usage(analyzer: ApkAnalyzer):
    """Analyze WebView usage."""
    print("🌐 WebView Usage Analysis")
    print("=" * 70)

    usage = analyzer.find_webview_usage()

    print(f"WebView classes found: {usage['class_count']}")
    print(f"Methods using WebView: {usage['method_count']}")
    print()

    if usage['classes']:
        print("WebView classes (top 10):")
        for cls in usage['classes'][:10]:
            print(f"  - {cls}")
        if len(usage['classes']) > 10:
            print(f"  ... and {len(usage['classes']) - 10} more")
        print()

    if usage['methods']:
        print("Methods using WebView (top 10):")
        for method_info in usage['methods'][:10]:
            params = ', '.join(method_info['parameters']) if method_info['parameters'] else ''
            print(f"  - {method_info['class']}")
            print(f"    {method_info['method']}({params}) -> {method_info['return_type']}")
        if len(usage['methods']) > 10:
            print(f"  ... and {len(usage['methods']) - 10} more")
        print()

    # Security recommendations
    if usage['class_count'] > 0 or usage['method_count'] > 0:
        print("⚠️  WebView Security Recommendations:")
        print("  1. Disable JavaScript if not needed: webView.getSettings().setJavaScriptEnabled(false)")
        print("  2. Disable file access: webView.getSettings().setAllowFileAccess(false)")
        print("  3. Implement secure WebViewClient with SSL error handling")
        print("  4. Validate all URLs before loading")
        print("  5. Use HTTPS for all web content")
        print()


def find_specific_features(analyzer: ApkAnalyzer):
    """Find usage of specific Android features."""
    print("🔍 Specific Feature Analysis")
    print("=" * 70)

    features = {
        'Camera': 'Camera',
        'Location': 'Location',
        'Bluetooth': 'Bluetooth',
        'NFC': 'Nfc',
        'Biometric': 'Biometric',
        'MediaPlayer': 'MediaPlayer',
        'Notification': 'Notification',
    }

    for feature_name, class_pattern in features.items():
        classes = analyzer.find_classes(name=class_pattern, limit=1)
        status = "✅" if classes else "❌"
        print(f"  {status} {feature_name:15s}: {'Used' if classes else 'Not detected'}")

    print()


def analyze_app_vs_dependencies(analyzer: ApkAnalyzer):
    """Analyze distribution of app code vs dependencies."""
    print("📊 Code Distribution Analysis")
    print("=" * 70)

    manifest = analyzer.manifest
    app_package_prefix = '.'.join(manifest.package_name.split('.')[:2])

    classes = analyzer.load_classes()

    app_classes = []
    dep_classes = []

    for cls in classes:
        if cls.package_name.startswith(app_package_prefix):
            app_classes.append(cls)
        else:
            dep_classes.append(cls)

    total_classes = len(classes)
    app_pct = len(app_classes) / total_classes * 100
    dep_pct = len(dep_classes) / total_classes * 100

    print(f"Total classes:       {total_classes:8,}")
    print(f"App classes:         {len(app_classes):8,} ({app_pct:5.1f}%)")
    print(f"Dependency classes:  {len(dep_classes):8,} ({dep_pct:5.1f}%)")
    print()

    # Method counts
    app_methods = sum(len(cls.methods) for cls in app_classes)
    dep_methods = sum(len(cls.methods) for cls in dep_classes)
    total_methods = app_methods + dep_methods

    app_method_pct = app_methods / total_methods * 100 if total_methods > 0 else 0
    dep_method_pct = dep_methods / total_methods * 100 if total_methods > 0 else 0

    print(f"Total methods:       {total_methods:8,}")
    print(f"App methods:         {app_methods:8,} ({app_method_pct:5.1f}%)")
    print(f"Dependency methods:  {dep_methods:8,} ({dep_method_pct:5.1f}%)")
    print()

    if dep_pct > 80:
        print("⚠️  High dependency ratio (>80%)")
        print("   Consider:")
        print("   - Enabling ProGuard/R8 for code shrinking")
        print("   - Removing unused dependencies")
        print("   - Using lighter-weight alternatives")
    elif dep_pct > 60:
        print("⚡ Moderate dependency ratio (60-80%)")
        print("   Monitor dependencies and keep them updated")
    else:
        print("✅ Healthy code-to-dependency ratio")

    print()


def generate_dependency_report(analyzer: ApkAnalyzer):
    """Generate comprehensive dependency report."""
    print("=" * 70)
    print("📋 DEPENDENCY ANALYSIS SUMMARY")
    print("=" * 70)

    manifest = analyzer.manifest
    packages = analyzer.get_all_packages()
    libs = analyzer.get_third_party_libraries()
    webview = analyzer.find_webview_usage()

    print(f"APK:     {analyzer.apk_path.name}")
    print(f"Package: {manifest.package_name}")
    print(f"Version: {manifest.version_name}")
    print()

    print("Dependencies Overview:")
    print(f"  📦 Total packages:        {len(packages):,}")
    print(f"  📚 Third-party libraries: {len(libs)}")
    print(f"  🌐 WebView usage:         {'Yes' if webview['class_count'] > 0 else 'No'}")
    print()

    # Top dependencies
    if libs:
        print("Top 5 Dependencies by package count:")
        for lib, count in sorted(libs.items(), key=lambda x: -x[1])[:5]:
            print(f"  - {lib:35s} {count:4,} packages")
        print()

    print("Recommendations:")
    if len(libs) > 20:
        print("  ⚠️  Large number of dependencies - review for necessity")
    if webview['class_count'] > 0:
        print("  🔒 WebView detected - ensure proper security measures")
    print("  ✅ Keep all dependencies updated regularly")
    print("  ✅ Use dependency scanning tools (e.g., OWASP Dependency Check)")


def main():
    apk_path = "../samples/com.instagram.android.apk"

    print("🔍 APK Dependency & Package Analysis Tool")
    print("=" * 70)

    try:
        analyzer = ApkAnalyzer(apk_path)
        print(f"Loading: {analyzer.apk_path.name}")
        print()

        analyze_packages(analyzer)
        analyze_third_party_libs(analyzer)
        analyze_webview_usage(analyzer)
        find_specific_features(analyzer)
        analyze_app_vs_dependencies(analyzer)
        generate_dependency_report(analyzer)

        print("=" * 70)
        print("✅ Analysis complete!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
