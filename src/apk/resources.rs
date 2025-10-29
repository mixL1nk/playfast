//! Android resources.arsc parser and resolver
//!
//! Parses resources.arsc binary format using the `arsc` crate and provides
//! convenient APIs for resource ID resolution and querying.

use arsc::components::{Arsc, ResourceValue, Value};
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::io::Cursor;

/// Resolved resource data
#[derive(Debug, Clone)]
pub enum ResourceData {
    String(String),
    Integer(i32),
    Boolean(bool),
    Reference(u32),
    Unknown,
}

/// A resolved resource with all metadata
#[derive(Debug, Clone)]
pub struct ResolvedResource {
    pub id: u32,
    pub type_name: String,
    pub name: String,
    pub value: ResourceData,
}

/// Python-friendly resolved resource
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

    /// Check if this is a string resource
    pub fn is_string(&self) -> bool {
        self.type_name == "string"
    }

    /// Check if this is a boolean resource
    pub fn is_boolean(&self) -> bool {
        self.type_name == "bool" || self.value_type == "boolean"
    }
}

/// Resource resolver
pub struct ResourceResolver {
    #[allow(dead_code)]
    arsc: Arsc,
    /// Cache: resource_id -> ResolvedResource
    cache: HashMap<u32, ResolvedResource>,
}

impl ResourceResolver {
    /// Create ResourceResolver from raw ARSC bytes
    pub fn from_bytes(arsc_bytes: Vec<u8>) -> Result<Self, String> {
        let cursor = Cursor::new(arsc_bytes);

        let arsc = arsc::parse_from(cursor)
            .map_err(|e| format!("Failed to parse ARSC: {:?}", e))?;

        let cache = Self::build_cache(&arsc)?;

        Ok(Self { arsc, cache })
    }

    /// Check if a value looks like a resource ID
    pub fn is_resource_id(value: i64) -> bool {
        // Android resource IDs have format: 0xPPTTEEEE
        // PP = package (0x7f for app, 0x01 for system)
        // TT = type
        // EEEE = entry
        let package_id = (value >> 24) & 0xFF;
        package_id == 0x7f || package_id == 0x01
    }

    /// Get resource type from ID
    pub fn get_resource_type_id(resource_id: u32) -> u8 {
        ((resource_id >> 16) & 0xFF) as u8
    }

    /// Get entry ID from resource ID
    pub fn get_entry_id(resource_id: u32) -> u16 {
        (resource_id & 0xFFFF) as u16
    }

    /// Resolve a resource ID to its value
    pub fn resolve(&self, resource_id: u32) -> Option<&ResolvedResource> {
        self.cache.get(&resource_id)
    }

    /// Get all resources of a specific type
    pub fn get_by_type(&self, type_name: &str) -> Vec<&ResolvedResource> {
        self.cache
            .values()
            .filter(|r| r.type_name == type_name)
            .collect()
    }

    /// Get all string resources
    pub fn get_all_strings(&self) -> Vec<&ResolvedResource> {
        self.get_by_type("string")
    }

    /// Build resource cache from ARSC
    fn build_cache(arsc: &Arsc) -> Result<HashMap<u32, ResolvedResource>, String> {
        let mut cache = HashMap::new();

        for package in &arsc.packages {
            for resource_type in &package.types {
                // Get type name (e.g., "string", "layout", "drawable")
                let type_name = package
                    .type_names
                    .strings
                    .get(resource_type.id - 1)  // type IDs are 1-based
                    .cloned()
                    .unwrap_or_else(|| format!("type_{}", resource_type.id));

                for config in &resource_type.configs {
                    for entry in &config.resources.resources {
                        // Build resource ID: 0xPPTTEEEE
                        let resource_id = Self::build_resource_id(
                            package.id as u8,
                            resource_type.id as u8,
                            entry.spec_id as u16,
                        );

                        // Get resource name
                        let name = package
                            .key_names
                            .strings
                            .get(entry.name_index)
                            .cloned()
                            .unwrap_or_else(|| format!("res_{}", entry.spec_id));

                        // Extract value
                        let value = Self::extract_value(&entry.value, &arsc.global_string_pool);

                        cache.insert(
                            resource_id,
                            ResolvedResource {
                                id: resource_id,
                                type_name: type_name.clone(),
                                name,
                                value,
                            },
                        );
                    }
                }
            }
        }

        Ok(cache)
    }

    /// Build resource ID from components
    fn build_resource_id(package_id: u8, type_id: u8, entry_id: u16) -> u32 {
        ((package_id as u32) << 24) | ((type_id as u32) << 16) | (entry_id as u32)
    }

    /// Extract value from ResourceValue
    fn extract_value(
        resource_value: &ResourceValue,
        string_pool: &arsc::components::StringPool,
    ) -> ResourceData {
        match resource_value {
            ResourceValue::Plain(value) => Self::extract_plain_value(value, string_pool),
            ResourceValue::Bag { .. } => ResourceData::Unknown,
        }
    }

    /// Extract value from plain Value
    fn extract_plain_value(value: &Value, string_pool: &arsc::components::StringPool) -> ResourceData {
        // Type constants from Android
        const TYPE_STRING: u8 = 0x03;
        const TYPE_INT_DEC: u8 = 0x10;
        const TYPE_INT_HEX: u8 = 0x11;
        const TYPE_INT_BOOLEAN: u8 = 0x12;
        const TYPE_REFERENCE: u8 = 0x01;

        match value.r#type {
            TYPE_STRING => {
                // data_index points to global string pool
                string_pool
                    .strings
                    .get(value.data_index)
                    .map(|s| ResourceData::String(s.clone()))
                    .unwrap_or(ResourceData::Unknown)
            }
            TYPE_INT_DEC | TYPE_INT_HEX => {
                // data_index is the actual integer value
                ResourceData::Integer(value.data_index as i32)
            }
            TYPE_INT_BOOLEAN => {
                // data_index is 0 (false) or -1/1 (true)
                ResourceData::Boolean(value.data_index != 0)
            }
            TYPE_REFERENCE => {
                // data_index is another resource ID
                ResourceData::Reference(value.data_index as u32)
            }
            _ => ResourceData::Unknown,
        }
    }
}

/// Python wrapper for ResourceResolver
#[pyclass]
pub struct PyResourceResolver {
    resolver: ResourceResolver,
}

#[pymethods]
impl PyResourceResolver {
    /// Resolve a resource ID to its value
    pub fn resolve(&self, resource_id: u32) -> Option<PyResolvedResource> {
        self.resolver.resolve(resource_id).map(|r| {
            let (value_type, value) = match &r.value {
                ResourceData::String(s) => ("string", s.clone()),
                ResourceData::Integer(i) => ("integer", i.to_string()),
                ResourceData::Boolean(b) => ("boolean", b.to_string()),
                ResourceData::Reference(ref_id) => ("reference", format!("0x{:08x}", ref_id)),
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
        self.resolver
            .get_all_strings()
            .iter()
            .map(|r| self.resolve(r.id).unwrap())
            .collect()
    }

    /// Get all resources of a specific type
    pub fn get_by_type(&self, type_name: String) -> Vec<PyResolvedResource> {
        self.resolver
            .get_by_type(&type_name)
            .iter()
            .map(|r| self.resolve(r.id).unwrap())
            .collect()
    }

    /// Get total number of resources
    pub fn count(&self) -> usize {
        self.resolver.cache.len()
    }

    fn __repr__(&self) -> String {
        format!("ResourceResolver(resources={})", self.count())
    }
}

/// Parse resources.arsc from APK
#[pyfunction]
pub fn parse_resources_from_apk(apk_path: String) -> PyResult<PyResourceResolver> {
    use crate::apk::ApkExtractor;

    let extractor = ApkExtractor::new(&apk_path)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

    if !extractor.has_resources() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "APK does not contain resources.arsc",
        ));
    }

    let arsc_bytes = extractor
        .extract_resources()
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

    let resolver = ResourceResolver::from_bytes(arsc_bytes)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;

    Ok(PyResourceResolver { resolver })
}
