use crate::apk::DexEntry;
use crate::dex::constants::structure;
use crate::dex::error::{DexError, Result};
use crate::dex::models::{RustDexClass, RustDexMethod, RustDexField};
use crate::dex::parser::DexParser;
use rayon::prelude::*;

/// Container managing multiple DEX files
pub struct DexContainer {
    dex_entries: Vec<DexEntry>,
}

impl DexContainer {
    /// Create a new DexContainer from DEX entries
    pub fn new(dex_entries: Vec<DexEntry>) -> Self {
        Self { dex_entries }
    }

    /// Get number of DEX files
    pub fn dex_count(&self) -> usize {
        self.dex_entries.len()
    }

    /// Get all DEX entries
    pub fn entries(&self) -> &[DexEntry] {
        &self.dex_entries
    }

    /// Extract all classes from all DEX files
    pub fn extract_all_classes(&self) -> Result<Vec<RustDexClass>> {
        let mut all_classes = Vec::new();

        for (index, _entry) in self.dex_entries.iter().enumerate() {
            let classes = self.extract_classes_from_dex(index)?;
            all_classes.extend(classes);
        }

        Ok(all_classes)
    }

    /// Extract all classes from all DEX files in parallel
    pub fn extract_all_classes_parallel(&self) -> Result<Vec<RustDexClass>> {
        let results: std::result::Result<Vec<Vec<RustDexClass>>, DexError> =
            (0..self.dex_entries.len())
                .into_par_iter()
                .map(|index| self.extract_classes_from_dex(index))
                .collect();

        Ok(results?.into_iter().flatten().collect())
    }

    /// Extract classes from a specific DEX file
    pub fn extract_classes_from_dex(&self, dex_index: usize) -> Result<Vec<RustDexClass>> {
        if dex_index >= self.dex_entries.len() {
            return Err(DexError::InvalidDex(format!(
                "DEX index {} out of bounds (max: {})",
                dex_index,
                self.dex_entries.len()
            )));
        }

        let entry = &self.dex_entries[dex_index];
        let parser = DexParser::new(entry.data.clone())?;

        let mut classes = Vec::new();
        let class_count = parser.class_count();

        // Iterate through all class definitions
        for class_idx in 0..class_count {
            match self.parse_class(&parser, class_idx) {
                Ok(class) => classes.push(class),
                Err(e) => {
                    // Log error but continue with other classes
                    eprintln!("Warning: Failed to parse class {}: {:?}", class_idx, e);
                    continue;
                }
            }
        }

        Ok(classes)
    }

    /// Parse a single class
    fn parse_class(&self, parser: &DexParser, class_idx: u32) -> Result<RustDexClass> {
        let class_def = parser.get_class_def(class_idx)?;

        // Get class name
        let class_name = parser.get_type_name(class_def.class_idx)?;
        let mut rust_class = RustDexClass::new(class_name);
        rust_class.access_flags = class_def.access_flags;

        // Get superclass
        if class_def.superclass_idx != structure::NO_INDEX {
            match parser.get_type_name(class_def.superclass_idx) {
                Ok(superclass) => rust_class.superclass = Some(superclass),
                Err(_) => {} // Skip if we can't get the superclass
            }
        }

        // Parse class data (fields and methods)
        if class_def.class_data_off != 0 {
            let class_data = parser.parse_class_data(class_def.class_data_off)?;

            // Parse static fields
            for encoded_field in &class_data.static_fields {
                match self.parse_field(parser, encoded_field.field_idx, encoded_field.access_flags | 0x0008) {
                    Ok(field) => rust_class.fields.push(field),
                    Err(_) => continue,
                }
            }

            // Parse instance fields
            for encoded_field in &class_data.instance_fields {
                match self.parse_field(parser, encoded_field.field_idx, encoded_field.access_flags) {
                    Ok(field) => rust_class.fields.push(field),
                    Err(_) => continue,
                }
            }

            // Parse direct methods
            for encoded_method in &class_data.direct_methods {
                match self.parse_method(parser, encoded_method.method_idx, encoded_method.access_flags) {
                    Ok(method) => rust_class.methods.push(method),
                    Err(_) => continue,
                }
            }

            // Parse virtual methods
            for encoded_method in &class_data.virtual_methods {
                match self.parse_method(parser, encoded_method.method_idx, encoded_method.access_flags) {
                    Ok(method) => rust_class.methods.push(method),
                    Err(_) => continue,
                }
            }
        }

        Ok(rust_class)
    }

    /// Parse a field
    fn parse_field(&self, parser: &DexParser, field_idx: u32, access_flags: u32) -> Result<RustDexField> {
        let field_info = parser.get_field_info(field_idx)?;

        let field_name = parser.get_string(field_info.name_idx)?;
        let field_type = parser.get_type_name(field_info.type_idx)?;
        let declaring_class = parser.get_type_name(field_info.class_idx)?;

        Ok(RustDexField::new(
            field_name,
            field_type,
            declaring_class,
            access_flags,
        ))
    }

    /// Parse a method
    fn parse_method(&self, parser: &DexParser, method_idx: u32, access_flags: u32) -> Result<RustDexMethod> {
        let method_info = parser.get_method_info(method_idx)?;
        let proto_info = parser.get_proto_info(method_info.proto_idx)?;

        let method_name = parser.get_string(method_info.name_idx)?;
        let declaring_class = parser.get_type_name(method_info.class_idx)?;

        // Get parameter types
        let mut parameters = Vec::new();
        for param_idx in &proto_info.parameters {
            match parser.get_type_name(*param_idx) {
                Ok(param_type) => parameters.push(param_type),
                Err(_) => parameters.push("unknown".to_string()),
            }
        }

        // Get return type
        let return_type = parser.get_type_name(proto_info.return_type_idx)
            .unwrap_or_else(|_| "void".to_string());

        Ok(RustDexMethod::new(
            method_name,
            parameters,
            return_type,
            declaring_class,
            access_flags,
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dex_container_creation() {
        let entries = vec![
            DexEntry::new("classes.dex".to_string(), 0, vec![]),
            DexEntry::new("classes2.dex".to_string(), 1, vec![]),
        ];

        let container = DexContainer::new(entries);
        assert_eq!(container.dex_count(), 2);
    }
}
