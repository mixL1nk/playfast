# APK Analysis with Playfast

Playfast includes high-performance Android APK analysis capabilities built in Rust with Python bindings.

## Features

- **Fast DEX Parsing**: Custom DEX parser processing 150K+ classes in ~500ms
- **Manifest Parsing**: Extract package info, permissions, components from AndroidManifest.xml
- **Class/Method Search**: Filter and search classes and methods with flexible criteria
- **Multi-DEX Support**: Handles APKs with multiple DEX files
- **Parallel Processing**: Leverages rayon for CPU-bound operations
- **High-Level Python API**: Convenient `ApkAnalyzer` wrapper for easy analysis

## Installation

APK analysis features are included with playfast:

```bash
pip install playfast
```

## Quick Start

### Basic Analysis

```python
from playfast import ApkAnalyzer

# Load APK
analyzer = ApkAnalyzer("app.apk")

# Get manifest info
manifest = analyzer.manifest
print(f"Package: {manifest.package_name}")
print(f"Version: {manifest.version_name}")

# Get statistics
stats = analyzer.get_statistics()
print(f"Classes: {stats['class_count']:,}")
print(f"Methods: {stats['method_count']:,}")
```

### Searching for Classes

```python
# Find Activity classes
activities = analyzer.find_activities(limit=10)
for activity in activities:
    print(activity.class_name)

# Search in specific package
rtc_classes = analyzer.find_classes(
    package="com.example.rtc",
    limit=20
)

# Exclude system packages
app_classes = analyzer.get_app_classes()
```

### Searching for Methods

```python
# Find onCreate methods
onCreate_methods = analyzer.find_methods(method_name="onCreate")
for cls, method in onCreate_methods:
    print(f"{cls.simple_name}.{method.name}")

# Find getter methods (no parameters)
getters = analyzer.find_methods(
    method_name="get",
    param_count=0,
    class_package="com.example"
)

# Find methods returning String
string_methods = analyzer.find_methods(
    return_type="String",
    limit=20
)
```

## Low-Level API

For advanced users, direct Rust API is available:

```python
from playfast import core

# Extract APK info
dex_count, has_manifest, has_resources, dex_files = core.extract_apk_info(apk_path)

# Parse manifest
manifest = core.parse_manifest_from_apk(apk_path)

# Extract all classes
classes = core.extract_classes_from_apk(apk_path, parallel=True)

# Search with filters
class_filter = core.ClassFilter(
    packages=["com.example"],
    class_name="Activity"
)
results = core.search_classes(apk_path, class_filter, limit=10)

# Method search
method_filter = core.MethodFilter(
    method_name="onCreate",
    param_count=1
)
methods = core.search_methods(apk_path, class_filter, method_filter)
```

## API Reference

### ApkAnalyzer

Main class for APK analysis.

#### Constructor

```python
ApkAnalyzer(apk_path: str | Path, load_classes: bool = False)
```

- `apk_path`: Path to the APK file
- `load_classes`: If True, load all classes immediately (default: False)

#### Properties

- `manifest`: Parsed AndroidManifest.xml (RustManifestInfo)
- `classes`: List of all classes (loads if not cached)
- `dex_count`: Number of DEX files
- `has_manifest`: Whether APK has AndroidManifest.xml
- `has_resources`: Whether APK has resources.arsc
- `dex_files`: List of DEX file names

#### Methods

##### `find_classes()`

Find classes matching criteria.

```python
find_classes(
    package: str | None = None,
    exclude_packages: list[str] | None = None,
    name: str | None = None,
    limit: int | None = None,
    parallel: bool = True
) -> list[RustDexClass]
```

##### `find_methods()`

Find methods matching criteria.

```python
find_methods(
    method_name: str | None = None,
    param_count: int | None = None,
    return_type: str | None = None,
    class_package: str | None = None,
    class_name: str | None = None,
    limit: int | None = None,
    parallel: bool = True
) -> list[tuple[RustDexClass, RustDexMethod]]
```

##### Convenience Methods

- `find_activities(package=None, limit=None)`: Find Activity classes
- `find_services(package=None, limit=None)`: Find Service classes
- `find_receivers(package=None, limit=None)`: Find BroadcastReceiver classes
- `get_app_classes(limit=None)`: Get app classes (excluding android/androidx)
- `get_statistics()`: Get APK statistics dictionary

### RustManifestInfo

Parsed AndroidManifest.xml information.

**Attributes:**
- `package_name`: Package name (e.g., "com.example.app")
- `version_name`: Version name (e.g., "1.0.0")
- `version_code`: Version code
- `min_sdk_version`: Minimum SDK version
- `target_sdk_version`: Target SDK version
- `permissions`: List of requested permissions
- `activities`: List of activity names
- `services`: List of service names
- `receivers`: List of receiver names
- `providers`: List of provider names
- `application_label`: Application label

### RustDexClass

Represents a DEX class.

**Attributes:**
- `class_name`: Full class name (e.g., "com.example.MainActivity")
- `simple_name`: Simple class name (e.g., "MainActivity")
- `package_name`: Package name (e.g., "com.example")
- `superclass`: Superclass name
- `methods`: List of RustDexMethod
- `fields`: List of RustDexField
- `access_flags`: Access flags (public, abstract, etc.)

**Methods:**
- `is_public()`: Check if class is public
- `is_abstract()`: Check if class is abstract
- `is_interface()`: Check if class is interface
- `is_final()`: Check if class is final

### RustDexMethod

Represents a DEX method.

**Attributes:**
- `name`: Method name
- `parameters`: List of parameter types
- `return_type`: Return type
- `access_flags`: Access flags

**Methods:**
- `is_public()`, `is_private()`, `is_protected()`: Check visibility
- `is_static()`: Check if static
- `is_final()`: Check if final
- `is_abstract()`: Check if abstract

### ClassFilter

Filter for searching classes.

```python
ClassFilter(
    packages: list[str] | None = None,
    exclude_packages: list[str] | None = None,
    class_name: str | None = None,
    modifiers: int | None = None
)
```

### MethodFilter

Filter for searching methods.

```python
MethodFilter(
    method_name: str | None = None,
    param_count: int | None = None,
    param_types: list[str] | None = None,
    return_type: str | None = None,
    modifiers: int | None = None
)
```

## Examples

Complete examples are available in the `examples/` directory:

- **apk_analysis_basic.py**: Basic APK analysis and information extraction
- **apk_security_audit.py**: Security audit tool for APKs
- **apk_comparison.py**: Compare two APK versions

## Performance

Performance benchmarks on Instagram APK (150K+ classes, 615K+ methods):

| Operation | Time | Throughput |
|-----------|------|------------|
| DEX parsing | 410ms | 364K classes/sec |
| Manifest parsing | 632ms | - |
| Class search | ~500ms | - |
| Method search | ~500ms | - |

All operations use parallel processing with rayon for optimal CPU utilization.

## Implementation Details

### Architecture

- **Rust Core**: High-performance DEX parsing, ULEB128 decoding, MUTF-8 strings
- **PyO3**: Zero-copy Python bindings
- **Rayon**: Parallel processing for CPU-bound operations
- **rusty-axml**: Binary XML (AXML) parsing for AndroidManifest.xml

### DEX Format Support

- DEX format specification: [Android DEX Format](https://source.android.com/docs/core/runtime/dex-format)
- Custom parser implementation (no dependency on buggy crates)
- Full support for:
  - String pool with MUTF-8 encoding
  - Type descriptors and signatures
  - Class definitions and data
  - Method and field definitions
  - Access flags and modifiers

### Multi-DEX Handling

APKs can contain multiple DEX files (classes.dex, classes2.dex, ...). The analyzer:
- Automatically detects all DEX files
- Sorts them by number
- Processes them in parallel
- Merges results

## Limitations

Current limitations:

1. **No Decompilation**: Does not decompile DEX to Java source code
2. **No Resource Parsing**: resources.arsc parsing not yet implemented
3. **No Code Analysis**: No bytecode analysis or control flow graphs
4. **Read-Only**: Cannot modify or rebuild APKs

## Future Enhancements

Planned features:

- [ ] Resource parsing (resources.arsc)
- [ ] Method bytecode inspection
- [ ] Call graph generation
- [ ] Dead code detection
- [ ] ProGuard/R8 mapping support
- [ ] APK signing verification

## Comparison with Other Tools

| Tool | Language | Performance | Features |
|------|----------|-------------|----------|
| **playfast** | Rust+Python | ⚡⚡⚡ Very Fast | Basic analysis, search |
| androguard | Python | 🐢 Slow | Full analysis, decompilation |
| apktool | Java | 🐌 Moderate | Decompilation, rebuild |
| jadx | Java | 🐌 Moderate | Decompilation, GUI |

Playfast focuses on **speed** and **ease of use** for common APK analysis tasks. For decompilation or deep analysis, use androguard or jadx.

## Contributing

Contributions are welcome! Areas for improvement:

- Resource parsing implementation
- Performance optimizations
- Additional convenience methods
- Documentation improvements

## License

MIT License - see LICENSE file for details.
