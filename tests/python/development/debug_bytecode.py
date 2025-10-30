#!/usr/bin/env python3
"""Debug bytecode to understand why values aren't being tracked."""

from pathlib import Path

from playfast import core


def debug_method_bytecode(apk_path: Path):
    """Debug bytecode analysis."""
    print("=" * 70)
    print("🐛 Debug Bytecode Analysis")
    print("=" * 70)
    print()

    all_classes = core.extract_classes_from_apk(str(apk_path))

    # Find the specific class we saw in results
    target_class = None
    for cls in all_classes:
        if cls.simple_name == "c" and "V5" in cls.package_name:
            target_class = cls
            break

    if not target_class:
        print("Target class not found, using first WebView class")
        # Find any WebView class
        for cls in all_classes:
            if any(
                "WebView" in method.return_type
                or any("WebView" in param for param in method.parameters)
                for method in cls.methods
            ):
                target_class = cls
                break

    if not target_class:
        print("No WebView class found")
        return

    print(f"Found class: {target_class.class_name}")
    print(f"Methods: {len(target_class.methods)}")
    print()

    # Extract bytecode
    bytecode_results = core.extract_methods_bytecode(str(apk_path), [target_class])

    for class_name, method_name, bytecode in bytecode_results:
        if method_name == "onViewCreated":
            print(f"Method: {class_name}.{method_name}()")
            print(f"Bytecode length: {len(bytecode)} words")
            print()

            # Decode instructions
            instructions = core.decode_bytecode(bytecode)

            print(f"Total instructions: {len(instructions)}")
            print()
            print("All instructions:")
            print("-" * 70)

            # Track registers
            register_values = {}

            for i, insn in enumerate(instructions):
                print(f"{i:3d}: {insn.raw}")

                # Track const
                if insn.is_const():
                    if insn.dest is not None and insn.value is not None:
                        register_values[insn.dest] = insn.value
                        print(
                            f"       → v{insn.dest} = {insn.value} ({type(insn.value).__name__})"
                        )

                # Check invoke
                if insn.is_invoke():
                    if insn.method_idx is not None:
                        try:
                            sig = core.resolve_method_from_apk(
                                str(apk_path), insn.method_idx
                            )
                            print(f"       → {sig.method_name}")

                            if sig.is_set_javascript_enabled():
                                print("       ✨ Found setJavaScriptEnabled!")
                                if insn.args:
                                    print(f"       Args: {insn.args}")
                                    for arg_idx, arg_reg in enumerate(insn.args):
                                        value = register_values.get(arg_reg, "unknown")
                                        print(
                                            f"         arg[{arg_idx}] = v{arg_reg} = {value}"
                                        )
                        except:
                            pass

            print()
            print("Register state:")
            for reg, val in sorted(register_values.items()):
                print(f"  v{reg} = {val}")
            print()


def main():
    samples_dir = Path("../samples")
    apk = samples_dir / "com.sampleapp.apk"

    if apk.exists():
        debug_method_bytecode(apk)


if __name__ == "__main__":
    main()
