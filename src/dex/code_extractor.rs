//! Extract method bytecode from DEX files

use pyo3::prelude::*;

use super::decoder::DexDecoder;
use super::parser::DexParser;

/// Extract bytecode for methods from classes in an APK
///
/// This is a simplified version that extracts bytecode for methods
/// by searching through DEX files in the APK.
#[pyfunction]
pub fn extract_methods_bytecode(
    apk_path: String,
    classes: Vec<crate::dex::models::RustDexClass>,
) -> PyResult<Vec<(String, String, Vec<u16>)>> {
    use crate::apk::ApkExtractor;

    let extractor = ApkExtractor::new(&apk_path)
        .map_err(|e| pyo3::exceptions::PyException::new_err(e.to_string()))?;

    let dex_entries = extractor.dex_entries().to_vec();
    let mut results = Vec::new();

    // For each class, find its methods' bytecode
    for class in classes {
        // Try each DEX file
        for dex_entry in &dex_entries {
            let parser = match DexParser::new(dex_entry.data.clone()) {
                Ok(p) => p,
                Err(_) => continue,
            };

            // Search through all classes in this DEX
            for class_idx in 0..parser.class_count() {
                let class_def = match parser.get_class_def(class_idx) {
                    Ok(c) => c,
                    Err(_) => continue,
                };

                let class_type_name = match parser.get_type_name(class_def.class_idx) {
                    Ok(n) => n,
                    Err(_) => continue,
                };

                if class_type_name == class.class_name {
                    // Found the class - extract methods
                    let class_data = match parser.parse_class_data(class_def.class_data_off) {
                        Ok(d) => d,
                        Err(_) => continue,
                    };

                    // Extract bytecode for each method
                    for encoded_method in class_data
                        .direct_methods
                        .iter()
                        .chain(class_data.virtual_methods.iter())
                    {
                        let method_info = match parser.get_method_info(encoded_method.method_idx) {
                            Ok(m) => m,
                            Err(_) => continue,
                        };

                        let method_name = match parser.get_string(method_info.name_idx) {
                            Ok(n) => n,
                            Err(_) => continue,
                        };

                        let bytecode = if encoded_method.code_off > 0 {
                            match parser.get_method_bytecode(encoded_method.code_off) {
                                Ok(b) => b,
                                Err(_) => Vec::new(),
                            }
                        } else {
                            Vec::new()
                        };

                        results.push((class.class_name.clone(), method_name, bytecode));
                    }

                    break;
                }
            }
        }
    }

    Ok(results)
}

/// Get bytecode for a specific method by name
///
/// Searches through all DEX files in an APK until it finds the method.
#[pyfunction]
pub fn get_method_bytecode_from_apk(
    apk_path: String,
    class_name: String,
    method_name: String,
) -> PyResult<Vec<u16>> {
    use crate::apk::ApkExtractor;

    let extractor = ApkExtractor::new(&apk_path)
        .map_err(|e| pyo3::exceptions::PyException::new_err(e.to_string()))?;

    // Try each DEX file
    for dex_entry in extractor.dex_entries() {
        let parser = match DexParser::new(dex_entry.data.clone()) {
            Ok(p) => p,
            Err(_) => continue,
        };

        // Search through all classes
        for class_idx in 0..parser.class_count() {
            let class_def = match parser.get_class_def(class_idx) {
                Ok(c) => c,
                Err(_) => continue,
            };

            let class_type_name = match parser.get_type_name(class_def.class_idx) {
                Ok(n) => n,
                Err(_) => continue,
            };

            if class_type_name == class_name {
                // Found the class - search for method
                let class_data = match parser.parse_class_data(class_def.class_data_off) {
                    Ok(d) => d,
                    Err(_) => continue,
                };

                for encoded_method in class_data
                    .direct_methods
                    .iter()
                    .chain(class_data.virtual_methods.iter())
                {
                    let method_info = match parser.get_method_info(encoded_method.method_idx) {
                        Ok(m) => m,
                        Err(_) => continue,
                    };

                    let found_method_name = match parser.get_string(method_info.name_idx) {
                        Ok(n) => n,
                        Err(_) => continue,
                    };

                    if found_method_name == method_name {
                        // Found the method!
                        return if encoded_method.code_off > 0 {
                            parser
                                .get_method_bytecode(encoded_method.code_off)
                                .map_err(|e| pyo3::exceptions::PyException::new_err(e.to_string()))
                        } else {
                            Ok(Vec::new())
                        };
                    }
                }
            }
        }
    }

    Err(pyo3::exceptions::PyException::new_err(format!(
        "Method not found: {}.{}",
        class_name, method_name
    )))
}

/// Find method bytecode (non-Python version for internal use)
pub fn find_method_bytecode(
    parser: &DexParser,
    class_name: &str,
    method_name: &str,
) -> Result<Option<Vec<u16>>, String> {
    // Search through all classes
    for class_idx in 0..parser.class_count() {
        let class_def = parser.get_class_def(class_idx).map_err(|e| e.to_string())?;
        let class_type_name = parser.get_type_name(class_def.class_idx).map_err(|e| e.to_string())?;

        if class_type_name == class_name {
            // Found the class - search for method
            let class_data = parser.parse_class_data(class_def.class_data_off).map_err(|e| e.to_string())?;

            for encoded_method in class_data
                .direct_methods
                .iter()
                .chain(class_data.virtual_methods.iter())
            {
                let method_info = parser.get_method_info(encoded_method.method_idx).map_err(|e| e.to_string())?;
                let found_method_name = parser.get_string(method_info.name_idx).map_err(|e| e.to_string())?;

                if found_method_name == method_name {
                    // Found the method!
                    return if encoded_method.code_off > 0 {
                        Ok(Some(parser.get_method_bytecode(encoded_method.code_off).map_err(|e| e.to_string())?))
                    } else {
                        Ok(Some(Vec::new()))
                    };
                }
            }
        }
    }

    Ok(None)
}
