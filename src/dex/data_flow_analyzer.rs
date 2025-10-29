//! Data Flow Analyzer - Generic flow analysis from entry points to sink methods
//!
//! This module integrates entry point analysis and call graph to find complete paths
//! from Android components to various sink methods (WebView, File I/O, Network, etc.),
//! including data flow tracking.

use pyo3::prelude::*;
use std::collections::{HashMap, HashSet};

use crate::dex::entry_point_analyzer::{EntryPoint, EntryPointAnalyzer, ComponentType};
use crate::dex::call_graph::{CallGraph, CallPath};
use crate::dex::class_decompiler::DecompiledClass;

/// Represents a complete data flow from an entry point to a sink method
#[pyclass]
#[derive(Clone, Debug)]
pub struct Flow {
    /// Entry point that leads to the sink
    #[pyo3(get)]
    pub entry_point: String,

    /// Component type (Activity, Service, etc.)
    #[pyo3(get)]
    pub component_type: String,

    /// Sink method being called (e.g., WebView.loadUrl, File.write)
    #[pyo3(get)]
    pub sink_method: String,

    /// Call paths from entry to sink
    #[pyo3(get)]
    pub paths: Vec<CallPath>,

    /// Whether this is a deeplink handler
    #[pyo3(get)]
    pub is_deeplink_handler: bool,

    /// Shortest path length
    #[pyo3(get)]
    pub min_path_length: usize,

    /// Number of different paths
    #[pyo3(get)]
    pub path_count: usize,
}

#[pymethods]
impl Flow {
    fn __repr__(&self) -> String {
        format!(
            "Flow({} → {} via {} path(s), depth={})",
            self.entry_point, self.sink_method, self.path_count, self.min_path_length
        )
    }

    /// Get the shortest path
    #[pyo3(name = "get_shortest_path")]
    pub fn get_shortest_path(&self) -> Option<CallPath> {
        self.paths.iter().min_by_key(|p| p.length).cloned()
    }

    /// Get all lifecycle methods involved
    #[pyo3(name = "get_lifecycle_methods")]
    pub fn get_lifecycle_methods(&self) -> Vec<String> {
        let lifecycle = vec![
            "onCreate", "onStart", "onResume", "onPause", "onStop", "onDestroy",
            "onNewIntent", "onActivityResult", "onRequestPermissionsResult",
        ];

        let mut found = HashSet::new();
        for path in &self.paths {
            for method in &path.methods {
                for lc in &lifecycle {
                    if method.contains(lc) {
                        found.insert(method.clone());
                    }
                }
            }
        }

        found.into_iter().collect()
    }
}

/// Data flow information from source to sink
#[pyclass]
#[derive(Clone, Debug)]
pub struct DataFlow {
    /// Source of data (e.g., "Intent.getStringExtra")
    #[pyo3(get)]
    pub source: String,

    /// Sink where data is used (e.g., "WebView.loadUrl", "File.write")
    #[pyo3(get)]
    pub sink: String,

    /// Methods involved in the data flow
    #[pyo3(get)]
    pub flow_path: Vec<String>,

    /// Estimated confidence (0.0 - 1.0)
    #[pyo3(get)]
    pub confidence: f32,
}

#[pymethods]
impl DataFlow {
    fn __repr__(&self) -> String {
        format!(
            "DataFlow({} → {} via {} hops, confidence={:.2})",
            self.source,
            self.sink,
            self.flow_path.len(),
            self.confidence
        )
    }
}

/// Generic Data Flow Analyzer - finds flows from entry points to any sink
#[pyclass]
pub struct DataFlowAnalyzer {
    entry_analyzer: EntryPointAnalyzer,
    call_graph: CallGraph,
}

impl DataFlowAnalyzer {
    /// Create a new data flow analyzer
    pub fn new(entry_analyzer: EntryPointAnalyzer, call_graph: CallGraph) -> Self {
        Self {
            entry_analyzer,
            call_graph,
        }
    }

    /// Find all sink methods matching the given patterns
    fn find_sink_methods(&self, patterns: &[&str]) -> Vec<String> {
        let mut sink_methods = Vec::new();

        for pattern in patterns {
            let methods = self.call_graph.find_methods_matching(pattern);
            sink_methods.extend(methods);
        }

        sink_methods
    }

    /// Generic method to find flows from entry points to sinks matching patterns
    pub fn find_flows_to(&self, sink_patterns: &[&str], max_depth: usize) -> Vec<Flow> {
        let mut flows = Vec::new();

        let entry_points = self.entry_analyzer.analyze();
        let sink_methods = self.find_sink_methods(sink_patterns);

        if sink_methods.is_empty() {
            return flows;
        }

        // For each entry point
        for entry_point in &entry_points {
            // Try lifecycle methods as starting points
            let lifecycle_methods = vec![
                "onCreate",
                "onStart",
                "onResume",
                "onNewIntent",
            ];

            for lifecycle in &lifecycle_methods {
                let source_method = format!("{}.{}", entry_point.class_name, lifecycle);

                // Find paths to each sink method
                for sink_method in &sink_methods {
                    let paths = self.call_graph.find_paths(&source_method, sink_method, max_depth);

                    if !paths.is_empty() {
                        let min_length = paths.iter().map(|p| p.length).min().unwrap_or(0);

                        flows.push(Flow {
                            entry_point: entry_point.class_name.clone(),
                            component_type: format!("{:?}", entry_point.component_type),
                            sink_method: sink_method.clone(),
                            paths: paths.clone(),
                            is_deeplink_handler: entry_point.is_deeplink_handler,
                            min_path_length: min_length,
                            path_count: paths.len(),
                        });
                    }
                }
            }
        }

        flows
    }

    /// Convenience method: Find flows to WebView methods
    pub fn find_webview_flows(&self, max_depth: usize) -> Vec<Flow> {
        let webview_patterns = vec![
            "loadUrl",
            "loadData",
            "loadDataWithBaseURL",
            "evaluateJavascript",
            "addJavascriptInterface",
            "setWebViewClient",
            "setWebChromeClient",
        ];

        self.find_flows_to(&webview_patterns, max_depth)
    }

    /// Convenience method: Find flows to file I/O methods
    pub fn find_file_flows(&self, max_depth: usize) -> Vec<Flow> {
        let file_patterns = vec![
            "FileOutputStream",
            "FileWriter",
            "RandomAccessFile.write",
            "Files.write",
        ];

        self.find_flows_to(&file_patterns, max_depth)
    }

    /// Convenience method: Find flows to network methods
    pub fn find_network_flows(&self, max_depth: usize) -> Vec<Flow> {
        let network_patterns = vec![
            "HttpURLConnection",
            "OkHttp",
            "URLConnection.connect",
            "Socket.connect",
        ];

        self.find_flows_to(&network_patterns, max_depth)
    }

    /// Convenience method: Find flows to SQL methods
    pub fn find_sql_flows(&self, max_depth: usize) -> Vec<Flow> {
        let sql_patterns = vec![
            "execSQL",
            "rawQuery",
            "SQLiteDatabase.query",
        ];

        self.find_flows_to(&sql_patterns, max_depth)
    }

    /// Find deeplink handlers that lead to specific sinks
    pub fn find_deeplink_flows(&self, sink_patterns: &[&str], max_depth: usize) -> Vec<Flow> {
        self.find_flows_to(sink_patterns, max_depth)
            .into_iter()
            .filter(|flow| flow.is_deeplink_handler)
            .collect()
    }

    /// Analyze data flow from Intent to sink (simplified heuristic-based approach)
    pub fn analyze_data_flows(&self, flows: &[Flow]) -> Vec<DataFlow> {
        let mut data_flows = Vec::new();

        // Intent data extraction methods to track
        let intent_methods = vec![
            "getStringExtra",
            "getIntExtra",
            "getBooleanExtra",
            "getData",
            "getDataString",
            "getExtras",
        ];

        for flow in flows {
            for path in &flow.paths {
                // Check if path contains intent data extraction
                let has_intent_data = path.methods.iter().any(|m| {
                    intent_methods.iter().any(|intent_method| m.contains(intent_method))
                });

                if has_intent_data {
                    // Find which intent method is used
                    if let Some(source_method) = path.methods.iter().find(|m| {
                        intent_methods.iter().any(|intent_method| m.contains(intent_method))
                    }) {
                        // Calculate confidence based on path length and directness
                        let confidence = if path.length <= 3 {
                            0.9
                        } else if path.length <= 5 {
                            0.7
                        } else if path.length <= 8 {
                            0.5
                        } else {
                            0.3
                        };

                        data_flows.push(DataFlow {
                            source: source_method.clone(),
                            sink: flow.sink_method.clone(),
                            flow_path: path.methods.clone(),
                            confidence,
                        });
                    }
                }
            }
        }

        data_flows
    }

    /// Get statistics about flow analysis
    pub fn get_stats(&self) -> HashMap<String, usize> {
        let mut stats = HashMap::new();

        let entry_points = self.entry_analyzer.analyze();
        stats.insert("entry_points".to_string(), entry_points.len());

        let deeplink_handlers = entry_points
            .iter()
            .filter(|ep| ep.is_deeplink_handler)
            .count();
        stats.insert("deeplink_handlers".to_string(), deeplink_handlers);

        stats
    }
}

#[pymethods]
impl DataFlowAnalyzer {
    /// Find flows to methods matching patterns
    #[pyo3(name = "find_flows_to")]
    pub fn find_flows_to_py(&self, patterns: Vec<String>, max_depth: Option<usize>) -> Vec<Flow> {
        let pattern_refs: Vec<&str> = patterns.iter().map(|s| s.as_str()).collect();
        self.find_flows_to(&pattern_refs, max_depth.unwrap_or(10))
    }

    /// Find flows to WebView methods
    #[pyo3(name = "find_webview_flows")]
    pub fn find_webview_flows_py(&self, max_depth: Option<usize>) -> Vec<Flow> {
        self.find_webview_flows(max_depth.unwrap_or(10))
    }

    /// Find flows to file I/O methods
    #[pyo3(name = "find_file_flows")]
    pub fn find_file_flows_py(&self, max_depth: Option<usize>) -> Vec<Flow> {
        self.find_file_flows(max_depth.unwrap_or(10))
    }

    /// Find flows to network methods
    #[pyo3(name = "find_network_flows")]
    pub fn find_network_flows_py(&self, max_depth: Option<usize>) -> Vec<Flow> {
        self.find_network_flows(max_depth.unwrap_or(10))
    }

    /// Find flows to SQL methods
    #[pyo3(name = "find_sql_flows")]
    pub fn find_sql_flows_py(&self, max_depth: Option<usize>) -> Vec<Flow> {
        self.find_sql_flows(max_depth.unwrap_or(10))
    }

    /// Find deeplink flows to specific patterns
    #[pyo3(name = "find_deeplink_flows")]
    pub fn find_deeplink_flows_py(&self, patterns: Vec<String>, max_depth: Option<usize>) -> Vec<Flow> {
        let pattern_refs: Vec<&str> = patterns.iter().map(|s| s.as_str()).collect();
        self.find_deeplink_flows(&pattern_refs, max_depth.unwrap_or(10))
    }

    /// Analyze data flows for given flows
    #[pyo3(name = "analyze_data_flows")]
    pub fn analyze_data_flows_py(&self, flows: Vec<Flow>) -> Vec<DataFlow> {
        self.analyze_data_flows(&flows)
    }

    /// Get flow analysis statistics
    #[pyo3(name = "get_stats")]
    pub fn get_stats_py(&self) -> HashMap<String, usize> {
        self.get_stats()
    }

    fn __repr__(&self) -> String {
        let stats = self.get_stats();
        format!(
            "DataFlowAnalyzer(entry_points={}, deeplink_handlers={})",
            stats.get("entry_points").unwrap_or(&0),
            stats.get("deeplink_handlers").unwrap_or(&0)
        )
    }
}

// ============================================================================
// Backward Compatibility Aliases
// ============================================================================

/// Backward compatibility: WebViewFlow is now an alias for Flow
pub type WebViewFlow = Flow;

/// Backward compatibility: WebViewFlowAnalyzer is now an alias for DataFlowAnalyzer
pub type WebViewFlowAnalyzer = DataFlowAnalyzer;

// ============================================================================
// Python Functions
// ============================================================================

/// Create a data flow analyzer from APK
#[pyfunction]
pub fn create_data_flow_analyzer(apk_path: String) -> PyResult<DataFlowAnalyzer> {
    use crate::dex::entry_point_analyzer::analyze_entry_points_from_apk;
    use crate::dex::call_graph::build_call_graph_from_apk_parallel;

    // Build entry point analyzer
    let entry_analyzer = analyze_entry_points_from_apk(apk_path.clone())?;

    // Build call graph (using optimized parallel version)
    let call_graph = build_call_graph_from_apk_parallel(apk_path, None)?;

    // Create analyzer
    Ok(DataFlowAnalyzer::new(
        entry_analyzer.analyzer.clone(),
        call_graph,
    ))
}

/// Find flows from entry points to sink patterns
#[pyfunction]
pub fn find_flows_from_apk(
    apk_path: String,
    sink_patterns: Vec<String>,
    max_depth: Option<usize>,
) -> PyResult<Vec<Flow>> {
    let analyzer = create_data_flow_analyzer(apk_path)?;
    let pattern_refs: Vec<&str> = sink_patterns.iter().map(|s| s.as_str()).collect();
    Ok(analyzer.find_flows_to(&pattern_refs, max_depth.unwrap_or(10)))
}

/// Convenience: Find WebView flows from APK
#[pyfunction]
pub fn find_webview_flows_from_apk(
    apk_path: String,
    max_depth: Option<usize>,
) -> PyResult<Vec<Flow>> {
    let analyzer = create_data_flow_analyzer(apk_path)?;
    Ok(analyzer.find_webview_flows(max_depth.unwrap_or(10)))
}

/// Convenience: Find file I/O flows from APK
#[pyfunction]
pub fn find_file_flows_from_apk(
    apk_path: String,
    max_depth: Option<usize>,
) -> PyResult<Vec<Flow>> {
    let analyzer = create_data_flow_analyzer(apk_path)?;
    Ok(analyzer.find_file_flows(max_depth.unwrap_or(10)))
}

/// Convenience: Find network flows from APK
#[pyfunction]
pub fn find_network_flows_from_apk(
    apk_path: String,
    max_depth: Option<usize>,
) -> PyResult<Vec<Flow>> {
    let analyzer = create_data_flow_analyzer(apk_path)?;
    Ok(analyzer.find_network_flows(max_depth.unwrap_or(10)))
}

// ============================================================================
// Backward Compatibility Functions
// ============================================================================

/// Backward compatibility: analyze_webview_flows_from_apk
#[pyfunction]
pub fn analyze_webview_flows_from_apk(
    apk_path: String,
    max_depth: Option<usize>,
) -> PyResult<Vec<Flow>> {
    find_webview_flows_from_apk(apk_path, max_depth)
}

/// Backward compatibility: create_webview_analyzer_from_apk
#[pyfunction]
pub fn create_webview_analyzer_from_apk(apk_path: String) -> PyResult<DataFlowAnalyzer> {
    create_data_flow_analyzer(apk_path)
}
