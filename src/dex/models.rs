use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

/// Reference pool containing strings, types, fields, and methods from DEX
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RustReferencePool {
    #[pyo3(get)]
    pub strings: Vec<String>,
    #[pyo3(get)]
    pub types: Vec<String>,
    #[pyo3(get)]
    pub fields: Vec<String>,
    #[pyo3(get)]
    pub methods: Vec<String>,
}

#[pymethods]
impl RustReferencePool {
    #[new]
    pub fn new() -> Self {
        Self {
            strings: Vec::new(),
            types: Vec::new(),
            fields: Vec::new(),
            methods: Vec::new(),
        }
    }

    /// Check if a string exists in any of the pools
    pub fn contains(&self, value: &str) -> bool {
        self.strings.iter().any(|s| s.contains(value))
            || self.types.iter().any(|s| s.contains(value))
            || self.fields.iter().any(|s| s.contains(value))
            || self.methods.iter().any(|s| s.contains(value))
    }

    /// Check if a string exists in the string pool
    pub fn contains_string(&self, value: &str) -> bool {
        self.strings.iter().any(|s| s.contains(value))
    }

    /// Check if a type exists in the type pool
    pub fn contains_type(&self, value: &str) -> bool {
        self.types.iter().any(|s| s.contains(value))
    }

    /// Check if a field exists in the field pool
    pub fn contains_field(&self, value: &str) -> bool {
        self.fields.iter().any(|s| s.contains(value))
    }

    /// Check if a method exists in the method pool
    pub fn contains_method(&self, value: &str) -> bool {
        self.methods.iter().any(|s| s.contains(value))
    }

    /// Convert to Python dictionary
    pub fn to_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = pyo3::types::PyDict::new(py);
        dict.set_item("strings", self.strings.clone())?;
        dict.set_item("types", self.types.clone())?;
        dict.set_item("fields", self.fields.clone())?;
        dict.set_item("methods", self.methods.clone())?;
        Ok(dict.into())
    }

    fn __repr__(&self) -> String {
        format!(
            "RustReferencePool(strings={}, types={}, fields={}, methods={})",
            self.strings.len(),
            self.types.len(),
            self.fields.len(),
            self.methods.len()
        )
    }
}

impl Default for RustReferencePool {
    fn default() -> Self {
        Self::new()
    }
}

/// Represents a field in a DEX class
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RustDexField {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub field_type: String,
    #[pyo3(get)]
    pub declaring_class: String,
    #[pyo3(get)]
    pub access_flags: u32,
}

#[pymethods]
impl RustDexField {
    #[new]
    pub fn new(name: String, field_type: String, declaring_class: String, access_flags: u32) -> Self {
        Self {
            name,
            field_type,
            declaring_class,
            access_flags,
        }
    }

    /// Check if field is public
    pub fn is_public(&self) -> bool {
        self.access_flags & 0x0001 != 0
    }

    /// Check if field is private
    pub fn is_private(&self) -> bool {
        self.access_flags & 0x0002 != 0
    }

    /// Check if field is protected
    pub fn is_protected(&self) -> bool {
        self.access_flags & 0x0004 != 0
    }

    /// Check if field is static
    pub fn is_static(&self) -> bool {
        self.access_flags & 0x0008 != 0
    }

    /// Check if field is final
    pub fn is_final(&self) -> bool {
        self.access_flags & 0x0010 != 0
    }

    /// Convert to Python dictionary
    pub fn to_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = pyo3::types::PyDict::new(py);
        dict.set_item("name", &self.name)?;
        dict.set_item("field_type", &self.field_type)?;
        dict.set_item("declaring_class", &self.declaring_class)?;
        dict.set_item("access_flags", self.access_flags)?;
        dict.set_item("is_public", self.is_public())?;
        dict.set_item("is_private", self.is_private())?;
        dict.set_item("is_protected", self.is_protected())?;
        dict.set_item("is_static", self.is_static())?;
        dict.set_item("is_final", self.is_final())?;
        Ok(dict.into())
    }

    fn __repr__(&self) -> String {
        format!("RustDexField(name='{}', type='{}', class='{}')",
                self.name, self.field_type, self.declaring_class)
    }
}

/// Represents a method in a DEX class
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RustDexMethod {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub parameters: Vec<String>,
    #[pyo3(get)]
    pub return_type: String,
    #[pyo3(get)]
    pub declaring_class: String,
    #[pyo3(get)]
    pub access_flags: u32,
    #[pyo3(get)]
    pub references: RustReferencePool,
}

#[pymethods]
impl RustDexMethod {
    #[new]
    pub fn new(
        name: String,
        parameters: Vec<String>,
        return_type: String,
        declaring_class: String,
        access_flags: u32,
    ) -> Self {
        Self {
            name,
            parameters,
            return_type,
            declaring_class,
            access_flags,
            references: RustReferencePool::new(),
        }
    }

    /// Check if method is public
    pub fn is_public(&self) -> bool {
        self.access_flags & 0x0001 != 0
    }

    /// Check if method is private
    pub fn is_private(&self) -> bool {
        self.access_flags & 0x0002 != 0
    }

    /// Check if method is protected
    pub fn is_protected(&self) -> bool {
        self.access_flags & 0x0004 != 0
    }

    /// Check if method is static
    pub fn is_static(&self) -> bool {
        self.access_flags & 0x0008 != 0
    }

    /// Check if method is final
    pub fn is_final(&self) -> bool {
        self.access_flags & 0x0010 != 0
    }

    /// Check if method is a constructor
    pub fn is_constructor(&self) -> bool {
        self.name == "<init>"
    }

    /// Check if method is a static initializer
    pub fn is_static_initializer(&self) -> bool {
        self.name == "<clinit>"
    }

    /// Get method signature (name + parameters)
    pub fn signature(&self) -> String {
        format!("{}({})", self.name, self.parameters.join(", "))
    }

    /// Convert to Python dictionary
    pub fn to_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = pyo3::types::PyDict::new(py);
        dict.set_item("name", &self.name)?;
        dict.set_item("parameters", &self.parameters)?;
        dict.set_item("return_type", &self.return_type)?;
        dict.set_item("declaring_class", &self.declaring_class)?;
        dict.set_item("access_flags", self.access_flags)?;
        dict.set_item("is_public", self.is_public())?;
        dict.set_item("is_private", self.is_private())?;
        dict.set_item("is_protected", self.is_protected())?;
        dict.set_item("is_static", self.is_static())?;
        dict.set_item("is_final", self.is_final())?;
        dict.set_item("is_constructor", self.is_constructor())?;
        dict.set_item("signature", self.signature())?;
        dict.set_item("references", self.references.to_dict(py)?)?;
        Ok(dict.into())
    }

    fn __repr__(&self) -> String {
        format!("RustDexMethod(name='{}', params=[{}], return='{}')",
                self.name, self.parameters.join(", "), self.return_type)
    }
}

/// Represents a class in a DEX file
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RustDexClass {
    #[pyo3(get)]
    pub class_name: String,
    #[pyo3(get)]
    pub package_name: String,
    #[pyo3(get)]
    pub simple_name: String,
    #[pyo3(get)]
    pub superclass: Option<String>,
    #[pyo3(get)]
    pub interfaces: Vec<String>,
    #[pyo3(get)]
    pub access_flags: u32,
    #[pyo3(get)]
    pub fields: Vec<RustDexField>,
    #[pyo3(get)]
    pub methods: Vec<RustDexMethod>,
    #[pyo3(get)]
    pub references: RustReferencePool,
}

#[pymethods]
impl RustDexClass {
    #[new]
    pub fn new(class_name: String) -> Self {
        let (package_name, simple_name) = Self::split_class_name(&class_name);

        Self {
            class_name,
            package_name,
            simple_name,
            superclass: None,
            interfaces: Vec::new(),
            access_flags: 0,
            fields: Vec::new(),
            methods: Vec::new(),
            references: RustReferencePool::new(),
        }
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

    /// Check if class is an interface
    pub fn is_interface(&self) -> bool {
        self.access_flags & 0x0200 != 0
    }

    /// Check if class is an enum
    pub fn is_enum(&self) -> bool {
        self.access_flags & 0x4000 != 0
    }

    /// Get number of methods
    pub fn method_count(&self) -> usize {
        self.methods.len()
    }

    /// Get number of fields
    pub fn field_count(&self) -> usize {
        self.fields.len()
    }

    /// Convert to Python dictionary
    pub fn to_dict(&self, py: Python) -> PyResult<PyObject> {
        let dict = pyo3::types::PyDict::new(py);
        dict.set_item("class_name", &self.class_name)?;
        dict.set_item("package_name", &self.package_name)?;
        dict.set_item("simple_name", &self.simple_name)?;
        dict.set_item("superclass", &self.superclass)?;
        dict.set_item("interfaces", &self.interfaces)?;
        dict.set_item("access_flags", self.access_flags)?;
        dict.set_item("is_public", self.is_public())?;
        dict.set_item("is_final", self.is_final())?;
        dict.set_item("is_abstract", self.is_abstract())?;
        dict.set_item("is_interface", self.is_interface())?;
        dict.set_item("is_enum", self.is_enum())?;
        dict.set_item("method_count", self.method_count())?;
        dict.set_item("field_count", self.field_count())?;

        let fields_list = pyo3::types::PyList::empty(py);
        for field in &self.fields {
            fields_list.append(field.to_dict(py)?)?;
        }
        dict.set_item("fields", fields_list)?;

        let methods_list = pyo3::types::PyList::empty(py);
        for method in &self.methods {
            methods_list.append(method.to_dict(py)?)?;
        }
        dict.set_item("methods", methods_list)?;

        dict.set_item("references", self.references.to_dict(py)?)?;
        Ok(dict.into())
    }

    fn __repr__(&self) -> String {
        format!(
            "RustDexClass(name='{}', methods={}, fields={})",
            self.class_name,
            self.methods.len(),
            self.fields.len()
        )
    }
}

impl RustDexClass {
    /// Split a full class name into package and simple name
    /// e.g., "com.example.app.MainActivity" -> ("com.example.app", "MainActivity")
    fn split_class_name(class_name: &str) -> (String, String) {
        // Handle class names like "Lcom/example/App;" (DEX format)
        let clean_name = class_name
            .trim_start_matches('L')
            .trim_end_matches(';')
            .replace('/', ".");

        if let Some(pos) = clean_name.rfind('.') {
            let package = clean_name[..pos].to_string();
            let simple = clean_name[pos + 1..].to_string();
            (package, simple)
        } else {
            (String::new(), clean_name)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_split_class_name() {
        let (pkg, simple) = RustDexClass::split_class_name("com.example.app.MainActivity");
        assert_eq!(pkg, "com.example.app");
        assert_eq!(simple, "MainActivity");

        let (pkg, simple) = RustDexClass::split_class_name("Lcom/example/App;");
        assert_eq!(pkg, "com.example");
        assert_eq!(simple, "App");

        let (pkg, simple) = RustDexClass::split_class_name("SimpleClass");
        assert_eq!(pkg, "");
        assert_eq!(simple, "SimpleClass");
    }

    #[test]
    fn test_access_flags() {
        let field = RustDexField::new(
            "test".to_string(),
            "int".to_string(),
            "TestClass".to_string(),
            0x0001 | 0x0008 | 0x0010, // public static final
        );
        assert!(field.is_public());
        assert!(field.is_static());
        assert!(field.is_final());
        assert!(!field.is_private());
    }
}
