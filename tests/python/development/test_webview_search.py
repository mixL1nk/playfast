#!/usr/bin/env python3
"""Test finding WebView usage in APK."""

from pathlib import Path

from playfast import ApkAnalyzer


def main():
    apk_path = Path("../samples/com.instagram.android.apk")
    analyzer = ApkAnalyzer(str(apk_path))

    print("🔍 WebView Usage Analysis")
    print("=" * 70)

    # 1. Find classes that extend WebView
    print("\n1. Classes extending WebView:")
    webview_classes = analyzer.find_classes(name="WebView", limit=20)
    print(f"   Found {len(webview_classes)} WebView classes")
    for cls in webview_classes[:10]:
        print(f"   - {cls.class_name}")
        if cls.superclass:
            print(f"     Extends: {cls.superclass}")

    # 2. Find WebView initialization methods
    print("\n2. Methods with WebView parameters:")
    webview_methods = analyzer.find_methods(
        method_name="",  # All methods
        class_package="com.instagram",
        limit=50,
    )

    webview_usage_count = 0
    for cls, method in webview_methods:
        # Check if method uses WebView in parameters or return type
        has_webview = False
        if "WebView" in method.return_type:
            has_webview = True
        for param in method.parameters:
            if "WebView" in param:
                has_webview = True
                break

        if has_webview:
            webview_usage_count += 1
            if webview_usage_count <= 10:
                params = ", ".join(method.parameters) if method.parameters else ""
                print(
                    f"   - {cls.simple_name}.{method.name}({params}) -> {method.return_type}"
                )

    print(f"\n   Total methods using WebView: {webview_usage_count}")

    # 3. Find all packages used in the app
    print("\n3. Analyzing all packages:")
    all_classes = analyzer.load_classes()

    packages = set()
    for cls in all_classes:
        if cls.package_name:
            packages.add(cls.package_name)

    print(f"   Total unique packages: {len(packages)}")

    # Group by top-level domain
    package_groups = {}
    for pkg in packages:
        parts = pkg.split(".")
        if len(parts) >= 2:
            top_level = f"{parts[0]}.{parts[1]}"
        else:
            top_level = parts[0]

        if top_level not in package_groups:
            package_groups[top_level] = []
        package_groups[top_level].append(pkg)

    print("\n   Package groups:")
    for top_level, pkgs in sorted(package_groups.items(), key=lambda x: -len(x[1]))[
        :20
    ]:
        print(f"   - {top_level:30s} ({len(pkgs):4d} packages)")


if __name__ == "__main__":
    main()
