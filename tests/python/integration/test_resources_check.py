#!/usr/bin/env python3
"""Check current resources.arsc capabilities"""

from pathlib import Path
from playfast import core
import sys

def check_resources_support(apk_path: Path):
    """Check what resources.arsc functionality is available"""

    print("=" * 70)
    print("🔍 Resources.arsc Support Check")
    print("=" * 70)
    print()

    if not apk_path.exists():
        print(f"❌ APK not found: {apk_path}")
        return

    print(f"📱 Testing with: {apk_path.name}\n")

    # Check available functions
    print("Available core functions:")
    resources_funcs = [attr for attr in dir(core) if 'resource' in attr.lower()]

    if resources_funcs:
        print("  ✅ Found resource-related functions:")
        for func in resources_funcs:
            print(f"     • {func}")
    else:
        print("  ❌ No resource-related functions found")
    print()

    # Check APK extractor
    print("Checking ApkExtractor capabilities:")
    extractor_attrs = [attr for attr in dir(core) if 'extract' in attr.lower() or 'apk' in attr.lower()]
    for attr in extractor_attrs:
        print(f"  • {attr}")
    print()

    # Try to extract manifest (which uses binary XML parsing)
    print("Testing binary XML parsing (AndroidManifest.xml):")
    try:
        manifest = core.parse_manifest_from_apk(str(apk_path))
        print(f"  ✅ Manifest parsing works!")
        print(f"     Package: {manifest.package}")
        print(f"     Activities: {len(manifest.activities)}")
        print(f"     Permissions: {len(manifest.permissions)}")
    except Exception as e:
        print(f"  ❌ Manifest parsing failed: {e}")
    print()

    # Summary
    print("=" * 70)
    print("📊 Summary")
    print("=" * 70)
    print()
    print("Current Capabilities:")
    print("  ✅ APK extraction (ZIP handling)")
    print("  ✅ DEX file parsing")
    print("  ✅ AndroidManifest.xml parsing (binary XML)")
    print("  ✅ Bytecode decompilation")
    print()
    print("Resources.arsc Status:")
    print("  ❌ resources.arsc parser NOT implemented")
    print("  ℹ️  Can extract raw bytes, but cannot parse")
    print()
    print("What resources.arsc contains:")
    print("  • String resources (app_name, button labels, etc.)")
    print("  • Integer resources (IDs referenced in code)")
    print("  • Drawable references")
    print("  • Layout references")
    print("  • Style and theme definitions")
    print()
    print("Why resources.arsc parsing might be useful:")
    print("  1. Resolve resource IDs to actual values")
    print("     Example: R.string.app_name → \"My App\"")
    print("  2. Extract localized strings")
    print("  3. Find hardcoded secrets in string resources")
    print("  4. Analyze resource usage patterns")
    print()
    print("Current workarounds:")
    print("  1. Use external tools: aapt2, apktool")
    print("  2. Python libraries: androguard (has ARSC parser)")
    print("  3. Manual extraction with apk.extract_resources()")
    print()

def main():
    samples_dir = Path("../samples")
    apk = samples_dir / "com.sampleapp.apk"

    if apk.exists():
        check_resources_support(apk)
    else:
        print(f"❌ APK not found: {apk}")
        print("\nNote: This check doesn't require a specific APK")
        print("Just checking what functions are available in playfast.core")
        print()
        print("Available functions with 'resource' in name:")
        resources_funcs = [attr for attr in dir(core) if 'resource' in attr.lower()]
        if resources_funcs:
            for func in resources_funcs:
                print(f"  • {func}")
        else:
            print("  ❌ No resource-related functions found")

if __name__ == "__main__":
    main()
