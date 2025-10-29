//! Call Graph Builder for Android DEX analysis
//!
//! This module builds a call graph showing method-to-method relationships,
//! enabling analysis of call paths from entry points to specific APIs (e.g., WebView.loadUrl).

use pyo3::prelude::*;
use std::collections::{HashMap, HashSet, VecDeque};

use crate::dex::class_decompiler::{DecompiledClass, DecompiledMethod};
use crate::dex::expression_builder::ReconstructedExpression;

/// Represents a method call edge in the call graph
#[pyclass]
#[derive(Clone, Debug)]
pub struct MethodCall {
    /// Caller method signature
    #[pyo3(get)]
    pub caller: String,

    /// Callee method signature
    #[pyo3(get)]
    pub callee: String,

    /// Call site information (e.g., line number, expression)
    #[pyo3(get)]
    pub call_site: String,
}

#[pymethods]
impl MethodCall {
    fn __repr__(&self) -> String {
        format!("{} → {}", self.caller, self.callee)
    }
}

/// Represents a path from one method to another through the call graph
#[pyclass]
#[derive(Clone, Debug)]
pub struct CallPath {
    /// List of method signatures in the path
    #[pyo3(get)]
    pub methods: Vec<String>,

    /// List of call edges in the path
    #[pyo3(get)]
    pub calls: Vec<MethodCall>,

    /// Path length (number of hops)
    #[pyo3(get)]
    pub length: usize,
}

#[pymethods]
impl CallPath {
    fn __repr__(&self) -> String {
        self.methods.join(" → ")
    }

    /// Get the source method (first in path)
    #[pyo3(name = "get_source")]
    pub fn get_source(&self) -> Option<String> {
        self.methods.first().cloned()
    }

    /// Get the target method (last in path)
    #[pyo3(name = "get_target")]
    pub fn get_target(&self) -> Option<String> {
        self.methods.last().cloned()
    }

    /// Check if path contains a specific method
    #[pyo3(name = "contains_method")]
    pub fn contains_method(&self, method: &str) -> bool {
        self.methods.iter().any(|m| m.contains(method))
    }
}

/// Call Graph structure for analyzing method invocations
#[pyclass]
#[derive(Clone)]
pub struct CallGraph {
    /// Map from method signature to list of methods it calls
    graph: HashMap<String, Vec<MethodCall>>,

    /// Reverse map: method signature to list of methods that call it
    reverse_graph: HashMap<String, Vec<String>>,

    /// All methods in the graph
    methods: HashSet<String>,
}

impl CallGraph {
    /// Create a new empty call graph
    pub fn new() -> Self {
        Self {
            graph: HashMap::new(),
            reverse_graph: HashMap::new(),
            methods: HashSet::new(),
        }
    }

    /// Add a method call edge to the graph
    pub fn add_call(&mut self, caller: String, callee: String, call_site: String) {
        self.methods.insert(caller.clone());
        self.methods.insert(callee.clone());

        let call = MethodCall {
            caller: caller.clone(),
            callee: callee.clone(),
            call_site,
        };

        // Forward edge
        self.graph
            .entry(caller.clone())
            .or_insert_with(Vec::new)
            .push(call);

        // Reverse edge
        self.reverse_graph
            .entry(callee)
            .or_insert_with(Vec::new)
            .push(caller);
    }

    /// Get all methods called by a given method
    pub fn get_callees(&self, method: &str) -> Vec<String> {
        self.graph
            .get(method)
            .map(|calls| calls.iter().map(|c| c.callee.clone()).collect())
            .unwrap_or_default()
    }

    /// Get all methods that call a given method
    pub fn get_callers(&self, method: &str) -> Vec<String> {
        self.reverse_graph
            .get(method)
            .cloned()
            .unwrap_or_default()
    }

    /// Find all paths from source to target method (BFS with depth limit)
    pub fn find_paths(&self, source: &str, target: &str, max_depth: usize) -> Vec<CallPath> {
        let mut paths = Vec::new();
        let mut queue: VecDeque<(String, Vec<String>, Vec<MethodCall>)> = VecDeque::new();

        // Start BFS from source
        queue.push_back((source.to_string(), vec![source.to_string()], vec![]));

        while let Some((current, path, calls)) = queue.pop_front() {
            // Check depth limit
            if path.len() > max_depth {
                continue;
            }

            // Check if we reached target
            if current.contains(target) {
                paths.push(CallPath {
                    methods: path.clone(),
                    calls: calls.clone(),
                    length: path.len() - 1,
                });
                continue;
            }

            // Explore neighbors
            if let Some(method_calls) = self.graph.get(&current) {
                for call in method_calls {
                    // Avoid cycles
                    if path.contains(&call.callee) {
                        continue;
                    }

                    let mut new_path = path.clone();
                    new_path.push(call.callee.clone());

                    let mut new_calls = calls.clone();
                    new_calls.push(call.clone());

                    queue.push_back((call.callee.clone(), new_path, new_calls));
                }
            }
        }

        paths
    }

    /// Find all methods that match a pattern (e.g., "WebView.loadUrl")
    pub fn find_methods_matching(&self, pattern: &str) -> Vec<String> {
        self.methods
            .iter()
            .filter(|m| m.contains(pattern))
            .cloned()
            .collect()
    }
}

#[pymethods]
impl CallGraph {
    /// Get all methods in the graph
    #[pyo3(name = "get_all_methods")]
    pub fn get_all_methods_py(&self) -> Vec<String> {
        self.methods.iter().cloned().collect()
    }

    /// Get methods called by a given method
    #[pyo3(name = "get_callees")]
    pub fn get_callees_py(&self, method: &str) -> Vec<String> {
        self.get_callees(method)
    }

    /// Get methods that call a given method
    #[pyo3(name = "get_callers")]
    pub fn get_callers_py(&self, method: &str) -> Vec<String> {
        self.get_callers(method)
    }

    /// Find paths between two methods
    #[pyo3(name = "find_paths")]
    pub fn find_paths_py(&self, source: &str, target: &str, max_depth: Option<usize>) -> Vec<CallPath> {
        self.find_paths(source, target, max_depth.unwrap_or(10))
    }

    /// Find methods matching a pattern
    #[pyo3(name = "find_methods")]
    pub fn find_methods_py(&self, pattern: &str) -> Vec<String> {
        self.find_methods_matching(pattern)
    }

    /// Get graph statistics
    #[pyo3(name = "get_stats")]
    pub fn get_stats(&self) -> HashMap<String, usize> {
        let mut stats = HashMap::new();
        stats.insert("total_methods".to_string(), self.methods.len());
        stats.insert("total_edges".to_string(),
            self.graph.values().map(|v| v.len()).sum());
        stats
    }

    fn __repr__(&self) -> String {
        format!(
            "CallGraph(methods={}, edges={})",
            self.methods.len(),
            self.graph.values().map(|v| v.len()).sum::<usize>()
        )
    }
}

/// Call Graph Builder - constructs call graphs from decompiled classes
pub struct CallGraphBuilder {
    graph: CallGraph,
}

impl CallGraphBuilder {
    /// Create a new call graph builder
    pub fn new() -> Self {
        Self {
            graph: CallGraph::new(),
        }
    }

    /// Add a decompiled class to the call graph
    pub fn add_class(&mut self, class: &DecompiledClass) {
        for method in &class.methods {
            self.add_method(&class.class_name, method);
        }
    }

    /// Add a decompiled method to the call graph
    fn add_method(&mut self, class_name: &str, method: &DecompiledMethod) {
        let method_sig = format!("{}.{}", class_name, method.name);

        // Extract method calls from expressions
        for expr in &method.expressions {
            if let Some(call_info) = self.extract_method_call(expr) {
                let call_site = format!("{}:{}", method.name, expr.value_type);
                self.graph.add_call(method_sig.clone(), call_info, call_site);
            }
        }
    }

    /// Extract method call information from an expression
    fn extract_method_call(&self, expr: &ReconstructedExpression) -> Option<String> {
        // Check if this is a method invocation
        if expr.is_method_call {
            // Use the method_signature field if available
            if let Some(ref method_sig) = expr.method_signature {
                return Some(method_sig.clone());
            }
            // Otherwise try to parse from expression
            if let Some(method_name) = self.parse_method_from_expression(&expr.expression) {
                return Some(method_name);
            }
        }
        None
    }

    /// Parse method name from expression code
    fn parse_method_from_expression(&self, code: &str) -> Option<String> {
        // Look for patterns like: "Landroid/webkit/WebView;->loadUrl"
        // or method calls in the code

        // Simple pattern matching for now
        if code.contains("->") {
            // Extract class and method from Dalvik descriptor
            if let Some(start) = code.find('L') {
                if let Some(arrow) = code.find("->") {
                    let class_part = &code[start + 1..arrow];
                    let class_name = class_part.replace('/', ".");

                    // Extract method name
                    let method_part = &code[arrow + 2..];
                    if let Some(method_name) = method_part.split('(').next() {
                        return Some(format!("{}.{}", class_name, method_name));
                    }
                }
            }
        }

        None
    }

    /// Build and return the call graph
    pub fn build(self) -> CallGraph {
        self.graph
    }
}

/// Python wrapper for CallGraphBuilder
#[pyclass]
pub struct PyCallGraphBuilder {
    builder: CallGraphBuilder,
}

#[pymethods]
impl PyCallGraphBuilder {
    #[new]
    pub fn new() -> Self {
        Self {
            builder: CallGraphBuilder::new(),
        }
    }

    /// Add a decompiled class to the graph
    #[pyo3(name = "add_class")]
    pub fn add_class_py(&mut self, class: &DecompiledClass) {
        self.builder.add_class(class);
    }

    /// Build and return the call graph
    #[pyo3(name = "build")]
    pub fn build_py(&self) -> CallGraph {
        self.builder.graph.clone()
    }
}

/// Build a call graph from an APK file
#[pyfunction]
pub fn build_call_graph_from_apk(
    apk_path: String,
    class_filter: Option<Vec<String>>,
) -> PyResult<CallGraph> {
    use crate::apk::ApkExtractor;
    use crate::dex::parser::DexParser;
    use crate::dex::class_decompiler::decompile_class;

    let extractor = ApkExtractor::new(&apk_path)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

    let mut builder = CallGraphBuilder::new();

    // Process each DEX file
    for dex_entry in extractor.dex_entries() {
        let parser = match DexParser::new(dex_entry.data.clone()) {
            Ok(p) => p,
            Err(_) => continue,
        };

        // Process each class in the DEX file
        for class_idx in 0..parser.class_count() {
            let class_def = match parser.get_class_def(class_idx) {
                Ok(c) => c,
                Err(_) => continue,
            };

            let class_name = match parser.get_type_name(class_def.class_idx) {
                Ok(n) => n,
                Err(_) => continue,
            };

            // Apply filter if provided
            if let Some(ref filter) = class_filter {
                if !filter.iter().any(|f| class_name.contains(f)) {
                    continue;
                }
            }

            // Decompile and add to graph
            if let Ok(decompiled) = decompile_class(&parser, class_def, &dex_entry.data) {
                builder.add_class(&decompiled);
            }
        }
    }

    Ok(builder.build())
}

/// Build a call graph from an APK file (parallel version - optimized)
#[pyfunction]
pub fn build_call_graph_from_apk_parallel(
    apk_path: String,
    class_filter: Option<Vec<String>>,
) -> PyResult<CallGraph> {
    use crate::apk::ApkExtractor;
    use crate::dex::parser::DexParser;
    use crate::dex::class_decompiler::decompile_class;
    use rayon::prelude::*;
    use std::sync::Arc;

    let extractor = ApkExtractor::new(&apk_path)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

    // Collect all classes to process with shared Arc-wrapped data
    let mut tasks = Vec::new();

    for dex_entry in extractor.dex_entries() {
        // Wrap DEX data in Arc - shared across all threads, no cloning!
        let dex_data = Arc::new(dex_entry.data.clone());

        // Create parser once with cloned data (one-time cost per DEX file)
        let parser = match DexParser::new((*dex_data).clone()) {
            Ok(p) => Arc::new(p),  // Wrap parser in Arc too
            Err(_) => continue,
        };

        for class_idx in 0..parser.class_count() {
            let class_def = match parser.get_class_def(class_idx) {
                Ok(c) => c,
                Err(_) => continue,
            };

            let class_name = match parser.get_type_name(class_def.class_idx) {
                Ok(n) => n,
                Err(_) => continue,
            };

            // Apply filter if provided
            if let Some(ref filter) = class_filter {
                if !filter.iter().any(|f| class_name.contains(f)) {
                    continue;
                }
            }

            // Store: (Arc<parser>, Arc<dex_data>, class_def)
            // Arc cloning is cheap (just atomic reference count increment)
            tasks.push((Arc::clone(&parser), Arc::clone(&dex_data), class_def));
        }
    }

    // Process classes in parallel - each thread uses shared parser and data
    let decompiled_classes: Vec<_> = tasks
        .par_iter()
        .filter_map(|(parser, dex_data, class_def)| {
            // Use shared parser and data - NO CLONING!
            decompile_class(parser.as_ref(), class_def.clone(), dex_data.as_ref()).ok()
        })
        .collect();

    // Build graph from decompiled classes (sequential - fast)
    let mut builder = CallGraphBuilder::new();
    for decompiled in decompiled_classes {
        builder.add_class(&decompiled);
    }

    Ok(builder.build())
}
