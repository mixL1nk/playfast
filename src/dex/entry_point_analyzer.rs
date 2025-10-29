//! Entry Point Analyzer
//!
//! Links Android manifest components (Activities, Services, etc.) with
//! their corresponding DEX classes, enabling analysis of app entry points
//! and deeplink handlers.

use crate::apk::manifest::{ActivityIntentFilter, RustManifestInfo};
use crate::dex::class_decompiler::DecompiledClass;
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Type of Android component
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[pyclass]
pub enum ComponentType {
    Activity,
    Service,
    BroadcastReceiver,
    ContentProvider,
}

#[pymethods]
impl ComponentType {
    fn __repr__(&self) -> String {
        format!("{:?}", self)
    }
}

/// Entry point in the application
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntryPoint {
    /// Component type (Activity, Service, etc.)
    #[pyo3(get)]
    pub component_type: ComponentType,

    /// Fully qualified class name
    #[pyo3(get)]
    pub class_name: String,

    /// Intent filters for this component
    #[pyo3(get)]
    pub intent_filters: Vec<ActivityIntentFilter>,

    /// Whether this entry point handles deeplinks
    #[pyo3(get)]
    pub is_deeplink_handler: bool,

    /// Whether the corresponding class was found in DEX
    #[pyo3(get)]
    pub class_found: bool,
}

#[pymethods]
impl EntryPoint {
    /// Get all deeplink patterns this entry point handles
    pub fn get_deeplink_patterns(&self) -> Vec<String> {
        let mut patterns = Vec::new();

        for filter in &self.intent_filters {
            for data in &filter.data {
                let mut pattern = String::new();

                if let Some(scheme) = &data.scheme {
                    pattern.push_str(scheme);
                    pattern.push_str("://");
                }

                if let Some(host) = &data.host {
                    pattern.push_str(host);
                }

                if let Some(path) = &data.path {
                    pattern.push_str(path);
                } else if let Some(prefix) = &data.path_prefix {
                    pattern.push_str(prefix);
                    pattern.push('*');
                } else if let Some(path_pattern) = &data.path_pattern {
                    pattern.push_str(path_pattern);
                }

                if !pattern.is_empty() {
                    patterns.push(pattern);
                }
            }
        }

        patterns
    }

    /// Get all intent actions this entry point handles
    pub fn get_actions(&self) -> Vec<String> {
        self.intent_filters
            .iter()
            .flat_map(|f| f.actions.clone())
            .collect()
    }

    /// Check if this handles a specific action
    pub fn handles_action(&self, action: &str) -> bool {
        self.intent_filters
            .iter()
            .any(|f| f.actions.iter().any(|a| a == action))
    }

    fn __repr__(&self) -> String {
        format!(
            "EntryPoint({:?}, {}, deeplink={}, found={})",
            self.component_type,
            self.class_name,
            self.is_deeplink_handler,
            self.class_found
        )
    }
}

/// Entry point analyzer
#[derive(Clone)]
pub struct EntryPointAnalyzer {
    manifest: RustManifestInfo,
    classes: HashMap<String, DecompiledClass>,
}

impl EntryPointAnalyzer {
    /// Create a new analyzer
    pub fn new(manifest: RustManifestInfo, classes: Vec<DecompiledClass>) -> Self {
        let class_map = classes
            .into_iter()
            .map(|c| (c.class_name.clone(), c))
            .collect();

        Self {
            manifest,
            classes: class_map,
        }
    }

    /// Analyze all entry points
    pub fn analyze(&self) -> Vec<EntryPoint> {
        let mut entry_points = Vec::new();

        // Analyze Activities
        for activity in &self.manifest.activities {
            entry_points.push(self.analyze_component(
                activity,
                ComponentType::Activity,
            ));
        }

        // Analyze Services
        for service in &self.manifest.services {
            entry_points.push(EntryPoint {
                component_type: ComponentType::Service,
                class_name: service.clone(),
                intent_filters: Vec::new(), // Services typically don't have intent filters in manifest
                is_deeplink_handler: false,
                class_found: self.classes.contains_key(service),
            });
        }

        // Analyze BroadcastReceivers
        for receiver in &self.manifest.receivers {
            entry_points.push(EntryPoint {
                component_type: ComponentType::BroadcastReceiver,
                class_name: receiver.clone(),
                intent_filters: Vec::new(),
                is_deeplink_handler: false,
                class_found: self.classes.contains_key(receiver),
            });
        }

        entry_points
    }

    /// Analyze a specific component
    fn analyze_component(&self, class_name: &str, component_type: ComponentType) -> EntryPoint {
        // Find intent filters for this component
        let intent_filters: Vec<ActivityIntentFilter> = self
            .manifest
            .intent_filters
            .iter()
            .filter(|f| f.activity == class_name)
            .cloned()
            .collect();

        // Check if it handles deeplinks
        let is_deeplink_handler = intent_filters.iter().any(|f| f.is_deeplink());

        // Check if class exists in DEX
        let class_found = self.classes.contains_key(class_name);

        EntryPoint {
            component_type,
            class_name: class_name.to_string(),
            intent_filters,
            is_deeplink_handler,
            class_found,
        }
    }

    /// Get all deeplink handlers
    pub fn get_deeplink_handlers(&self) -> Vec<EntryPoint> {
        self.analyze()
            .into_iter()
            .filter(|ep| ep.is_deeplink_handler)
            .collect()
    }

    /// Get entry point with its class
    pub fn get_entry_point_with_class(&self, class_name: &str) -> Option<(EntryPoint, DecompiledClass)> {
        let entry_point = self.analyze()
            .into_iter()
            .find(|ep| ep.class_name == class_name)?;

        let class = self.classes.get(class_name)?.clone();

        Some((entry_point, class))
    }

    /// Get all entry points that have corresponding classes
    pub fn get_analyzed_entry_points(&self) -> Vec<(EntryPoint, DecompiledClass)> {
        self.analyze()
            .into_iter()
            .filter_map(|ep| {
                self.classes
                    .get(&ep.class_name)
                    .map(|c| (ep, c.clone()))
            })
            .collect()
    }
}

/// Python wrapper
#[pyclass]
pub struct PyEntryPointAnalyzer {
    pub analyzer: EntryPointAnalyzer,
}

#[pymethods]
impl PyEntryPointAnalyzer {
    /// Get all entry points
    pub fn analyze(&self) -> Vec<EntryPoint> {
        self.analyzer.analyze()
    }

    /// Get only deeplink handlers
    pub fn get_deeplink_handlers(&self) -> Vec<EntryPoint> {
        self.analyzer.get_deeplink_handlers()
    }

    /// Get entry points that have classes found in DEX
    pub fn get_found_entry_points(&self) -> Vec<EntryPoint> {
        self.analyzer
            .analyze()
            .into_iter()
            .filter(|ep| ep.class_found)
            .collect()
    }

    /// Get statistics
    pub fn get_stats(&self) -> String {
        let all = self.analyzer.analyze();
        let found = all.iter().filter(|ep| ep.class_found).count();
        let deeplinks = all.iter().filter(|ep| ep.is_deeplink_handler).count();

        format!(
            "Total: {}, Found in DEX: {}, Deeplink handlers: {}",
            all.len(),
            found,
            deeplinks
        )
    }

    fn __repr__(&self) -> String {
        self.get_stats()
    }
}

/// Analyze entry points from APK
#[pyfunction]
pub fn analyze_entry_points_from_apk(apk_path: String) -> PyResult<PyEntryPointAnalyzer> {
    use crate::apk::{ApkExtractor, parse_manifest};
    use crate::dex::class_decompiler::decompile_class_from_apk;

    // Extract and parse manifest
    let extractor = ApkExtractor::new(&apk_path)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

    let manifest_data = extractor
        .extract_manifest()
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

    let manifest = parse_manifest(&manifest_data)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

    // Decompile all component classes
    let mut classes = Vec::new();

    // Collect all component names
    let component_names: Vec<String> = manifest
        .activities
        .iter()
        .chain(manifest.services.iter())
        .chain(manifest.receivers.iter())
        .cloned()
        .collect();

    // Try to decompile each component
    for class_name in component_names {
        if let Ok(class) = decompile_class_from_apk(apk_path.clone(), class_name) {
            classes.push(class);
        }
    }

    let analyzer = EntryPointAnalyzer::new(manifest, classes);

    Ok(PyEntryPointAnalyzer { analyzer })
}
