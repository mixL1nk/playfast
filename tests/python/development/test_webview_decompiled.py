#!/usr/bin/env python3
"""WebView Security Analysis with Partial Decompilation (Phase 1)"""

from pathlib import Path
from playfast import core
from collections import defaultdict

def analyze_method_with_decompilation(class_name: str, method_name: str, bytecode: list, apk_path: str) -> dict:
    """
    Analyze a method with partial decompilation

    Returns dict with:
    - has_javascript_call: bool
    - javascript_enabled: bool | None
    - evidence: list of decompiled statements
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

        # Look for invoke instructions
        if insn.is_invoke() and insn.method_idx is not None:
            try:
                # 🎯 PHASE 1: Resolve method index to signature
                sig = core.resolve_method_from_apk(apk_path, insn.method_idx)

                # Check if this is setJavaScriptEnabled
                if sig.is_set_javascript_enabled():
                    # Extract argument value
                    # The invoke args list includes the target object + parameters
                    # For instance methods: args[0] = 'this', args[1] = param1, etc
                    arg_value = None
                    if insn.args and len(insn.args) >= 1:
                        # Check all args for boolean values
                        for arg_reg in insn.args:
                            if arg_reg in register_values:
                                value = register_values[arg_reg]
                                if value in [0, 1]:
                                    arg_value = bool(value)
                                    break

                    # Generate decompiled statement
                    if arg_value is not None:
                        decompiled = sig.format_call(['true' if arg_value else 'false'])
                    else:
                        decompiled = sig.format_call(['?'])

                    evidence.append({
                        'bytecode': insn.raw,
                        'signature': sig.full_signature,
                        'decompiled': decompiled,
                        'value': arg_value
                    })

                    has_set_js_enabled = True
                    js_enabled_value = arg_value

            except Exception:
                # Could not resolve method - skip
                pass

    return {
        'has_javascript_call': has_set_js_enabled,
        'javascript_enabled': js_enabled_value,
        'evidence': evidence
    }

def analyze_webview_security_decompiled(apk_path: Path):
    """WebView security analysis with partial decompilation"""

    print("=" * 70)
    print("🔐 WebView Security Analysis with Decompilation")
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
    print("Step 2: Extracting and analyzing bytecode with decompilation...")
    sample_classes = webview_classes[:15]

    bytecode_results = core.extract_methods_bytecode(
        str(apk_path),
        sample_classes
    )

    print(f"  Extracted bytecode for {len(bytecode_results)} methods\n")

    # Step 3: Decompile and analyze
    print("Step 3: Decompiling JavaScript settings...")
    print("=" * 70)

    # Group results
    js_enabled_methods = []
    js_disabled_methods = []
    unclear_methods = []

    for class_name, method_name, bytecode in bytecode_results:
        analysis = analyze_method_with_decompilation(
            class_name, method_name, bytecode, str(apk_path)
        )

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
                print(f"   ✓ {ev['decompiled']}")  # ← Decompiled code!
                print(f"     Original: {ev['bytecode']}")
                print(f"     Signature: {ev['signature']}")
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
                print(f"   ✓ {ev['decompiled']}")  # ← Decompiled code!
                print(f"     Original: {ev['bytecode']}")
                print(f"     Signature: {ev['signature']}")
    else:
        print("   None found in analyzed methods")

    print()
    print()
    print("❓ Unclear JavaScript Settings:")
    print("-" * 70)
    if unclear_methods:
        for method in unclear_methods:
            print(f"\n📍 {method['class']}.{method['method']}()")
            print(f"   Class: {method['full_class']}")
            for ev in method['evidence']:
                print(f"   ⚠️  {ev['decompiled']}")
                print(f"     (Value could not be determined statically)")
    else:
        print("   None found")

    # Summary
    print()
    print()
    print("=" * 70)
    print("📊 Security Summary")
    print("=" * 70)
    print()

    total_analyzed = len([r for r in bytecode_results if r[2]])
    total_js_methods = len(js_enabled_methods) + len(js_disabled_methods) + len(unclear_methods)

    print(f"Total methods analyzed: {total_analyzed}")
    print(f"Methods with JS settings: {total_js_methods}")
    print(f"  🟢 JavaScript ENABLED: {len(js_enabled_methods)}")
    print(f"  🔴 JavaScript DISABLED: {len(js_disabled_methods)}")
    print(f"  ❓ Unclear: {len(unclear_methods)}")
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

    # Show decompilation comparison
    if js_enabled_methods or js_disabled_methods:
        print("=" * 70)
        print("📝 Decompilation Comparison (Before vs After)")
        print("=" * 70)
        print()

        example = js_enabled_methods[0] if js_enabled_methods else js_disabled_methods[0]
        ev = example['evidence'][0]

        print(f"Method: {example['full_class']}.{example['method']}()\n")

        print("BEFORE (Raw Bytecode):")
        print("  " + ev['bytecode'])
        print("  → Method call @ index (unreadable)")
        print()

        print("AFTER (Phase 1 Decompilation):")
        print("  " + ev['decompiled'])
        print("  ✅ Human-readable method call with value")
        print()

        print("This is Phase 1: Method Index Resolution")
        print("Phase 2 will add better expression reconstruction")
        print()

def main():
    samples_dir = Path("../samples")
    apk = samples_dir / "com.sampleapp.apk"

    if apk.exists():
        analyze_webview_security_decompiled(apk)
    else:
        print(f"❌ APK not found: {apk}")

    print("=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)
    print()
    print("Key Improvements:")
    print("  ✅ Method indices resolved to human-readable signatures")
    print("  ✅ Decompiled code shows actual method calls")
    print("  ✅ Clear distinction between enabled/disabled JavaScript")
    print()
    print("Next: Phase 2 - Simple Expression Reconstruction")
    print("  • Better formatting of method chains")
    print("  • Field resolution (this.webView)")
    print("  • String constant extraction")
    print()

if __name__ == "__main__":
    main()
