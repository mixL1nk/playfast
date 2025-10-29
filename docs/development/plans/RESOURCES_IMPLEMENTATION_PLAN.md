# Resources.arsc Implementation Plan

## Crate Evaluation Result

### ✅ Found: `arsc` crate (v0.1.5)
- **GitHub**: https://github.com/YaxinCheng/arsc
- **Crates.io**: https://crates.io/crates/arsc
- **Downloads**: 9,075+ total
- **License**: MIT

### Data Structures (from source analysis)

```rust
pub struct Arsc {
    pub packages: Vec<Package>,
    pub global_string_pool: StringPool,
}

pub struct Package {
    pub id: u32,
    pub name: String,
    pub type_names: StringPool,      // "string", "layout", "drawable"
    pub key_names: StringPool,        // "app_name", "button_ok"
    pub types: Vec<Type>,             // Resource types
    pub last_public_type: u32,
    pub last_public_key: u32,
}

pub struct Type {
    pub id: usize,
    pub specs: Option<Specs>,
    pub configs: Vec<Config>,         // Different configurations (locales, etc)
}

pub struct Config {
    pub type_id: usize,
    pub resources: Resources,
}

pub struct Resources {
    pub resources: Vec<ResourceEntry>,
    pub missing_entries: usize,
}

pub struct ResourceEntry {
    pub flags: u16,
    pub name_index: usize,            // Index in key_names pool
    pub value: ResourceValue,
    pub spec_id: usize,
}

pub enum ResourceValue {
    Bag { parent: u32, values: Vec<(u32, Value)> },
    Plain(Value),
}

pub struct Value {
    pub size: u16,
    pub r#type: u8,
    pub data_index: usize,            // Index in global_string_pool for strings
}
```

### API
```rust
use arsc::{parse, write};

let arsc = parse("/path/to/resources.arsc")?;
// Access: arsc.packages[0].types[0].configs[0].resources
```

## Decision: Use `arsc` Crate ✅

**Reasons**:
1. ✅ Already implements complete ARSC binary format parsing
2. ✅ Well-structured data model
3. ✅ MIT licensed (compatible with our project)
4. ✅ Saves 12-16 hours of implementation time
5. ✅ Battle-tested (9,000+ downloads)

**vs Custom Implementation**:
- ❌ Would take 12-16 hours
- ❌ Likely to have bugs with edge cases
- ❌ Maintenance burden
- ❌ Reinventing the wheel

## Implementation Plan

### Phase 1: Integration (2-3 hours)

#### Step 1.1: Add Dependency
```toml
# Cargo.toml
[dependencies]
arsc = "0.1.5"
```

#### Step 1.2: Create Resource Module
Create `src/apk/resources.rs`:

```rust
use arsc::{Arsc, Package, ResourceEntry, ResourceValue, Value};
use std::collections::HashMap;

/// Resource resolver for Android APK
pub struct ResourceResolver {
    arsc: Arsc,
    /// Cache: resource_id -> (type_name, key_name, value)
    cache: HashMap<u32, ResolvedResource>,
}

pub struct ResolvedResource {
    pub id: u32,
    pub type_name: String,    // "string", "layout", etc
    pub name: String,          // "app_name", "button_ok"
    pub value: ResourceData,
}

pub enum ResourceData {
    String(String),
    Integer(i32),
    Boolean(bool),
    Reference(u32),
    Unknown,
}

impl ResourceResolver {
    /// Create from raw ARSC bytes
    pub fn from_bytes(arsc_bytes: Vec<u8>) -> Result<Self> {
        // Use arsc crate to parse
        let arsc = arsc::parse_from(arsc_bytes.as_slice())?;

        // Build cache
        let cache = Self::build_cache(&arsc)?;

        Ok(Self { arsc, cache })
    }

    /// Resolve resource ID to value
    pub fn resolve(&self, resource_id: u32) -> Option<&ResolvedResource> {
        self.cache.get(&resource_id)
    }

    /// Check if value is a resource ID
    pub fn is_resource_id(value: i64) -> bool {
        // Android resource IDs have format: 0xPPTTEEEE
        // PP = package (usually 0x7f for app resources)
        // TT = type
        // EEEE = entry
        (value >> 24) == 0x7f || (value >> 24) == 0x01  // 0x01 = system resources
    }

    /// Build resource ID -> ResolvedResource cache
    fn build_cache(arsc: &Arsc) -> Result<HashMap<u32, ResolvedResource>> {
        let mut cache = HashMap::new();

        for package in &arsc.packages {
            for (type_idx, resource_type) in package.types.iter().enumerate() {
                let type_name = package.type_names.strings.get(type_idx)
                    .cloned()
                    .unwrap_or_default();

                for config in &resource_type.configs {
                    for entry in &config.resources.resources {
                        // Build resource ID: 0xPPTTEEEE
                        let resource_id = Self::build_resource_id(
                            package.id,
                            resource_type.id as u32,
                            entry.spec_id as u32
                        );

                        let name = package.key_names.strings
                            .get(entry.name_index)
                            .cloned()
                            .unwrap_or_default();

                        let value = Self::extract_value(
                            &entry.value,
                            &arsc.global_string_pool
                        );

                        cache.insert(resource_id, ResolvedResource {
                            id: resource_id,
                            type_name: type_name.clone(),
                            name,
                            value,
                        });
                    }
                }
            }
        }

        Ok(cache)
    }

    fn build_resource_id(package_id: u32, type_id: u32, entry_id: u32) -> u32 {
        (package_id << 24) | (type_id << 16) | entry_id
    }

    fn extract_value(
        resource_value: &ResourceValue,
        string_pool: &arsc::components::StringPool
    ) -> ResourceData {
        match resource_value {
            ResourceValue::Plain(value) => {
                match value.r#type {
                    0x03 => {  // TYPE_STRING
                        string_pool.strings.get(value.data_index)
                            .map(|s| ResourceData::String(s.clone()))
                            .unwrap_or(ResourceData::Unknown)
                    }
                    0x10 => {  // TYPE_INT_DEC
                        ResourceData::Integer(value.data_index as i32)
                    }
                    0x12 => {  // TYPE_INT_BOOLEAN
                        ResourceData::Boolean(value.data_index != 0)
                    }
                    0x01 => {  // TYPE_REFERENCE
                        ResourceData::Reference(value.data_index as u32)
                    }
                    _ => ResourceData::Unknown,
                }
            }
            ResourceValue::Bag { .. } => ResourceData::Unknown,
        }
    }
}
```

#### Step 1.3: Python Bindings
Add to `src/apk/resources.rs`:

```rust
use pyo3::prelude::*;
use serde::{Serialize, Deserialize};

#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PyResolvedResource {
    #[pyo3(get)]
    pub id: u32,
    #[pyo3(get)]
    pub type_name: String,
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub value_type: String,
    #[pyo3(get)]
    pub value: String,
}

#[pymethods]
impl PyResolvedResource {
    fn __repr__(&self) -> String {
        format!(
            "Resource(id=0x{:08x}, type={}, name={}, value={})",
            self.id, self.type_name, self.name, self.value
        )
    }
}

#[pyclass]
pub struct PyResourceResolver {
    resolver: ResourceResolver,
}

#[pymethods]
impl PyResourceResolver {
    /// Resolve a resource ID
    pub fn resolve(&self, resource_id: u32) -> Option<PyResolvedResource> {
        self.resolver.resolve(resource_id).map(|r| {
            let (value_type, value) = match &r.value {
                ResourceData::String(s) => ("string", s.clone()),
                ResourceData::Integer(i) => ("integer", i.to_string()),
                ResourceData::Boolean(b) => ("boolean", b.to_string()),
                ResourceData::Reference(r) => ("reference", format!("0x{:08x}", r)),
                ResourceData::Unknown => ("unknown", "?".to_string()),
            };

            PyResolvedResource {
                id: r.id,
                type_name: r.type_name.clone(),
                name: r.name.clone(),
                value_type: value_type.to_string(),
                value,
            }
        })
    }

    /// Check if a value looks like a resource ID
    #[staticmethod]
    pub fn is_resource_id(value: i64) -> bool {
        ResourceResolver::is_resource_id(value)
    }

    /// Get all string resources
    pub fn get_all_strings(&self) -> Vec<PyResolvedResource> {
        self.resolver.cache.values()
            .filter(|r| r.type_name == "string")
            .map(|r| /* convert to PyResolvedResource */)
            .collect()
    }
}

/// Parse resources.arsc from APK
#[pyfunction]
pub fn parse_resources_from_apk(apk_path: String) -> PyResult<PyResourceResolver> {
    use crate::apk::ApkExtractor;

    let extractor = ApkExtractor::new(&apk_path)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

    let arsc_bytes = extractor.extract_resources()
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

    let resolver = ResourceResolver::from_bytes(arsc_bytes)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(PyResourceResolver { resolver })
}
```

### Phase 2: Integration with Decompilation (1-2 hours)

#### Step 2.1: Enhanced Expression Formatting
Update `expression_builder.rs`:

```rust
pub struct ExpressionBuilder {
    resolver: MethodResolver,
    resource_resolver: Option<ResourceResolver>,  // NEW
    registers: HashMap<u8, RegisterValue>,
    pc: usize,
}

impl RegisterValue {
    pub fn format(&self, resource_resolver: Option<&ResourceResolver>) -> String {
        match self {
            RegisterValue::ConstInt(val) => {
                // Check if it's a resource ID
                if let Some(resolver) = resource_resolver {
                    if ResourceResolver::is_resource_id(*val) {
                        if let Some(resource) = resolver.resolve(*val as u32) {
                            return format!("R.{}.{}  /* {} */",
                                resource.type_name,
                                resource.name,
                                match &resource.value {
                                    ResourceData::String(s) => format!("\"{}\"", s),
                                    ResourceData::Boolean(b) => b.to_string(),
                                    ResourceData::Integer(i) => i.to_string(),
                                    _ => "?".to_string(),
                                }
                            );
                        }
                    }
                }

                // Format as boolean or regular int
                match *val {
                    0 => "false".to_string(),
                    1 => "true".to_string(),
                    _ => val.to_string(),
                }
            }
            // ... other cases
        }
    }
}
```

#### Step 2.2: Update Python API
```python
# With resource resolution:
class_info = core.decompile_class_from_apk(
    "app.apk",
    "WebViewActivity",
    resolve_resources=True  # NEW parameter
)

# Output improvement:
# Before: setJavaScriptEnabled(2131363364)
# After:  setJavaScriptEnabled(R.bool.enable_js  /* false */)
```

### Phase 3: Testing (1 hour)

Create `test_resources.py`:
```python
def test_resource_parsing():
    # Test 1: Parse resources
    resolver = core.parse_resources_from_apk("app.apk")

    # Test 2: Resolve specific ID
    res = resolver.resolve(0x7f0e0001)
    assert res.type_name == "string"
    assert res.name == "app_name"

    # Test 3: Get all strings
    strings = resolver.get_all_strings()
    print(f"Found {len(strings)} string resources")

    # Test 4: Integration with decompilation
    class_info = core.decompile_class_from_apk(
        "app.apk",
        "WebViewActivity",
        resolve_resources=True
    )
    # Check that resource IDs are resolved in expressions
```

## Timeline

| Phase | Task | Time |
|-------|------|------|
| 1.1 | Add arsc dependency | 10 min |
| 1.2 | Create ResourceResolver | 1.5 hours |
| 1.3 | Python bindings | 1 hour |
| 2.1 | Expression formatting | 45 min |
| 2.2 | API integration | 30 min |
| 3.0 | Testing | 1 hour |
| **Total** | | **~5 hours** |

## Benefits

### Before Implementation
```python
# Decompiled output:
setJavaScriptEnabled(2131363364)
setAllowFileAccess(2131363365)
loadUrl(2131363366)
```
**Problem**: What do these numbers mean?

### After Implementation
```python
# Decompiled output with resource resolution:
setJavaScriptEnabled(R.bool.enable_js  /* false */)
setAllowFileAccess(R.bool.allow_file  /* true */)
loadUrl(R.string.url  /* "https://example.com" */)
```
**Benefit**: Clear understanding of actual values!

## Security Analysis Use Cases

1. **Find hardcoded secrets**:
   ```python
   resolver = parse_resources_from_apk("app.apk")
   strings = resolver.get_all_strings()

   for s in strings:
       if "api_key" in s.name.lower() or "secret" in s.name.lower():
           print(f"⚠️  {s.name} = {s.value}")
   ```

2. **Analyze WebView settings**:
   - See actual boolean values for security settings
   - Identify which URLs are loaded
   - Check file access patterns

3. **Find internal URLs**:
   ```python
   for s in strings:
       if s.value.startswith("http"):
           print(f"URL found: {s.name} = {s.value}")
   ```

## Next Steps

1. ✅ Add `arsc = "0.1.5"` to Cargo.toml
2. ✅ Implement ResourceResolver
3. ✅ Add Python bindings
4. ✅ Integrate with expression builder
5. ✅ Test with real APK
6. ✅ Update documentation
