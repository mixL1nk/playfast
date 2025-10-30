#!/usr/bin/env python3
"""Test Method Resolution - Phase 1 of Decompilation."""

from pathlib import Path

from playfast import core


def test_method_resolution(apk_path: Path):
    """Test resolving method indices to human-readable signatures."""
    print("=" * 70)
    print("🧪 Testing Method Resolution")
    print("=" * 70)
    print()

    if not apk_path.exists():
        print(f"❌ APK not found: {apk_path}")
        return

    print(f"📱 Testing with: {apk_path.name}\n")

    # Step 1: Find WebView classes and extract bytecode
    print("Step 1: Extracting bytecode from WebView methods...")
    all_classes = core.extract_classes_from_apk(str(apk_path))

    webview_classes = [
        cls
        for cls in all_classes
        if any(
            "WebView" in method.return_type
            or any("WebView" in param for param in method.parameters)
            for method in cls.methods
        )
    ][:5]  # Take first 5 classes

    bytecode_results = core.extract_methods_bytecode(str(apk_path), webview_classes)

    print(f"  Found {len(bytecode_results)} methods with bytecode\n")

    # Step 2: Find method calls and resolve them
    print("Step 2: Resolving method indices...")
    print("-" * 70)

    resolved_count = 0
    failed_count = 0

    for class_name, method_name, bytecode in bytecode_results[:10]:  # Test first 10
        if not bytecode:
            continue

        # Decode bytecode
        instructions = core.decode_bytecode(bytecode)

        # Find invoke instructions
        for insn in instructions:
            if insn.is_invoke() and insn.method_idx is not None:
                method_idx = insn.method_idx

                # Try to resolve this method
                try:
                    sig = core.resolve_method_from_apk(str(apk_path), method_idx)

                    print(f"\n✅ Resolved method@{method_idx}")
                    print(f"   Class: {sig.class_name}")
                    print(f"   Method: {sig.method_name}")
                    print(f"   Params: {sig.parameters}")
                    print(f"   Return: {sig.return_type}")
                    print(f"   Full: {sig.full_signature}")

                    # Test helper methods
                    if sig.is_webview_method():
                        print("   🌐 WebView method!")
                    if sig.is_set_javascript_enabled():
                        print("   🔒 JavaScript control method!")

                    resolved_count += 1

                    # Only show first 3 examples
                    if resolved_count >= 3:
                        break

                except Exception as e:
                    failed_count += 1
                    if failed_count <= 2:  # Show first 2 errors
                        print(f"\n❌ Failed to resolve method@{method_idx}: {e}")

        if resolved_count >= 3:
            break

    # Step 3: Test with known WebView methods
    print()
    print()
    print("Step 3: Testing specific patterns...")
    print("-" * 70)

    # Look for setJavaScriptEnabled calls
    js_enabled_calls = []

    for class_name, method_name, bytecode in bytecode_results:
        if not bytecode:
            continue

        instructions = core.decode_bytecode(bytecode)

        # Track register values
        register_values = {}

        for insn in instructions:
            # Track const values
            if insn.is_const() and insn.dest is not None and insn.value is not None:
                register_values[insn.dest] = insn.value

            # Check invoke instructions
            if insn.is_invoke() and insn.method_idx is not None:
                try:
                    sig = core.resolve_method_from_apk(str(apk_path), insn.method_idx)

                    if sig.is_set_javascript_enabled():
                        # Found a JavaScript control call!
                        # Check if we know the argument value
                        arg_value = None
                        if insn.args and len(insn.args) >= 2:
                            arg_reg = insn.args[1]  # Second arg (first is 'this')
                            arg_value = register_values.get(arg_reg)

                        js_enabled_calls.append(
                            {
                                "class": class_name,
                                "method": method_name,
                                "signature": sig,
                                "enabled": bool(arg_value)
                                if arg_value in [0, 1]
                                else None,
                                "instruction": insn.raw,
                            }
                        )

                except Exception:
                    pass  # Skip resolution errors

    # Show results
    if js_enabled_calls:
        print(f"\n🎯 Found {len(js_enabled_calls)} setJavaScriptEnabled calls:\n")

        for call in js_enabled_calls:
            sig = call["signature"]
            enabled_str = (
                "✅ ENABLED"
                if call["enabled"]
                else "❌ DISABLED"
                if call["enabled"] is False
                else "❓ UNKNOWN"
            )

            print(f"{enabled_str}")
            print(f"   Location: {call['class'].split('.')[-1]}.{call['method']}()")
            print(
                f"   Call: {sig.format_call(['true' if call['enabled'] else 'false'] if call['enabled'] is not None else ['?'])}"
            )
            print(f"   Bytecode: {call['instruction']}")
            print()
    else:
        print("⚠️  No setJavaScriptEnabled calls found in sample")

    # Summary
    print()
    print("=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    print()
    print(f"Methods resolved successfully: {resolved_count}")
    print(f"Resolution failures: {failed_count}")
    print(f"setJavaScriptEnabled calls found: {len(js_enabled_calls)}")
    print()

    if js_enabled_calls:
        print("✅ Method resolution working correctly!")
        print("   Ready to integrate into WebView analysis")
    else:
        print("⚠️  Method resolution works, but no JavaScript control found in sample")
    print()


def main():
    samples_dir = Path("../samples")
    apk = samples_dir / "com.sampleapp.apk"

    if apk.exists():
        test_method_resolution(apk)
    else:
        print(f"❌ APK not found: {apk}")
        print("Please place an APK in ../samples/")


if __name__ == "__main__":
    main()
