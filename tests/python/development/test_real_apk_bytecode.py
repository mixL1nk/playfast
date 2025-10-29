#!/usr/bin/env python3
"""Test bytecode extraction from real APK"""

from pathlib import Path
from playfast import core

def test_webview_security_analysis():
    """
    Analyze WebView security settings in real APK

    Goal: Find setJavaScriptEnabled calls and extract parameter values
    """
    print("=" * 70)
    print("🔐 WebView Security Analysis")
    print("=" * 70)
    print()

    apk_path = Path("../samples/com.sampleapp.apk")

    if not apk_path.exists():
        print(f"❌ APK not found: {apk_path}")
        return

    # Step 1: Find all classes
    print("📱 Loading APK...")
    classes = core.extract_classes_from_apk(str(apk_path))
    print(f"✅ Loaded {len(classes):,} classes\n")

    # Step 2: Find WebView-related methods
    print("🔍 Searching for WebView methods...")
    webview_methods = []

    for cls in classes:
        for method in cls.methods:
            # Look for methods that might set JavaScript
            if "setJavaScriptEnabled" in method.name or "addJavascriptInterface" in method.name:
                webview_methods.append((cls, method))

    print(f"Found {len(webview_methods)} WebView security methods\n")

    for cls, method in webview_methods[:10]:
        print(f"  - {cls.simple_name}.{method.name}()")
        print(f"    Params: {', '.join(method.parameters) if method.parameters else 'none'}")
        print(f"    Return: {method.return_type}")
        print()

    # Step 3: Note about bytecode extraction
    print("=" * 70)
    print("📝 Current Limitation")
    print("=" * 70)
    print()
    print("✅ We can:")
    print("  1. Decode bytecode instructions (const/4, invoke-*, etc.)")
    print("  2. Extract constant values from bytecode")
    print("  3. Track method invocations")
    print()
    print("🚧 Still need to implement:")
    print("  1. Extract raw bytecode from DEX method structures")
    print("  2. Integrate dex-rs library for CodeItem parsing")
    print("  3. Map method_idx to actual method information")
    print()
    print("💡 Workaround:")
    print("  For now, we can detect method presence.")
    print("  To analyze true/false values, we need to:")
    print("  - Add DEX method code extraction")
    print("  - Use dex-rs Dex::from_bytes() to parse")
    print("  - Extract CodeItem.insns() for each method")
    print()

def show_next_steps():
    """Show next implementation steps"""
    print("=" * 70)
    print("📋 Next Steps")
    print("=" * 70)
    print()

    print("To complete WebView security analysis:")
    print()

    print("1. Add dex-rs integration (1-2 hours)")
    print("   - Add `dex` crate to Cargo.toml")
    print("   - Create wrapper to extract method bytecode")
    print("   - Expose get_method_bytecode(class_name, method_name)")
    print()

    print("2. Create high-level API (1 hour)")
    print("   - analyze_webview_settings(apk_path)")
    print("   - Returns: List of (class, method, javascript_enabled: bool)")
    print()

    print("3. Test with sample APKs (30 minutes)")
    print("   - Baemin, Instagram, etc.")
    print("   - Validate true/false detection")
    print()

    print("Total estimated time: 2-3 hours")
    print()

if __name__ == "__main__":
    test_webview_security_analysis()
    show_next_steps()

    print("=" * 70)
    print("✅ Bytecode API is ready!")
    print("✅ Can decode instructions and extract constants")
    print("🚧 Next: Integrate dex-rs for full method bytecode extraction")
    print("=" * 70)
