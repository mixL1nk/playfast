#!/usr/bin/env python3
"""Basic APK analysis example using ApkAnalyzer.

This example demonstrates how to use the high-level ApkAnalyzer API
to extract information from an APK file.
"""

from playfast import ApkAnalyzer


def main():
    # Initialize analyzer with APK file
    apk_path = "../samples/com.instagram.android.apk"
    analyzer = ApkAnalyzer(apk_path)

    print("=" * 70)
    print(f"APK Analysis: {analyzer.apk_path.name}")
    print("=" * 70)

    # Print basic info (uses __str__)
    print(analyzer)
    print()

    # Get manifest information
    manifest = analyzer.manifest
    print("📱 Manifest Details:")
    print(f"  Package:     {manifest.package_name}")
    print(f"  Version:     {manifest.version_name}")
    print(f"  Min SDK:     {manifest.min_sdk_version}")
    print(f"  Target SDK:  {manifest.target_sdk_version}")
    print()

    # Get statistics
    print("📊 APK Statistics:")
    stats = analyzer.get_statistics()
    for key, value in stats.items():
        print(f"  {key:20s}: {value}")
    print()

    # Find specific components
    print("🔍 Finding Activities:")
    activities = analyzer.find_activities(limit=5)
    for activity in activities:
        print(f"  - {activity.simple_name}")
    print()

    print("🔍 Finding Services:")
    services = analyzer.find_services(limit=5)
    for service in services:
        print(f"  - {service.simple_name}")
    print()

    # Search for specific patterns
    print("🔎 Searching for 'onCreate' methods:")
    onCreate_methods = analyzer.find_methods(method_name="onCreate", limit=5)
    for cls, method in onCreate_methods:
        params = ", ".join(method.parameters) if method.parameters else ""
        print(f"  - {cls.simple_name}.{method.name}({params})")
    print()

    # Find getter methods
    print("🔎 Searching for getter methods (no parameters):")
    getters = analyzer.find_methods(
        method_name="get",
        param_count=0,
        class_package="com.instagram",
        limit=5
    )
    for cls, method in getters:
        print(f"  - {cls.simple_name}.{method.name}() -> {method.return_type}")
    print()

    # Get app-specific classes (excluding framework)
    print("📦 Application Classes (excluding android/androidx):")
    app_classes = analyzer.get_app_classes(limit=10)
    print(f"  Found {len(app_classes)} app-specific classes")
    print("  Sample classes:")
    for cls in app_classes[:5]:
        print(f"  - {cls.class_name}")
    print()

    print("=" * 70)
    print("✅ Analysis complete!")


if __name__ == "__main__":
    main()
