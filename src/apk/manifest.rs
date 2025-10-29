use crate::apk::error::{ApkError, Result};
use pyo3::prelude::*;
use std::io::Cursor;
use serde::{Deserialize, Serialize};

/// Intent filter data (for deeplink analysis)
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntentFilterData {
    #[pyo3(get)]
    pub scheme: Option<String>,
    #[pyo3(get)]
    pub host: Option<String>,
    #[pyo3(get)]
    pub path: Option<String>,
    #[pyo3(get)]
    pub path_prefix: Option<String>,
    #[pyo3(get)]
    pub path_pattern: Option<String>,
}

#[pymethods]
impl IntentFilterData {
    fn __repr__(&self) -> String {
        let mut parts = Vec::new();
        if let Some(scheme) = &self.scheme {
            parts.push(format!("scheme='{}'", scheme));
        }
        if let Some(host) = &self.host {
            parts.push(format!("host='{}'", host));
        }
        if let Some(path) = &self.path {
            parts.push(format!("path='{}'", path));
        }
        format!("IntentFilterData({})", parts.join(", "))
    }
}

/// Activity with intent filters
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActivityIntentFilter {
    #[pyo3(get)]
    pub activity: String,
    #[pyo3(get)]
    pub actions: Vec<String>,
    #[pyo3(get)]
    pub categories: Vec<String>,
    #[pyo3(get)]
    pub data: Vec<IntentFilterData>,
}

#[pymethods]
impl ActivityIntentFilter {
    fn __repr__(&self) -> String {
        format!(
            "ActivityIntentFilter(activity='{}', actions={}, data={})",
            self.activity,
            self.actions.len(),
            self.data.len()
        )
    }

    pub fn is_deeplink(&self) -> bool {
        // Check if this is a deeplink intent filter
        // Must have VIEW action and BROWSABLE or DEFAULT category
        let has_view_action = self.actions.iter().any(|a| a.contains("VIEW"));
        let has_browsable = self.categories.iter().any(|c| c.contains("BROWSABLE") || c.contains("DEFAULT"));

        has_view_action && has_browsable && !self.data.is_empty()
    }
}

/// Parsed AndroidManifest.xml information
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RustManifestInfo {
    #[pyo3(get)]
    pub package_name: String,
    #[pyo3(get)]
    pub version_code: Option<String>,
    #[pyo3(get)]
    pub version_name: Option<String>,
    #[pyo3(get)]
    pub min_sdk_version: Option<String>,
    #[pyo3(get)]
    pub target_sdk_version: Option<String>,
    #[pyo3(get)]
    pub permissions: Vec<String>,
    #[pyo3(get)]
    pub activities: Vec<String>,
    #[pyo3(get)]
    pub services: Vec<String>,
    #[pyo3(get)]
    pub receivers: Vec<String>,
    #[pyo3(get)]
    pub providers: Vec<String>,
    #[pyo3(get)]
    pub application_label: Option<String>,
    #[pyo3(get)]
    pub intent_filters: Vec<ActivityIntentFilter>,
}

#[pymethods]
impl RustManifestInfo {
    #[new]
    pub fn new(package_name: String) -> Self {
        Self {
            package_name,
            version_code: None,
            version_name: None,
            min_sdk_version: None,
            target_sdk_version: None,
            permissions: Vec::new(),
            activities: Vec::new(),
            services: Vec::new(),
            receivers: Vec::new(),
            providers: Vec::new(),
            application_label: None,
            intent_filters: Vec::new(),
        }
    }

    /// Get only deeplink intent filters
    pub fn get_deeplinks(&self) -> Vec<ActivityIntentFilter> {
        self.intent_filters
            .iter()
            .filter(|f| f.is_deeplink())
            .cloned()
            .collect()
    }

    /// Convert to Python dictionary
    pub fn to_dict(&self, py: Python) -> PyResult<Py<pyo3::types::PyAny>> {
        let dict = pyo3::types::PyDict::new(py);
        dict.set_item("package_name", &self.package_name)?;
        dict.set_item("version_code", &self.version_code)?;
        dict.set_item("version_name", &self.version_name)?;
        dict.set_item("min_sdk_version", &self.min_sdk_version)?;
        dict.set_item("target_sdk_version", &self.target_sdk_version)?;
        dict.set_item("permissions", &self.permissions)?;
        dict.set_item("activities", &self.activities)?;
        dict.set_item("services", &self.services)?;
        dict.set_item("receivers", &self.receivers)?;
        dict.set_item("providers", &self.providers)?;
        dict.set_item("application_label", &self.application_label)?;
        Ok(dict.into())
    }

    fn __repr__(&self) -> String {
        format!(
            "RustManifestInfo(package='{}', version='{}', activities={}, services={}, receivers={}, providers={})",
            self.package_name,
            self.version_name.as_deref().unwrap_or("unknown"),
            self.activities.len(),
            self.services.len(),
            self.receivers.len(),
            self.providers.len()
        )
    }
}

/// Parse AndroidManifest.xml from binary data
pub fn parse_manifest(data: &[u8]) -> Result<RustManifestInfo> {
    // Parse binary XML using rusty-axml
    let cursor = Cursor::new(data.to_vec());
    let axml = rusty_axml::parse_from_cursor(cursor)
        .map_err(|e| ApkError::InvalidApk(format!("Failed to parse manifest: {:?}", e)))?;

    // Get package name from root node
    let root = axml.root();
    let package_name = root
        .borrow()
        .get_attr("package")
        .ok_or_else(|| ApkError::InvalidApk("No package name found".to_string()))?
        .to_string();

    let mut manifest = RustManifestInfo::new(package_name.clone());

    // Get version info from root attributes (try with and without android: prefix)
    let root_borrowed = root.borrow();
    manifest.version_code = root_borrowed.get_attr("android:versionCode")
        .or_else(|| root_borrowed.get_attr("versionCode"))
        .map(|s| s.to_string());
    manifest.version_name = root_borrowed.get_attr("android:versionName")
        .or_else(|| root_borrowed.get_attr("versionName"))
        .map(|s| s.to_string());

    // Get SDK versions (try with and without android: prefix)
    let uses_sdk_nodes = rusty_axml::find_nodes_by_type(&axml, "uses-sdk");
    if let Some(uses_sdk) = uses_sdk_nodes.first() {
        let uses_sdk_borrowed = uses_sdk.borrow();
        manifest.min_sdk_version = uses_sdk_borrowed.get_attr("android:minSdkVersion")
            .or_else(|| uses_sdk_borrowed.get_attr("minSdkVersion"))
            .map(|s| s.to_string());
        manifest.target_sdk_version = uses_sdk_borrowed.get_attr("android:targetSdkVersion")
            .or_else(|| uses_sdk_borrowed.get_attr("targetSdkVersion"))
            .map(|s| s.to_string());
    }

    // Get permissions using helper function
    manifest.permissions = rusty_axml::get_requested_permissions(&axml);

    // Get activities
    let activities = rusty_axml::get_activities_names(&axml);
    manifest.activities = activities
        .into_iter()
        .map(|name| normalize_component_name(&package_name, &name))
        .collect();

    // Get services
    let services = rusty_axml::get_services_names(&axml);
    manifest.services = services
        .into_iter()
        .map(|name| normalize_component_name(&package_name, &name))
        .collect();

    // Get receivers
    let receivers = rusty_axml::get_receivers_names(&axml);
    manifest.receivers = receivers
        .into_iter()
        .map(|name| normalize_component_name(&package_name, &name))
        .collect();

    // Get providers
    let providers = rusty_axml::get_providers_names(&axml);
    manifest.providers = providers
        .into_iter()
        .map(|name| normalize_component_name(&package_name, &name))
        .collect();

    // Get application label
    let app_nodes = rusty_axml::find_nodes_by_type(&axml, "application");
    if let Some(app_node) = app_nodes.first() {
        manifest.application_label = app_node.borrow().get_attr("android:label").map(|s| s.to_string());
    }

    // Parse intent filters for deeplinks
    manifest.intent_filters = parse_intent_filters(&axml, &package_name);

    Ok(manifest)
}

/// Parse intent filters from activities
fn parse_intent_filters(axml: &rusty_axml::parser::Axml, package_name: &str) -> Vec<ActivityIntentFilter> {
    let mut intent_filters = Vec::new();

    // Get all activity nodes
    let activity_nodes = rusty_axml::find_nodes_by_type(axml, "activity");

    for activity_node in activity_nodes {
        let activity_borrowed = activity_node.borrow();

        // Get activity name
        let activity_name = if let Some(name) = activity_borrowed.get_attr("android:name") {
            normalize_component_name(package_name, name)
        } else {
            continue;
        };

        // Look for intent-filter children
        for child in activity_borrowed.children() {
            let child_borrowed = child.borrow();
            if child_borrowed.element_type() == "intent-filter" {
                let mut actions = Vec::new();
                let mut categories = Vec::new();
                let mut data_list = Vec::new();

                // Parse intent-filter children
                for intent_child in child_borrowed.children() {
                    let intent_child_borrowed = intent_child.borrow();
                    match intent_child_borrowed.element_type() {
                        "action" => {
                            if let Some(name) = intent_child_borrowed.get_attr("android:name") {
                                actions.push(name.to_string());
                            }
                        }
                        "category" => {
                            if let Some(name) = intent_child_borrowed.get_attr("android:name") {
                                categories.push(name.to_string());
                            }
                        }
                        "data" => {
                            let data = IntentFilterData {
                                scheme: intent_child_borrowed.get_attr("android:scheme").map(|s| s.to_string()),
                                host: intent_child_borrowed.get_attr("android:host").map(|s| s.to_string()),
                                path: intent_child_borrowed.get_attr("android:path").map(|s| s.to_string()),
                                path_prefix: intent_child_borrowed.get_attr("android:pathPrefix").map(|s| s.to_string()),
                                path_pattern: intent_child_borrowed.get_attr("android:pathPattern").map(|s| s.to_string()),
                            };
                            data_list.push(data);
                        }
                        _ => {}
                    }
                }

                // Only add if we have actual data
                if !actions.is_empty() || !data_list.is_empty() {
                    intent_filters.push(ActivityIntentFilter {
                        activity: activity_name.clone(),
                        actions,
                        categories,
                        data: data_list,
                    });
                }
            }
        }
    }

    intent_filters
}

/// Normalize component name (handle relative names like ".MainActivity")
fn normalize_component_name(package_name: &str, component_name: &str) -> String {
    if component_name.starts_with('.') {
        // Relative name: .MainActivity -> com.example.MainActivity
        format!("{}{}", package_name, component_name)
    } else if component_name.contains('.') {
        // Full name: com.example.MainActivity
        component_name.to_string()
    } else {
        // Simple name: MainActivity -> com.example.MainActivity
        format!("{}.{}", package_name, component_name)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_normalize_component_name() {
        let package = "com.example.app";

        assert_eq!(
            normalize_component_name(package, ".MainActivity"),
            "com.example.app.MainActivity"
        );

        assert_eq!(
            normalize_component_name(package, "com.example.app.MainActivity"),
            "com.example.app.MainActivity"
        );

        assert_eq!(
            normalize_component_name(package, "MainActivity"),
            "com.example.app.MainActivity"
        );
    }
}
