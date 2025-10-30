use crate::dex::models::{RustDexClass, RustDexMethod};
use pyo3::prelude::*;

/// Filter for finding classes
#[pyclass]
#[derive(Debug, Clone, Default)]
pub struct ClassFilter {
    #[pyo3(get, set)]
    pub packages: Vec<String>,
    #[pyo3(get, set)]
    pub exclude_packages: Vec<String>,
    #[pyo3(get, set)]
    pub class_name: Option<String>,
    #[pyo3(get, set)]
    pub modifiers: Option<u32>,
}

#[pymethods]
impl ClassFilter {
    /// Create a new empty ClassFilter
    #[new]
    #[pyo3(signature = (packages=None, exclude_packages=None, class_name=None, modifiers=None))]
    pub fn new(
        packages: Option<Vec<String>>,
        exclude_packages: Option<Vec<String>>,
        class_name: Option<String>,
        modifiers: Option<u32>,
    ) -> Self {
        Self {
            packages: packages.unwrap_or_default(),
            exclude_packages: exclude_packages.unwrap_or_default(),
            class_name,
            modifiers,
        }
    }

    /// Check if a class matches this filter
    pub fn matches(&self, class: &RustDexClass) -> bool {
        // Check packages (include)
        if !self.packages.is_empty() {
            let matches_package = self.packages.iter().any(|pkg| {
                class.package_name.starts_with(pkg)
            });
            if !matches_package {
                return false;
            }
        }

        // Check excluded packages
        if !self.exclude_packages.is_empty() {
            let excluded = self.exclude_packages.iter().any(|pkg| {
                class.package_name.starts_with(pkg)
            });
            if excluded {
                return false;
            }
        }

        // Check class name
        if let Some(ref name) = self.class_name {
            if !class.class_name.contains(name) && !class.simple_name.contains(name) {
                return false;
            }
        }

        // Check modifiers
        if let Some(required_flags) = self.modifiers {
            if class.access_flags & required_flags != required_flags {
                return false;
            }
        }

        true
    }
}

/// Builder for ClassFilter
/// Note: Reserved for future use. Python API uses ClassFilter directly.
#[allow(dead_code)]
#[derive(Debug, Default)]
pub struct ClassFilterBuilder {
    packages: Vec<String>,
    exclude_packages: Vec<String>,
    class_name: Option<String>,
    modifiers: Option<u32>,
}

impl ClassFilterBuilder {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn packages(mut self, packages: Vec<String>) -> Self {
        self.packages = packages;
        self
    }

    pub fn exclude_packages(mut self, exclude: Vec<String>) -> Self {
        self.exclude_packages = exclude;
        self
    }

    pub fn class_name(mut self, name: String) -> Self {
        self.class_name = Some(name);
        self
    }

    pub fn modifiers(mut self, flags: u32) -> Self {
        self.modifiers = Some(flags);
        self
    }

    pub fn build(self) -> ClassFilter {
        ClassFilter {
            packages: self.packages,
            exclude_packages: self.exclude_packages,
            class_name: self.class_name,
            modifiers: self.modifiers,
        }
    }
}

/// Filter for finding methods
#[pyclass]
#[derive(Debug, Clone, Default)]
pub struct MethodFilter {
    #[pyo3(get, set)]
    pub method_name: Option<String>,
    #[pyo3(get, set)]
    pub param_count: Option<usize>,
    #[pyo3(get, set)]
    pub param_types: Vec<String>,
    #[pyo3(get, set)]
    pub return_type: Option<String>,
    #[pyo3(get, set)]
    pub modifiers: Option<u32>,
}

#[pymethods]
impl MethodFilter {
    /// Create a new empty MethodFilter
    #[new]
    #[pyo3(signature = (method_name=None, param_count=None, param_types=None, return_type=None, modifiers=None))]
    pub fn new(
        method_name: Option<String>,
        param_count: Option<usize>,
        param_types: Option<Vec<String>>,
        return_type: Option<String>,
        modifiers: Option<u32>,
    ) -> Self {
        Self {
            method_name,
            param_count,
            param_types: param_types.unwrap_or_default(),
            return_type,
            modifiers,
        }
    }

    /// Check if a method matches this filter
    pub fn matches(&self, method: &RustDexMethod) -> bool {
        // Check method name
        if let Some(ref name) = self.method_name {
            if !method.name.contains(name) {
                return false;
            }
        }

        // Check parameter count
        if let Some(count) = self.param_count {
            if method.parameters.len() != count {
                return false;
            }
        }

        // Check parameter types
        if !self.param_types.is_empty() {
            if method.parameters.len() != self.param_types.len() {
                return false;
            }
            for (i, param_type) in self.param_types.iter().enumerate() {
                if !method.parameters[i].contains(param_type) {
                    return false;
                }
            }
        }

        // Check return type
        if let Some(ref ret_type) = self.return_type {
            if !method.return_type.contains(ret_type) {
                return false;
            }
        }

        // Check modifiers
        if let Some(required_flags) = self.modifiers {
            if method.access_flags & required_flags != required_flags {
                return false;
            }
        }

        true
    }
}

/// Builder for MethodFilter
/// Note: Reserved for future use. Python API uses MethodFilter directly.
#[allow(dead_code)]
#[derive(Debug, Default)]
pub struct MethodFilterBuilder {
    method_name: Option<String>,
    param_count: Option<usize>,
    param_types: Vec<String>,
    return_type: Option<String>,
    modifiers: Option<u32>,
}

impl MethodFilterBuilder {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn method_name(mut self, name: String) -> Self {
        self.method_name = Some(name);
        self
    }

    pub fn param_count(mut self, count: usize) -> Self {
        self.param_count = Some(count);
        self
    }

    pub fn param_types(mut self, types: Vec<String>) -> Self {
        self.param_types = types;
        self
    }

    pub fn return_type(mut self, ret_type: String) -> Self {
        self.return_type = Some(ret_type);
        self
    }

    pub fn modifiers(mut self, flags: u32) -> Self {
        self.modifiers = Some(flags);
        self
    }

    pub fn build(self) -> MethodFilter {
        MethodFilter {
            method_name: self.method_name,
            param_count: self.param_count,
            param_types: self.param_types,
            return_type: self.return_type,
            modifiers: self.modifiers,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_class_filter_builder() {
        let filter = ClassFilter::new(
            Some(vec!["com.example".to_string()]),
            None,
            Some("MainActivity".to_string()),
            None,
        );

        assert_eq!(filter.packages.len(), 1);
        assert_eq!(filter.class_name, Some("MainActivity".to_string()));
    }

    #[test]
    fn test_method_filter_builder() {
        let filter = MethodFilter::new(
            Some("onCreate".to_string()),
            Some(1),
            None,
            None,
            None,
        );

        assert_eq!(filter.method_name, Some("onCreate".to_string()));
        assert_eq!(filter.param_count, Some(1));
    }
}
