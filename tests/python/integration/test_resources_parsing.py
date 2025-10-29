#!/usr/bin/env python3
"""Test Resources.arsc Parsing"""

from pathlib import Path
from playfast import core

def test_resources_parsing(apk_path: Path):
    """Test resources.arsc parsing and resolution"""

    print("=" * 70)
    print("🔍 Resources.arsc Parsing Test")
    print("=" * 70)
    print()

    if not apk_path.exists():
        print(f"❌ APK not found: {apk_path}")
        return

    print(f"📱 Testing with: {apk_path.name}\n")

    # Test 1: Parse resources
    print("Test 1: Parse resources.arsc")
    print("-" * 70)

    try:
        resolver = core.parse_resources_from_apk(str(apk_path))
        print(f"✅ Successfully parsed resources.arsc")
        print(f"   Total resources: {resolver.count()}")
        print()

        # Test 2: Get all strings
        print("Test 2: Extract string resources")
        print("-" * 70)

        strings = resolver.get_all_strings()
        print(f"✅ Found {len(strings)} string resources")

        # Show first 10
        print("\n   First 10 string resources:")
        for res in strings[:10]:
            print(f"   • {res.name}: \"{res.value}\"")
        print()

        # Test 3: Resource ID detection
        print("Test 3: Resource ID detection")
        print("-" * 70)

        test_values = [
            0x7f0e0001,  # Likely a string resource
            0x7f030042,  # Likely a layout
            42,          # Not a resource
            0,           # Boolean false
            1,           # Boolean true
            2131363364,  # Another resource ID (0x7f0e0b24)
        ]

        for val in test_values:
            is_res = resolver.is_resource_id(val)
            status = "✅ Resource ID" if is_res else "❌ Not a resource ID"
            print(f"   {status}: 0x{val:08x} ({val})")
        print()

        # Test 4: Resolve specific IDs
        print("Test 4: Resolve specific resource IDs")
        print("-" * 70)

        # Try to resolve some IDs
        for res in strings[:5]:
            resolved = resolver.resolve(res.id)
            if resolved:
                print(f"   0x{res.id:08x} → {resolved.type_name}.{resolved.name} = {resolved.value}")
        print()

        # Test 5: Get resources by type
        print("Test 5: Get resources by type")
        print("-" * 70)

        # Check what types exist
        types_found = set()
        for res in strings[:100]:  # Sample first 100
            types_found.add(res.type_name)

        print(f"   Found resource types: {', '.join(sorted(types_found))}")

        # Get drawable resources
        drawables = resolver.get_by_type("drawable")
        print(f"   Drawable resources: {len(drawables)}")

        # Get layout resources
        layouts = resolver.get_by_type("layout")
        print(f"   Layout resources: {len(layouts)}")

        # Get color resources
        colors = resolver.get_by_type("color")
        print(f"   Color resources: {len(colors)}")
        print()

        # Test 6: Security analysis - find interesting strings
        print("Test 6: Security Analysis - Find interesting strings")
        print("-" * 70)

        interesting_keywords = ["key", "secret", "token", "password", "api", "url", "http"]

        for keyword in interesting_keywords:
            matches = [
                s for s in strings
                if keyword.lower() in s.name.lower() or keyword.lower() in s.value.lower()
            ]

            if matches:
                print(f"\n   🔍 Found {len(matches)} resources with '{keyword}':")
                for res in matches[:3]:  # Show first 3
                    print(f"      • {res.name}: \"{res.value[:50]}...\" " if len(res.value) > 50 else f"      • {res.name}: \"{res.value}\"")
                if len(matches) > 3:
                    print(f"      ... and {len(matches) - 3} more")
        print()

        # Test 7: Check for hardcoded URLs
        print("Test 7: Find hardcoded URLs")
        print("-" * 70)

        urls = [s for s in strings if s.value.startswith("http")]

        if urls:
            print(f"   ⚠️  Found {len(urls)} URL resources:")
            for url_res in urls[:10]:
                print(f"      • {url_res.name}: {url_res.value}")
            if len(urls) > 10:
                print(f"      ... and {len(urls) - 10} more")
        else:
            print("   ✅ No hardcoded URLs found in string resources")
        print()

    except Exception as e:
        print(f"❌ Failed to parse resources: {e}")
        import traceback
        traceback.print_exc()
        return

    print("=" * 70)
    print("📊 Summary")
    print("=" * 70)
    print()
    print("✅ Resources.arsc parsing successful!")
    print(f"   • Total resources: {resolver.count()}")
    print(f"   • String resources: {len(strings)}")
    print(f"   • URL resources: {len(urls)}")
    print()
    print("Next steps:")
    print("  1. ✅ Resource parsing works")
    print("  2. 🔄 Integrate with decompilation")
    print("  3. 🔄 Resolve resource IDs in bytecode")
    print()

def main():
    samples_dir = Path("../samples")
    apk = samples_dir / "com.sampleapp.apk"

    if apk.exists():
        test_resources_parsing(apk)
    else:
        print(f"❌ APK not found: {apk}")

if __name__ == "__main__":
    main()
