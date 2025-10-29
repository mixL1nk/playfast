//! Class-level decompilation
//!
//! Decompile entire classes including metadata and all methods

use crate::dex::expression_builder::{ExpressionBuilder, ReconstructedExpression};
use crate::dex::parser::{DexParser, ClassDef, EncodedMethod};
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

/// Decompiled method with metadata
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecompiledMethod {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub signature: String,
    #[pyo3(get)]
    pub access_flags: u32,
    #[pyo3(get)]
    pub is_public: bool,
    #[pyo3(get)]
    pub is_private: bool,
    #[pyo3(get)]
    pub is_static: bool,
    #[pyo3(get)]
    pub parameters: Vec<String>,
    #[pyo3(get)]
    pub return_type: String,
    #[pyo3(get)]
    pub expressions: Vec<ReconstructedExpression>,
    #[pyo3(get)]
    pub bytecode_size: usize,
}

#[pymethods]
impl DecompiledMethod {
    /// Check if method has security-relevant calls
    pub fn has_security_calls(&self) -> bool {
        self.expressions.iter().any(|e| {
            e.expression.contains("JavaScript")
                || e.expression.contains("setAllowFileAccess")
                || e.expression.contains("setMixedContentMode")
        })
    }

    /// Get all WebView-related expressions
    pub fn get_webview_expressions(&self) -> Vec<ReconstructedExpression> {
        self.expressions
            .iter()
            .filter(|e| e.expression.contains("WebView") || e.expression.contains("WebSettings"))
            .cloned()
            .collect()
    }

    fn __repr__(&self) -> String {
        format!("DecompiledMethod(name='{}', expressions={})", self.name, self.expressions.len())
    }
}

/// Decompiled class with full metadata
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DecompiledClass {
    #[pyo3(get)]
    pub class_name: String,
    #[pyo3(get)]
    pub package: String,
    #[pyo3(get)]
    pub simple_name: String,
    #[pyo3(get)]
    pub superclass: Option<String>,
    #[pyo3(get)]
    pub interfaces: Vec<String>,
    #[pyo3(get)]
    pub fields: Vec<String>,
    #[pyo3(get)]
    pub methods: Vec<DecompiledMethod>,
    #[pyo3(get)]
    pub access_flags: u32,
}

#[pymethods]
impl DecompiledClass {
    /// Get methods with security-relevant calls
    pub fn get_security_methods(&self) -> Vec<DecompiledMethod> {
        self.methods
            .iter()
            .filter(|m| m.has_security_calls())
            .cloned()
            .collect()
    }

    /// Get all methods that use WebView
    pub fn get_webview_methods(&self) -> Vec<DecompiledMethod> {
        self.methods
            .iter()
            .filter(|m| !m.get_webview_expressions().is_empty())
            .cloned()
            .collect()
    }

    /// Check if class is public
    pub fn is_public(&self) -> bool {
        self.access_flags & 0x0001 != 0
    }

    /// Check if class is final
    pub fn is_final(&self) -> bool {
        self.access_flags & 0x0010 != 0
    }

    /// Check if class is abstract
    pub fn is_abstract(&self) -> bool {
        self.access_flags & 0x0400 != 0
    }

    /// Get summary statistics
    pub fn get_summary(&self) -> String {
        let security_count = self.get_security_methods().len();
        let webview_count = self.get_webview_methods().len();
        format!(
            "Class: {}\nMethods: {}\nSecurity-relevant: {}\nWebView usage: {}",
            self.class_name,
            self.methods.len(),
            security_count,
            webview_count
        )
    }

    fn __repr__(&self) -> String {
        format!(
            "DecompiledClass(name='{}', methods={})",
            self.class_name,
            self.methods.len()
        )
    }
}

/// Decompile entire class from APK
#[pyfunction]
pub fn decompile_class_from_apk(apk_path: String, class_name: String) -> PyResult<DecompiledClass> {
    use crate::apk::ApkExtractor;

    let extractor = ApkExtractor::new(&apk_path)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

    // Search through DEX files
    for dex_entry in extractor.dex_entries() {
        if let Ok(parser) = DexParser::new(dex_entry.data.clone()) {
            // Find the class
            for class_idx in 0..parser.class_count() {
                let class_def = match parser.get_class_def(class_idx) {
                    Ok(c) => c,
                    Err(_) => continue,
                };

                let found_class_name = match parser.get_type_name(class_def.class_idx) {
                    Ok(n) => n,
                    Err(_) => continue,
                };

                if found_class_name == class_name {
                    // Found the class - decompile it
                    return decompile_class(&parser, class_def, &dex_entry.data);
                }
            }
        }
    }

    Err(pyo3::exceptions::PyValueError::new_err(format!(
        "Class not found: {}",
        class_name
    )))
}

/// Internal function to decompile a class
pub fn decompile_class(
    parser: &DexParser,
    class_def: ClassDef,
    dex_data: &[u8],
) -> PyResult<DecompiledClass> {
    // Get class metadata
    let class_name = parser
        .get_type_name(class_def.class_idx)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    let (package, simple_name) = split_class_name(&class_name);

    let superclass = if class_def.superclass_idx != 0xFFFFFFFF {
        parser.get_type_name(class_def.superclass_idx).ok()
    } else {
        None
    };

    // Get interfaces (for now, skip if we can't parse)
    let interfaces = Vec::new();
    // TODO: Implement proper interface parsing if needed
    // This requires parsing type_list from interfaces_off

    // Get fields
    let mut fields = Vec::new();
    if let Ok(class_data) = parser.parse_class_data(class_def.class_data_off) {
        for field in class_data.static_fields.iter().chain(class_data.instance_fields.iter()) {
            if let Ok(field_info) = parser.get_field_info(field.field_idx) {
                if let Ok(field_name) = parser.get_string(field_info.name_idx) {
                    if let Ok(field_type) = parser.get_type_name(field_info.type_idx) {
                        fields.push(format!("{}: {}", field_name, field_type));
                    }
                }
            }
        }
    }

    // Decompile all methods
    let mut methods = Vec::new();
    if let Ok(class_data) = parser.parse_class_data(class_def.class_data_off) {
        for encoded_method in class_data.direct_methods.iter().chain(class_data.virtual_methods.iter()) {
            if let Ok(method) = decompile_method(parser, encoded_method, &dex_data) {
                methods.push(method);
            }
        }
    }

    Ok(DecompiledClass {
        class_name,
        package,
        simple_name,
        superclass,
        interfaces,
        fields,
        methods,
        access_flags: class_def.access_flags,
    })
}

/// Decompile a single method
fn decompile_method(
    parser: &DexParser,
    encoded_method: &EncodedMethod,
    dex_data: &[u8],
) -> Result<DecompiledMethod, String> {
    // Get method info
    let method_info = parser.get_method_info(encoded_method.method_idx).map_err(|e| e.to_string())?;
    let method_name = parser.get_string(method_info.name_idx).map_err(|e| e.to_string())?;

    // Get prototype
    let proto = parser.get_proto_info(method_info.proto_idx).map_err(|e| e.to_string())?;
    let return_type = parser.get_type_name(proto.return_type_idx).map_err(|e| e.to_string())?;

    let mut parameters = Vec::new();
    for &param_type_idx in &proto.parameters {
        parameters.push(parser.get_type_name(param_type_idx).map_err(|e| e.to_string())?);
    }

    let signature = format!("{}({}): {}", method_name, parameters.join(", "), return_type);

    // Access flags
    let is_public = encoded_method.access_flags & 0x0001 != 0;
    let is_private = encoded_method.access_flags & 0x0002 != 0;
    let is_static = encoded_method.access_flags & 0x0008 != 0;

    // Get bytecode and decompile
    let (expressions, bytecode_size) = if encoded_method.code_off > 0 {
        if let Ok(bytecode) = parser.get_method_bytecode(encoded_method.code_off) {
            let size = bytecode.len();

            // Create expression builder
            if let Ok(parser2) = DexParser::new(dex_data.to_vec()) {
                let mut builder = ExpressionBuilder::new(parser2);
                let exprs = builder.process_bytecode(&bytecode).unwrap_or_default();
                (exprs, size)
            } else {
                (Vec::new(), size)
            }
        } else {
            (Vec::new(), 0)
        }
    } else {
        (Vec::new(), 0)
    };

    Ok(DecompiledMethod {
        name: method_name,
        signature,
        access_flags: encoded_method.access_flags,
        is_public,
        is_private,
        is_static,
        parameters,
        return_type,
        expressions,
        bytecode_size,
    })
}

/// Split class name into package and simple name
fn split_class_name(class_name: &str) -> (String, String) {
    let name = class_name.trim_matches('L').trim_matches(';').replace('/', ".");

    if let Some(last_dot) = name.rfind('.') {
        let package = name[..last_dot].to_string();
        let simple = name[last_dot + 1..].to_string();
        (package, simple)
    } else {
        (String::new(), name)
    }
}
