#!/usr/bin/env python3
"""Security audit example using ApkAnalyzer.

This example demonstrates how to perform basic security checks
on an APK file, including:
- Dangerous permissions
- Exported components
- Crypto usage patterns
- Network security
"""

from playfast import ApkAnalyzer


# Dangerous permissions that require special attention
DANGEROUS_PERMISSIONS = {
    "android.permission.READ_CONTACTS",
    "android.permission.WRITE_CONTACTS",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.CAMERA",
    "android.permission.RECORD_AUDIO",
    "android.permission.READ_PHONE_STATE",
    "android.permission.CALL_PHONE",
    "android.permission.READ_SMS",
    "android.permission.SEND_SMS",
    "android.permission.RECEIVE_SMS",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
}


def check_permissions(analyzer: ApkAnalyzer):
    """Check for dangerous permissions."""
    print("🔒 Permission Analysis")
    print("-" * 70)

    manifest = analyzer.manifest
    dangerous = []

    for perm in manifest.permissions:
        if perm in DANGEROUS_PERMISSIONS:
            dangerous.append(perm)

    print(f"Total permissions: {len(manifest.permissions)}")
    print(f"Dangerous permissions: {len(dangerous)}")

    if dangerous:
        print("\n⚠️  Dangerous permissions found:")
        for perm in dangerous:
            print(f"  - {perm}")
    else:
        print("✅ No dangerous permissions found")

    print()


def check_crypto_usage(analyzer: ApkAnalyzer):
    """Check for cryptographic API usage."""
    print("🔐 Cryptography Usage Analysis")
    print("-" * 70)

    # Search for crypto-related classes
    crypto_patterns = [
        ("javax.crypto", "javax.crypto package"),
        ("java.security", "java.security package"),
        ("Cipher", "Cipher classes"),
        ("MessageDigest", "Hash functions"),
        ("SecretKey", "Secret key usage"),
    ]

    for package_or_class, description in crypto_patterns:
        if "." in package_or_class and package_or_class.startswith("javax") or package_or_class.startswith("java"):
            # Package search
            results = analyzer.find_classes(package=package_or_class, limit=1)
        else:
            # Class name search
            results = analyzer.find_classes(name=package_or_class, limit=1)

        if results:
            print(f"✅ {description} detected")
        else:
            print(f"❌ {description} not detected")

    print()


def check_network_usage(analyzer: ApkAnalyzer):
    """Check for network-related classes and methods."""
    print("🌐 Network Security Analysis")
    print("-" * 70)

    # Check for HTTP (non-secure) usage
    http_classes = analyzer.find_classes(name="HttpURLConnection", limit=5)
    if http_classes:
        print(f"⚠️  Found {len(http_classes)} HttpURLConnection usage(s)")
        print("    Consider using HTTPS instead")
    else:
        print("✅ No HttpURLConnection usage detected")

    # Check for HTTPS
    https_classes = analyzer.find_classes(name="HttpsURLConnection", limit=5)
    if https_classes:
        print(f"✅ Found {len(https_classes)} HttpsURLConnection usage(s)")
    else:
        print("❌ No HttpsURLConnection usage detected")

    # Check for WebView
    webview_classes = analyzer.find_classes(name="WebView", limit=5)
    if webview_classes:
        print(f"⚠️  Found {len(webview_classes)} WebView usage(s)")
        print("    Ensure JavaScript and file access are properly secured")
    else:
        print("✅ No WebView usage detected")

    print()


def check_component_security(analyzer: ApkAnalyzer):
    """Check for exported components."""
    print("📱 Component Security Analysis")
    print("-" * 70)

    manifest = analyzer.manifest

    print(f"Total Activities: {len(manifest.activities)}")
    print(f"Total Services:   {len(manifest.services)}")
    print(f"Total Receivers:  {len(manifest.receivers)}")
    print(f"Total Providers:  {len(manifest.providers)}")

    print("\n💡 Note: Check AndroidManifest.xml for exported=\"true\" attribute")
    print("   Exported components should be properly secured with permissions")

    print()


def generate_report(analyzer: ApkAnalyzer):
    """Generate a summary security report."""
    print("=" * 70)
    print("📋 SECURITY AUDIT SUMMARY")
    print("=" * 70)

    manifest = analyzer.manifest

    print(f"APK:     {analyzer.apk_path.name}")
    print(f"Package: {manifest.package_name}")
    print(f"Version: {manifest.version_name}")
    print()

    # Count dangerous permissions
    dangerous_count = sum(
        1 for perm in manifest.permissions
        if perm in DANGEROUS_PERMISSIONS
    )

    print("Security Findings:")
    if dangerous_count > 0:
        print(f"  ⚠️  {dangerous_count} dangerous permission(s) requested")
    else:
        print("  ✅ No dangerous permissions")

    print(f"  ℹ️  {len(manifest.activities)} activities")
    print(f"  ℹ️  {len(manifest.services)} services")
    print(f"  ℹ️  {len(manifest.receivers)} broadcast receivers")
    print(f"  ℹ️  {len(manifest.providers)} content providers")

    print()
    print("Recommendations:")
    print("  1. Review all dangerous permissions for necessity")
    print("  2. Ensure exported components are properly secured")
    print("  3. Use HTTPS for all network communications")
    print("  4. Implement certificate pinning for sensitive data")
    print("  5. Obfuscate code using ProGuard/R8")


def main():
    apk_path = "../samples/com.instagram.android.apk"

    print("🔍 APK Security Audit Tool")
    print("=" * 70)

    try:
        analyzer = ApkAnalyzer(apk_path)

        check_permissions(analyzer)
        check_crypto_usage(analyzer)
        check_network_usage(analyzer)
        check_component_security(analyzer)
        generate_report(analyzer)

        print()
        print("=" * 70)
        print("✅ Security audit complete!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
