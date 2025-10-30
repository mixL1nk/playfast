//! Method Index Resolution
//!
//! Resolves method_idx to human-readable method signatures

use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

use super::error::Result;
use super::parser::DexParser;

/// Resolved method signature
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MethodSignature {
    /// Full class name (e.g., "android.webkit.WebSettings")
    #[pyo3(get)]
    pub class_name: String,

    /// Method name (e.g., "setJavaScriptEnabled")
    #[pyo3(get)]
    pub method_name: String,

    /// Parameter types (e.g., ["boolean"])
    #[pyo3(get)]
    pub parameters: Vec<String>,

    /// Return type (e.g., "void")
    #[pyo3(get)]
    pub return_type: String,

    /// Full signature for display
    #[pyo3(get)]
    pub full_signature: String,
}

#[pymethods]
impl MethodSignature {
    /// Get simple class name (last component)
    pub fn simple_class_name(&self) -> String {
        self.class_name
            .split('.')
            .last()
            .unwrap_or(&self.class_name)
            .to_string()
    }

    /// Check if this is a WebView-related method
    pub fn is_webview_method(&self) -> bool {
        self.class_name.contains("WebView") || self.class_name.contains("WebSettings")
    }

    /// Check if this is setJavaScriptEnabled
    pub fn is_set_javascript_enabled(&self) -> bool {
        self.method_name == "setJavaScriptEnabled"
    }

    /// Check if this is addJavascriptInterface
    pub fn is_add_javascript_interface(&self) -> bool {
        self.method_name == "addJavascriptInterface"
    }

    /// Format as Java-like method call
    pub fn format_call(&self, args: Vec<String>) -> String {
        format!(
            "{}.{}({})",
            self.simple_class_name()
                .chars()
                .next()
                .map(|c| c.to_lowercase().to_string())
                .unwrap_or_default()
                + &self.simple_class_name()[1..],
            self.method_name,
            args.join(", ")
        )
    }

    /// String representation
    pub fn __repr__(&self) -> String {
        self.full_signature.clone()
    }

    /// Convert to dict
    pub fn to_dict(&self, py: Python) -> PyResult<Py<pyo3::types::PyAny>> {
        let dict = pyo3::types::PyDict::new(py);
        dict.set_item("class_name", &self.class_name)?;
        dict.set_item("method_name", &self.method_name)?;
        dict.set_item("parameters", &self.parameters)?;
        dict.set_item("return_type", &self.return_type)?;
        dict.set_item("full_signature", &self.full_signature)?;
        Ok(dict.into())
    }
}

/// Method Resolver
pub struct MethodResolver {
    pub parser: DexParser,
}

impl MethodResolver {
    /// Create a new method resolver
    pub fn new(parser: DexParser) -> Self {
        Self { parser }
    }

    /// Resolve string index
    pub fn resolve_string(&self, string_idx: u32) -> Result<String> {
        self.parser.get_string(string_idx)
    }

    /// Resolve method index to method signature
    pub fn resolve(&self, method_idx: u32) -> Result<MethodSignature> {
        // Get method_id_item
        let method_info = self.parser.get_method_info(method_idx)?;

        // Get class name
        let class_name = self.parser.get_type_name(method_info.class_idx)?;

        // Get method name
        let method_name = self.parser.get_string(method_info.name_idx)?;

        // Get prototype (parameters + return type)
        let proto = self.parser.get_proto_info(method_info.proto_idx)?;

        // Get return type
        let return_type = self.parser.get_type_name(proto.return_type_idx)?;

        // Get parameter types
        let mut parameters = Vec::new();
        for &param_type_idx in &proto.parameters {
            let param_type = self.parser.get_type_name(param_type_idx)?;
            parameters.push(param_type);
        }

        // Build full signature
        let full_signature = format!(
            "{}.{}({}): {}",
            class_name,
            method_name,
            parameters.join(", "),
            return_type
        );

        Ok(MethodSignature {
            class_name,
            method_name,
            parameters,
            return_type,
            full_signature,
        })
    }

    /// Resolve multiple method indices
    pub fn resolve_many(&self, method_indices: &[u32]) -> Vec<Result<MethodSignature>> {
        method_indices
            .iter()
            .map(|&idx| self.resolve(idx))
            .collect()
    }
}

/// Create a method resolver from DEX data (Python API)
#[pyfunction]
pub fn create_method_resolver(dex_data: Vec<u8>) -> PyResult<MethodResolverPy> {
    let parser = DexParser::new(dex_data)
        .map_err(|e| pyo3::exceptions::PyException::new_err(e.to_string()))?;
    let resolver = MethodResolver::new(parser);

    Ok(MethodResolverPy { resolver })
}

/// Python wrapper for MethodResolver
#[pyclass]
pub struct MethodResolverPy {
    resolver: MethodResolver,
}

#[pymethods]
impl MethodResolverPy {
    /// Resolve a single method index
    pub fn resolve(&self, method_idx: u32) -> PyResult<MethodSignature> {
        self.resolver
            .resolve(method_idx)
            .map_err(|e| pyo3::exceptions::PyException::new_err(e.to_string()))
    }

    /// Resolve multiple method indices
    pub fn resolve_many(&self, method_indices: Vec<u32>) -> PyResult<Vec<MethodSignature>> {
        let results = self.resolver.resolve_many(&method_indices);

        // Filter out errors and collect successes
        let signatures: Vec<MethodSignature> = results
            .into_iter()
            .filter_map(|r| r.ok())
            .collect();

        Ok(signatures)
    }
}

/// Resolve method index from APK
///
/// Searches through all DEX files in the APK until it finds the method index.
#[pyfunction]
pub fn resolve_method_from_apk(
    apk_path: String,
    method_idx: u32,
) -> PyResult<MethodSignature> {
    use crate::apk::ApkExtractor;

    let extractor = ApkExtractor::new(&apk_path)
        .map_err(|e| pyo3::exceptions::PyException::new_err(e.to_string()))?;

    // Try each DEX file
    for dex_entry in extractor.dex_entries() {
        if let Ok(parser) = DexParser::new(dex_entry.data.clone()) {
            let resolver = MethodResolver::new(parser);
            if let Ok(signature) = resolver.resolve(method_idx) {
                return Ok(signature);
            }
        }
    }

    Err(pyo3::exceptions::PyException::new_err(format!(
        "Method index {} not found in any DEX file",
        method_idx
    )))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_method_signature_simple_name() {
        let sig = MethodSignature {
            class_name: "android.webkit.WebSettings".to_string(),
            method_name: "setJavaScriptEnabled".to_string(),
            parameters: vec!["boolean".to_string()],
            return_type: "void".to_string(),
            full_signature: "android.webkit.WebSettings.setJavaScriptEnabled(boolean): void"
                .to_string(),
        };

        assert_eq!(sig.simple_class_name(), "WebSettings");
        assert!(sig.is_webview_method());
        assert!(sig.is_set_javascript_enabled());
    }

    #[test]
    fn test_format_call() {
        let sig = MethodSignature {
            class_name: "android.webkit.WebSettings".to_string(),
            method_name: "setJavaScriptEnabled".to_string(),
            parameters: vec!["boolean".to_string()],
            return_type: "void".to_string(),
            full_signature: String::new(),
        };

        let formatted = sig.format_call(vec!["true".to_string()]);
        assert_eq!(formatted, "webSettings.setJavaScriptEnabled(true)");
    }
}
