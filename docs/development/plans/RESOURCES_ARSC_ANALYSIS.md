# Resources.arsc Analysis & Implementation Plan

## Current Status

### ✅ Implemented
- APK extraction (ZIP handling)
- Raw resources.arsc extraction: `ApkExtractor::extract_resources()`
- AndroidManifest.xml parsing (binary XML format)
- DEX file parsing and bytecode analysis
- Class-level decompilation

### ❌ NOT Implemented
- **resources.arsc parser**: Cannot parse the binary format
- Resource ID → String/Value resolution
- Localized string extraction

## What is resources.arsc?

resources.arsc is a binary file containing all app resources:
- **String resources**: app names, labels, messages
- **Integer resources**: dimensions, colors, IDs
- **References**: drawables, layouts, styles
- **Localization**: translations for different languages

### File Format
```
resources.arsc (binary)
├── Resource Table Header
├── String Pool (global strings)
├── Package (usually one per APK)
│   ├── Package Header
│   ├── Type String Pool (type names: string, layout, drawable)
│   ├── Key String Pool (resource names: app_name, button_ok)
│   └── Type Specs & Configs
│       ├── Type Spec (e.g., "string")
│       └── Type Configs (different configurations)
│           └── Resource Entries
│               ├── ID → Value mapping
│               └── Localized variants
```

## Use Cases for WebView Security Analysis

### 1. Resource ID Resolution (High Priority)
**Problem**: Decompiled code shows resource IDs
```java
// Current output:
webSettings.setJavaScriptEnabled(2131363364)

// With resources.arsc parsing:
webSettings.setJavaScriptEnabled(R.id.web_settings) → false
```

**Impact**:
- ❌ Currently unclear what the value means
- ✅ With parser: Know it's a resource ID, can try to resolve

### 2. String Resource Analysis (Medium Priority)
**Use case**: Find hardcoded secrets/URLs in strings
```
Example resources:
- strings.xml → R.string.api_key = "sk_live_abc123..."
- strings.xml → R.string.server_url = "https://internal.example.com"
```

**Security implications**:
- API keys in string resources
- Internal URLs exposed
- Debug strings left in production

### 3. Localization Analysis (Low Priority)
Extract all translations to:
- Check for inconsistent security messages
- Find locale-specific behavior

## Implementation Complexity

### Option 1: Minimal (Resource ID detection only)
**Goal**: Detect when a const value is a resource ID

**Implementation**: ~2-3 hours
```rust
pub struct ResourceIdDetector {
    // Resource IDs typically start with 0x7f (127)
    // Format: 0x7fTTEEEE
    // TT = resource type (02=string, 03=layout, etc)
    // EEEE = entry ID
}

impl ResourceIdDetector {
    pub fn is_resource_id(value: i64) -> bool {
        (value >> 24) == 0x7f
    }

    pub fn get_resource_type(value: i64) -> Option<&str> {
        let type_id = (value >> 16) & 0xFF;
        match type_id {
            0x02 => Some("string"),
            0x03 => Some("layout"),
            0x04 => Some("drawable"),
            _ => None
        }
    }
}
```

**Output improvement**:
```
Before: webSettings.setJavaScriptEnabled(2131363364)
After:  webSettings.setJavaScriptEnabled(R.drawable.something)
                                         ↑ Detected as resource ID
```

**Pros**:
- Quick to implement
- Improves readability immediately
- No parsing needed

**Cons**:
- Cannot resolve actual value
- Just detection, not resolution

### Option 2: Full Parser (Complete resource parsing)
**Goal**: Parse entire resources.arsc and resolve IDs

**Implementation**: ~12-16 hours
```rust
pub struct ArscParser {
    pub packages: Vec<Package>,
    pub string_pool: StringPool,
}

pub struct Package {
    pub id: u32,
    pub name: String,
    pub types: Vec<ResourceType>,
}

pub struct ResourceType {
    pub name: String, // "string", "layout", etc
    pub entries: HashMap<u32, ResourceEntry>,
}

pub struct ResourceEntry {
    pub id: u32,
    pub name: String,  // "app_name", "button_ok"
    pub value: ResourceValue,
}

pub enum ResourceValue {
    String(String),
    Integer(i32),
    Boolean(bool),
    Reference(u32),
    // ... many more types
}
```

**Output improvement**:
```
webSettings.setJavaScriptEnabled(2131363364)
↓ Resolved
webSettings.setJavaScriptEnabled(false) // from R.bool.enable_js
```

**Pros**:
- Complete resource resolution
- Can extract all strings for security audit
- Enables advanced analysis

**Cons**:
- Complex binary format
- Many edge cases (configurations, locales)
- Maintenance burden

### Option 3: Hybrid (ID detection + external tool)
**Goal**: Detect IDs + use aapt2/apktool for resolution

**Implementation**: ~4-5 hours
```rust
// Rust: Detect resource IDs
pub fn is_resource_id(value: i64) -> bool { ... }

// Python: Use external tool for resolution
def resolve_resource_id(apk_path: str, res_id: int) -> Optional[str]:
    """Use aapt2 to resolve resource ID"""
    result = subprocess.run(
        ["aapt2", "dump", "resources", apk_path],
        capture_output=True
    )
    # Parse aapt2 output to find resource
    return parse_aapt_output(result.stdout, res_id)
```

**Pros**:
- Leverages existing tools (aapt2 is reliable)
- Moderate implementation time
- Can fall back to detection-only if tool unavailable

**Cons**:
- External dependency
- Slower (subprocess calls)
- Platform-specific (aapt2 availability)

## Recommendation

### Immediate (0.5-1 hour): Resource ID Detection
Implement Option 1 (Minimal) to improve decompilation output:

```rust
// In expression_builder.rs or new resource_helper.rs
pub fn format_const_value(value: i64) -> String {
    if is_resource_id(value) {
        if let Some(type_name) = get_resource_type(value) {
            return format!("R.{}.0x{:x}", type_name, value & 0xFFFF);
        }
    }

    // Format as boolean or int
    match value {
        0 => "false".to_string(),
        1 => "true".to_string(),
        _ => value.to_string(),
    }
}
```

**Impact**: Immediately improves readability of decompiled code

### Future (if needed): Full Parser
Only implement Option 2 if:
1. Users frequently need resource resolution
2. Security analysis requires string extraction
3. External tools (aapt2) are not acceptable

### Alternative: Use Existing Library
Check if existing Rust crates can parse ARSC:
- androiders/android-resource-parser
- Or use Python's androguard via FFI

## Testing Plan

```python
def test_resource_id_detection():
    # Test with known resource IDs from real APK

    # String resource: 0x7f0e0001
    assert is_resource_id(0x7f0e0001) == True
    assert get_resource_type(0x7f0e0001) == "string"

    # Layout resource: 0x7f0c0042
    assert is_resource_id(0x7f0c0042) == True
    assert get_resource_type(0x7f0c0042) == "layout"

    # Not a resource ID
    assert is_resource_id(2131363364) == True  # 0x7f0e0b24
    assert is_resource_id(42) == False
    assert is_resource_id(0) == False
    assert is_resource_id(1) == False
```

## Decision

**Recommended Action**:
1. ✅ Implement Option 1 (Resource ID Detection) **NOW** (~1 hour)
   - Immediate value
   - No external dependencies
   - Easy to maintain

2. ⏳ Defer Option 2 (Full Parser) until specific need arises
   - Complex implementation
   - Limited immediate value for WebView analysis
   - Can add later if needed

3. 💡 Document workaround for users who need resolution:
   ```bash
   # Extract strings manually
   aapt2 dump strings app.apk

   # Or use apktool
   apktool d app.apk
   cat app/res/values/strings.xml
   ```

## Next Steps

If implementing Option 1:
1. Create `src/dex/resource_helper.rs`
2. Add `is_resource_id()` and `get_resource_type()` functions
3. Integrate into `expression_builder.rs` RegisterValue formatting
4. Add test cases
5. Update decompilation output

Estimated time: **0.5-1 hour**
