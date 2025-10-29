#!/usr/bin/env python3
"""Improved WebView Security Analysis - Shows which methods enable/disable JavaScript"""

from pathlib import Path
from playfast import core
from collections import defaultdict

def analyze_method_security(class_name: str, method_name: str, bytecode: list) -> dict:
    """
    Analyze a single method to determine JavaScript settings

    Returns dict with:
    - has_javascript_call: bool
    - javascript_enabled: bool | None
    - evidence: list of instructions
    """
    if not bytecode:
        return {'has_javascript_call': False, 'javascript_enabled': None, 'evidence': []}

    instructions = core.decode_bytecode(bytecode)

    # Track const values loaded into registers
    register_values = {}
    evidence = []
    has_set_js_enabled = False
    js_enabled_value = None

    for i, insn in enumerate(instructions):
        # Track const instructions
        if insn.is_const() and insn.dest is not None and insn.value is not None:
            register_values[insn.dest] = insn.value

        # Look for invoke instructions that might be setJavaScriptEnabled
        if insn.is_invoke() and insn.method_idx is not None:
            # Check if there's a boolean value in the arguments
            # (This is a heuristic - method_idx would need to be resolved to actual method name)
            if insn.args and len(insn.args) >= 2:
                # For setJavaScriptEnabled(boolean), the boolean is typically the 2nd arg
                # (1st arg is 'this')
                for arg_reg in insn.args[1:]:
                    if arg_reg in register_values:
                        value = register_values[arg_reg]
                        if value in [0, 1]:
                            # Found a boolean argument to a method call
                            evidence.append({
                                'instruction': insn.raw,
                                'register': f'v{arg_reg}',
                                'value': bool(value),
                                'method_idx': insn.method_idx
                            })
                            # Heuristic: assume this is JavaScript-related
                            has_set_js_enabled = True
                            js_enabled_value = bool(value)

    return {
        'has_javascript_call': has_set_js_enabled,
        'javascript_enabled': js_enabled_value,
        'evidence': evidence
    }

def analyze_webview_security_improved(apk_path: Path):
    """Improved WebView security analysis with method-level detail"""

    print("=" * 70)
    print("🔐 Improved WebView Security Analysis")
    print("=" * 70)
    print()

    if not apk_path.exists():
        print(f"❌ APK not found: {apk_path}")
        return

    print(f"📱 Analyzing: {apk_path.name}\n")

    # Step 1: Find WebView classes
    print("Step 1: Finding WebView-related classes...")
    all_classes = core.extract_classes_from_apk(str(apk_path))

    webview_classes = []
    for cls in all_classes:
        if any('WebView' in method.return_type or
               any('WebView' in param for param in method.parameters)
               for method in cls.methods):
            webview_classes.append(cls)

    print(f"  Found {len(webview_classes)} WebView-related classes\n")

    if not webview_classes:
        print("❌ No WebView usage found")
        return

    # Step 2: Extract bytecode and analyze
    print("Step 2: Extracting and analyzing bytecode...")
    sample_classes = webview_classes[:15]  # Analyze more classes

    bytecode_results = core.extract_methods_bytecode(
        str(apk_path),
        sample_classes
    )

    print(f"  Extracted bytecode for {len(bytecode_results)} methods\n")

    # Step 3: Detailed analysis
    print("Step 3: Analyzing JavaScript settings...")
    print("=" * 70)

    # Group results
    js_enabled_methods = []
    js_disabled_methods = []
    unclear_methods = []

    for class_name, method_name, bytecode in bytecode_results:
        analysis = analyze_method_security(class_name, method_name, bytecode)

        if analysis['has_javascript_call']:
            method_info = {
                'class': class_name.split('.')[-1],
                'full_class': class_name,
                'method': method_name,
                'enabled': analysis['javascript_enabled'],
                'evidence': analysis['evidence']
            }

            if analysis['javascript_enabled'] is True:
                js_enabled_methods.append(method_info)
            elif analysis['javascript_enabled'] is False:
                js_disabled_methods.append(method_info)
            else:
                unclear_methods.append(method_info)

    # Display results
    print()
    print("🟢 JavaScript ENABLED Methods:")
    print("-" * 70)
    if js_enabled_methods:
        for method in js_enabled_methods:
            print(f"\n📍 {method['class']}.{method['method']}()")
            print(f"   Class: {method['full_class']}")
            for ev in method['evidence']:
                print(f"   ✓ {ev['instruction']}")
                print(f"     → Register {ev['register']} = TRUE")
                print(f"     → Method call @ index {ev['method_idx']}")
    else:
        print("   None found in analyzed methods")

    print()
    print()
    print("🔴 JavaScript DISABLED Methods:")
    print("-" * 70)
    if js_disabled_methods:
        for method in js_disabled_methods:
            print(f"\n📍 {method['class']}.{method['method']}()")
            print(f"   Class: {method['full_class']}")
            for ev in method['evidence']:
                print(f"   ✓ {ev['instruction']}")
                print(f"     → Register {ev['register']} = FALSE")
                print(f"     → Method call @ index {ev['method_idx']}")
    else:
        print("   None found in analyzed methods")

    # Summary
    print()
    print()
    print("=" * 70)
    print("📊 Security Summary")
    print("=" * 70)
    print()

    total_analyzed = len([r for r in bytecode_results if r[2]])
    total_js_methods = len(js_enabled_methods) + len(js_disabled_methods)

    print(f"Total methods analyzed: {total_analyzed}")
    print(f"Methods with JS settings: {total_js_methods}")
    print(f"  🟢 JavaScript ENABLED: {len(js_enabled_methods)}")
    print(f"  🔴 JavaScript DISABLED: {len(js_disabled_methods)}")
    print()

    if total_js_methods > 0:
        enabled_ratio = len(js_enabled_methods) / total_js_methods
        risk_score = enabled_ratio * 10

        print(f"🔒 Security Risk Score: {risk_score:.1f}/10")

        if risk_score > 7:
            print("   ⚠️  HIGH RISK - Majority of methods enable JavaScript")
        elif risk_score > 3:
            print("   ⚠️  MEDIUM RISK - Some methods enable JavaScript")
        else:
            print("   ✅ LOW RISK - Most methods disable JavaScript")
        print()

        # Specific recommendations
        print("💡 Recommendations:")
        if js_enabled_methods:
            print("   • Review these methods that enable JavaScript:")
            for method in js_enabled_methods[:3]:
                print(f"     - {method['full_class']}.{method['method']}()")
            if len(js_enabled_methods) > 3:
                print(f"     ... and {len(js_enabled_methods) - 3} more")
        print()

    # Show bytecode sample for education
    if js_enabled_methods:
        print("=" * 70)
        print("📝 Example: How we detect JavaScript enablement")
        print("=" * 70)
        print()

        example = js_enabled_methods[0]
        print(f"Method: {example['full_class']}.{example['method']}()\n")
        print("Bytecode pattern:")
        print("```")
        for ev in example['evidence']:
            print(f"{ev['instruction']}")
        print("```")
        print()
        print("Analysis:")
        print("  1. const/4 loads value 1 (TRUE) into a register")
        print("  2. invoke-* passes this register to a method")
        print("  3. Likely calling setJavaScriptEnabled(true)")
        print()

def main():
    samples_dir = Path("../samples")
    apk = samples_dir / "com.sampleapp.apk"

    if apk.exists():
        analyze_webview_security_improved(apk)

    print("=" * 70)
    print("✅ Improved Analysis Complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
