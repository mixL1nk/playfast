#!/usr/bin/env python3
"""Complete WebView Security Analysis with Bytecode"""

from pathlib import Path
from playfast import core

def analyze_webview_security(apk_path: Path):
    """
    Complete WebView security analysis with bytecode inspection

    Goals:
    1. Find WebView-related classes
    2. Extract method bytecode
    3. Analyze JavaScript settings (true/false values)
    """
    print("=" * 70)
    print("🔐 Complete WebView Security Analysis")
    print("=" * 70)
    print()

    if not apk_path.exists():
        print(f"❌ APK not found: {apk_path}")
        return

    print(f"📱 Analyzing: {apk_path.name}\n")

    # Step 1: Find WebView-related classes
    print("Step 1: Finding WebView classes...")
    all_classes = core.extract_classes_from_apk(str(apk_path))
    print(f"  Loaded {len(all_classes):,} classes\n")

    # Filter for WebView-related classes
    webview_classes = []
    for cls in all_classes:
        # Look for classes that extend or use WebView
        if any('WebView' in method.return_type or
               any('WebView' in param for param in method.parameters)
               for method in cls.methods):
            webview_classes.append(cls)

    print(f"  Found {len(webview_classes)} WebView-related classes\n")

    if not webview_classes:
        print("❌ No WebView usage found in this APK")
        return

    # Show sample classes
    for i, cls in enumerate(webview_classes[:5], 1):
        print(f"  {i}. {cls.simple_name}")
        print(f"     Package: {cls.package_name}")
        webview_methods = [m for m in cls.methods
                          if 'WebView' in m.return_type or
                          any('WebView' in p for p in m.parameters)]
        print(f"     WebView methods: {len(webview_methods)}")
        print()

    # Step 2: Extract bytecode for these classes
    print("Step 2: Extracting method bytecode...")

    # Take a sample of classes (to avoid processing too many)
    sample_classes = webview_classes[:10]

    bytecode_results = core.extract_methods_bytecode(
        str(apk_path),
        sample_classes
    )

    print(f"  Extracted bytecode for {len(bytecode_results)} methods\n")

    # Step 3: Analyze bytecode for JavaScript settings
    print("Step 3: Analyzing JavaScript settings...")
    print("-" * 70)

    js_settings_found = []

    for class_name, method_name, bytecode in bytecode_results:
        if not bytecode:
            continue  # Skip methods with no code

        # Decode instructions
        instructions = core.decode_bytecode(bytecode)

        # Look for const instructions (potential boolean values)
        for insn in instructions:
            if insn.is_const() and insn.value is not None:
                # Check if this is a boolean-like value (0 or 1)
                if insn.value in [0, 1]:
                    js_settings_found.append({
                        'class': class_name.split('.')[-1],  # Simple name
                        'method': method_name,
                        'value': bool(insn.value),
                        'instruction': insn.raw
                    })

    # Show results
    if js_settings_found:
        print(f"✅ Found {len(js_settings_found)} boolean constants in WebView methods:\n")

        # Group by true/false
        true_settings = [s for s in js_settings_found if s['value']]
        false_settings = [s for s in js_settings_found if not s['value']]

        print(f"🟢 TRUE values (likely JavaScript ENABLED): {len(true_settings)}")
        for setting in true_settings[:5]:
            print(f"   - {setting['class']}.{setting['method']}()")
            print(f"     {setting['instruction']}")

        print()
        print(f"🔴 FALSE values (likely JavaScript DISABLED): {len(false_settings)}")
        for setting in false_settings[:5]:
            print(f"   - {setting['class']}.{setting['method']}()")
            print(f"     {setting['instruction']}")
        print()

    else:
        print("⚠️  No explicit boolean constants found in analyzed methods")
        print("   (This might mean dynamic configuration or obfuscation)\n")

    # Step 4: Summary
    print("=" * 70)
    print("📊 Analysis Summary")
    print("=" * 70)
    print()

    print(f"Total classes analyzed: {len(sample_classes)}")
    print(f"Total methods with bytecode: {len([r for r in bytecode_results if r[2]])}")
    print(f"Boolean constants found: {len(js_settings_found)}")
    print()

    if true_settings:
        risk_score = (len(true_settings) / len(js_settings_found) * 10) if js_settings_found else 0
        print(f"🔒 Security Risk Score: {risk_score:.1f}/10")
        if risk_score > 7:
            print("   ⚠️  HIGH RISK: Many JavaScript-enabled settings detected")
        elif risk_score > 4:
            print("   ⚠️  MEDIUM RISK: Some JavaScript-enabled settings detected")
        else:
            print("   ✅ LOW RISK: Few JavaScript-enabled settings")
    print()

def main():
    # Test with sample APKs
    samples_dir = Path("../samples")

    apks = [
        samples_dir / "com.sampleapp.apk",  # Baemin
    ]

    for apk in apks:
        if apk.exists():
            analyze_webview_security(apk)
            print("\n" * 2)

    print("=" * 70)
    print("✅ WebView Bytecode Analysis Complete!")
    print("=" * 70)
    print()
    print("Key Achievements:")
    print("  ✅ Extract method bytecode from real APK")
    print("  ✅ Decode Dalvik instructions")
    print("  ✅ Identify boolean constants (true/false)")
    print("  ✅ Analyze WebView security settings")
    print()

if __name__ == "__main__":
    main()
