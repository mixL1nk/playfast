#!/usr/bin/env python3
"""Test script for class/method search functionality"""

from pathlib import Path
import time
from playfast import core

def test_class_search():
    """Test searching for classes with filters"""
    apk_path = Path("../samples/com.instagram.android.apk")

    if not apk_path.exists():
        print(f"❌ APK file not found: {apk_path}")
        return

    print(f"📦 Testing class search with: {apk_path.name}")
    print("=" * 70)

    # Test 1: Search for Activity classes
    print("\n🔍 Test 1: Search for Activity classes")
    print("-" * 70)
    filter1 = core.ClassFilter(class_name="Activity")
    start_time = time.time()
    results1 = core.search_classes(str(apk_path), filter1, limit=10)
    elapsed = time.time() - start_time
    print(f"✅ Found {len(results1)} activities in {elapsed*1000:.2f}ms")
    for cls in results1[:5]:
        print(f"  - {cls.class_name}")

    # Test 2: Search in specific package
    print("\n🔍 Test 2: Search in com.instagram.rtc package")
    print("-" * 70)
    filter2 = core.ClassFilter(packages=["com.instagram.rtc"])
    start_time = time.time()
    results2 = core.search_classes(str(apk_path), filter2, limit=10)
    elapsed = time.time() - start_time
    print(f"✅ Found {len(results2)} classes in {elapsed*1000:.2f}ms")
    for cls in results2:
        print(f"  - {cls.class_name}")

    # Test 3: Exclude android packages
    print("\n🔍 Test 3: Search excluding android/androidx packages")
    print("-" * 70)
    filter3 = core.ClassFilter(
        exclude_packages=["android", "androidx", "com.google"],
        class_name="Service"
    )
    start_time = time.time()
    results3 = core.search_classes(str(apk_path), filter3, limit=10)
    elapsed = time.time() - start_time
    print(f"✅ Found {len(results3)} services in {elapsed*1000:.2f}ms")
    for cls in results3[:5]:
        print(f"  - {cls.class_name}")

def test_method_search():
    """Test searching for methods with filters"""
    apk_path = Path("../samples/com.instagram.android.apk")

    if not apk_path.exists():
        print(f"❌ APK file not found: {apk_path}")
        return

    print("\n\n📦 Testing method search with: {apk_path.name}")
    print("=" * 70)

    # Test 1: Find onCreate methods
    print("\n🔍 Test 1: Find onCreate methods")
    print("-" * 70)
    class_filter = core.ClassFilter(class_name="Activity")
    method_filter = core.MethodFilter(method_name="onCreate")
    start_time = time.time()
    results = core.search_methods(str(apk_path), class_filter, method_filter, limit=5)
    elapsed = time.time() - start_time
    print(f"✅ Found {len(results)} onCreate methods in {elapsed*1000:.2f}ms")
    for cls, method in results:
        print(f"  - {cls.simple_name}.{method.name}({', '.join(method.parameters)})")

    # Test 2: Find methods with no parameters
    print("\n🔍 Test 2: Find getter methods (0 parameters, return type)")
    print("-" * 70)
    class_filter2 = core.ClassFilter(packages=["com.instagram"])
    method_filter2 = core.MethodFilter(
        method_name="get",
        param_count=0
    )
    start_time = time.time()
    results2 = core.search_methods(str(apk_path), class_filter2, method_filter2, limit=10)
    elapsed = time.time() - start_time
    print(f"✅ Found {len(results2)} getter methods in {elapsed*1000:.2f}ms")
    for cls, method in results2[:5]:
        print(f"  - {cls.simple_name}.{method.name}() -> {method.return_type}")

    # Test 3: Find methods with specific return type
    print("\n🔍 Test 3: Find methods returning String")
    print("-" * 70)
    class_filter3 = core.ClassFilter(packages=["com.instagram"])
    method_filter3 = core.MethodFilter(return_type="String")
    start_time = time.time()
    results3 = core.search_methods(str(apk_path), class_filter3, method_filter3, limit=10)
    elapsed = time.time() - start_time
    print(f"✅ Found {len(results3)} methods returning String in {elapsed*1000:.2f}ms")
    for cls, method in results3[:5]:
        params = ', '.join(method.parameters) if method.parameters else ''
        print(f"  - {cls.simple_name}.{method.name}({params}) -> {method.return_type}")

def main():
    try:
        test_class_search()
        test_method_search()
        print("\n" + "=" * 70)
        print("✅ All search tests passed!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
