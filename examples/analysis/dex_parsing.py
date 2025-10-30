#!/usr/bin/env python3
"""Test script for DEX parsing functionality.
Tests class extraction from Instagram APK.
"""

from pathlib import Path
import sys
import time


try:
    from playfast import core

    print("✓ Successfully imported playfast.core")
except ImportError as e:
    print(f"✗ Failed to import playfast.core: {e}")
    sys.exit(1)

apk_path = Path("../samples/com.instagram.android.apk")

if not apk_path.exists():
    print(f"✗ APK file not found: {apk_path}")
    sys.exit(1)

print(f"\nTesting DEX parsing with: {apk_path}")
print("=" * 60)

try:
    # Extract classes (parallel)
    print("\n🔍 Extracting classes (parallel)...")
    start = time.time()
    classes = core.extract_classes_from_apk(str(apk_path), parallel=True)
    elapsed = time.time() - start

    print(f"   Extracted {len(classes):,} classes in {elapsed:.2f}s")
    print(f"   Speed: {len(classes) / elapsed:.0f} classes/sec")

    # Show some sample classes
    print("\n📦 Sample Classes (first 10):")
    for i, cls in enumerate(classes[:10], 1):
        print(f"   {i}. {cls.class_name}")
        print(f"      Package: {cls.package_name}")
        print(f"      Methods: {cls.method_count()}, Fields: {cls.field_count()}")
        if cls.superclass:
            print(f"      Extends: {cls.superclass}")
        if cls.methods:
            print(
                f"      Sample method: {cls.methods[0].name}({', '.join(cls.methods[0].parameters)}) -> {cls.methods[0].return_type}"
            )

    # Find specific classes
    print("\n🔎 Finding Instagram-specific classes...")
    instagram_classes = [c for c in classes if "instagram" in c.package_name.lower()]
    print(f"   Found {len(instagram_classes):,} Instagram classes")

    if instagram_classes:
        sample = instagram_classes[0]
        print(f"\n   Example: {sample.class_name}")
        print(f"   - Public: {sample.is_public()}")
        print(f"   - Abstract: {sample.is_abstract()}")
        print(f"   - Methods: {len(sample.methods)}")
        print(f"   - Fields: {len(sample.fields)}")

        if sample.methods:
            print("\n   First few methods:")
            for method in sample.methods[:5]:
                flags = []
                if method.is_public():
                    flags.append("public")
                if method.is_private():
                    flags.append("private")
                if method.is_static():
                    flags.append("static")
                flags_str = " ".join(flags) if flags else "package-private"
                print(f"      {flags_str} {method.name}(...)")

    # Test sequential extraction (comparison)
    print("\n🔍 Extracting classes (sequential, for comparison)...")
    start = time.time()
    classes_seq = core.extract_classes_from_apk(str(apk_path), parallel=False)
    elapsed_seq = time.time() - start

    print(f"   Extracted {len(classes_seq):,} classes in {elapsed_seq:.2f}s")
    print(f"   Speedup: {elapsed_seq / elapsed:.2f}x faster with parallel")

    print("\n✓ All DEX parsing tests passed!")

except Exception as e:
    print(f"\n✗ Error during testing: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
