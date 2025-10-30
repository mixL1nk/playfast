#!/usr/bin/env python3
"""Test WebView settings detection."""

from pathlib import Path

from playfast import ApkAnalyzer


def analyze_webview_settings(apk_path, apk_name):
    """Analyze WebView security settings."""
    print(f"\n{'=' * 70}")
    print(f"🔍 WebView Settings Analysis: {apk_name}")
    print(f"{'=' * 70}\n")

    analyzer = ApkAnalyzer(str(apk_path))

    print(f"Package: {analyzer.manifest.package_name}")
    print()

    # 1. Find WebSettings-related methods
    print("1️⃣ Finding WebSettings method calls...")
    print("-" * 70)

    # Search for methods that call WebSettings methods
    settings_methods = [
        "setJavaScriptEnabled",
        "setAllowFileAccess",
        "setAllowContentAccess",
        "setDomStorageEnabled",
        "setAllowFileAccessFromFileURLs",
        "setAllowUniversalAccessFromFileURLs",
    ]

    for method_name in settings_methods:
        # Find methods that might call this setting
        results = analyzer.find_methods(method_name=method_name, limit=5)

        if results:
            print(f"\n  ✅ {method_name}: {len(results)} usage(s) found")
            for cls, method in results[:3]:
                print(f"    - {cls.simple_name}.{method.name}()")
            if len(results) > 3:
                print(f"    ... and {len(results) - 3} more")
        else:
            print(f"  ❌ {method_name}: Not found in method names")

    # 2. Find addJavascriptInterface calls
    print("\n\n2️⃣ Finding JavaScript Interface registration...")
    print("-" * 70)

    js_interface_methods = analyzer.find_methods(
        method_name="addJavascriptInterface", limit=10
    )

    if js_interface_methods:
        print(
            f"\n  ⚠️  Found {len(js_interface_methods)} JavaScript Interface registration(s)"
        )
        print("  This exposes native code to JavaScript - HIGH SECURITY RISK!\n")

        for cls, method in js_interface_methods[:5]:
            params = ", ".join(method.parameters) if method.parameters else ""
            print(f"    - {cls.class_name}")
            print(f"      {method.name}({params})")

        if len(js_interface_methods) > 5:
            print(f"    ... and {len(js_interface_methods) - 5} more")
    else:
        print("  ✅ No JavaScript Interface usage found (safer)")

    # 3. Find WebView-related classes
    print("\n\n3️⃣ Analyzing WebView implementation classes...")
    print("-" * 70)

    webview_classes = analyzer.find_classes(name="WebView", limit=20)

    if webview_classes:
        print(f"\n  Found {len(webview_classes)} WebView-related classes\n")

        # Analyze methods in WebView classes
        for cls in webview_classes[:5]:
            print(f"  Class: {cls.simple_name}")
            print(f"    Package: {cls.package_name}")
            print(f"    Methods: {len(cls.methods)}")

            # Look for init methods that might configure WebView
            init_methods = [
                m for m in cls.methods if "init" in m.name.lower() or m.name == "<init>"
            ]
            if init_methods:
                print(f"    Init methods: {len(init_methods)}")

            # Look for security-related methods
            security_keywords = [
                "javascript",
                "settings",
                "interface",
                "security",
                "origin",
            ]
            security_methods = [
                m
                for m in cls.methods
                if any(kw in m.name.lower() for kw in security_keywords)
            ]
            if security_methods:
                print(f"    Security-related methods: {len(security_methods)}")
                for m in security_methods[:3]:
                    print(f"      - {m.name}()")

            print()

    # 4. Find WebViewClient implementations
    print("\n4️⃣ Finding WebViewClient implementations...")
    print("-" * 70)

    webview_client_classes = analyzer.find_classes(name="WebViewClient", limit=10)

    if webview_client_classes:
        print(f"\n  Found {len(webview_client_classes)} WebViewClient classes\n")

        for cls in webview_client_classes[:5]:
            print(f"  Class: {cls.simple_name}")

            # Check for SSL error handling
            ssl_methods = [
                m
                for m in cls.methods
                if "ssl" in m.name.lower() or "certificate" in m.name.lower()
            ]
            if ssl_methods:
                print(f"    ⚠️  SSL handling methods: {len(ssl_methods)}")
                for m in ssl_methods:
                    print(f"      - {m.name}()")
            else:
                print("    ✅ No SSL override methods (good)")

            print()

    # 5. Summary and Security Assessment
    print("\n" + "=" * 70)
    print("📊 Security Assessment Summary")
    print("=" * 70)

    has_js_interface = len(js_interface_methods) > 0 if js_interface_methods else False
    has_webview = len(webview_classes) > 0 if webview_classes else False

    risk_score = 0
    risks = []

    if has_js_interface:
        risk_score += 3
        risks.append("🔴 JavaScript Interface exposed (HIGH RISK)")

    if has_webview:
        risk_score += 1
        risks.append("🟡 WebView in use (requires security review)")

    print(f"\nRisk Score: {risk_score}/10")
    print("\nIdentified Risks:")
    if risks:
        for risk in risks:
            print(f"  {risk}")
    else:
        print("  ✅ No immediate security risks detected")

    print("\n⚠️  Note: Static analysis limitations:")
    print("  - Cannot determine runtime JavaScript settings")
    print("  - Cannot analyze method bytecode (not implemented)")
    print("  - Need decompilation for full analysis")

    print("\n💡 Recommendations:")
    print("  1. Review all JavaScript Interface registrations")
    print("  2. Ensure JavaScript is disabled unless required")
    print("  3. Implement SSL certificate pinning")
    print("  4. Never override onReceivedSslError() without proper validation")
    print("  5. Use WebViewAssetLoader for local content")
    print()


def main():
    print("🔐 WebView Security Settings Analysis")
    print("=" * 70)

    apks = [
        ("Baemin", Path("../samples/com.sampleapp.apk")),
        ("Instagram", Path("../samples/com.instagram.android.apk")),
    ]

    for apk_name, apk_path in apks:
        if not apk_path.exists():
            print(f"⚠️  {apk_name} not found")
            continue

        try:
            analyze_webview_settings(apk_path, apk_name)
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()

    print("=" * 70)
    print("✅ Analysis complete!")


if __name__ == "__main__":
    main()
