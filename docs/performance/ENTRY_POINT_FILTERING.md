# Entry-Point-Driven Call Graph Analysis

## Problem Statement

### Current Implementation (Full Analysis)

```
1. Decompile ALL classes in APK (669 methods, ~142s)
2. Build complete call graph
3. Search paths from entry points to WebView

Issues:
- Analyzes many unreachable methods (dead code)
- Wastes time on library code not called by entry points
- No early termination even if target is found
```

**Example**: If an APK has 10,000 methods but only 1,000 are reachable from entry points, we waste 90% of analysis time!

### Proposed Solution (Incremental Analysis)

```
1. Start from entry points (141 entry points)
2. BFS: Decompile only reachable classes
3. Stop when max_depth reached or all targets found

Benefits:
- Analyze only necessary code
- Faster for typical security analysis workflows
- Better scalability for large APKs
```

## Algorithm Design

### Phase 1: Forward Reachability (Entry → Callees)

```rust
fn build_call_graph_from_entry_points(
    apk_path: String,
    entry_classes: Vec<String>,  // Entry point class names
    max_depth: usize,
) -> CallGraph {
    let mut graph = CallGraph::new();
    let mut queue = VecDeque::new();
    let mut visited = HashSet::new();
    let mut depth_map = HashMap::new();

    // Initialize with entry points
    for entry_class in entry_classes {
        queue.push_back(entry_class.clone());
        depth_map.insert(entry_class, 0);
    }

    while let Some(class_name) = queue.pop_front() {
        let current_depth = depth_map[&class_name];

        if current_depth >= max_depth {
            continue;  // Don't go deeper
        }

        if visited.contains(&class_name) {
            continue;  // Already processed
        }
        visited.insert(class_name.clone());

        // Decompile this class (on-demand)
        let decompiled = decompile_class_by_name(&apk_path, &class_name)?;
        graph.add_class(&decompiled);

        // Find all callees
        for method in &decompiled.methods {
            for callee in extract_method_calls(method) {
                let callee_class = extract_class_name(&callee);

                if !visited.contains(&callee_class) {
                    queue.push_back(callee_class.clone());
                    depth_map.insert(callee_class, current_depth + 1);
                }
            }
        }
    }

    graph
}
```

### Phase 2: Backward Reachability (Target ← Callers)

For WebView analysis, we also need to find **who calls WebView methods**:

```rust
fn add_backward_reachability(
    graph: &mut CallGraph,
    apk_path: String,
    target_methods: Vec<String>,  // e.g., ["WebView.loadUrl"]
    max_depth: usize,
) {
    // Find all callers of target methods
    let mut queue = VecDeque::new();
    let mut visited = HashSet::new();

    for target in target_methods {
        queue.push_back(target);
    }

    while let Some(method) = queue.pop_front() {
        // Search all classes for callers
        for class in all_classes {
            if let Some(callers) = find_callers_in_class(class, &method) {
                for caller in callers {
                    if !visited.contains(&caller) {
                        graph.add_class(decompile_class_by_name(&caller)?);
                        queue.push_back(caller);
                        visited.insert(caller);
                    }
                }
            }
        }
    }
}
```

### Phase 3: Hybrid Approach (Best of Both)

```rust
pub fn build_call_graph_for_webview_analysis(
    apk_path: String,
    entry_points: Vec<String>,
    max_depth: usize,
) -> CallGraph {
    // 1. Forward from entry points
    let mut graph = build_call_graph_from_entry_points(
        apk_path.clone(),
        entry_points,
        max_depth
    );

    // 2. Backward from WebView APIs
    let webview_methods = vec![
        "Landroid/webkit/WebView;.loadUrl",
        "Landroid/webkit/WebView;.evaluateJavascript",
        "Landroid/webkit/WebView;.loadData",
    ];

    add_backward_reachability(
        &mut graph,
        apk_path,
        webview_methods,
        max_depth
    );

    graph
}
```

## Implementation Challenges

### Challenge 1: Finding Class by Name

**Problem**: Current `DexParser` requires iterating all classes to find one by name.

**Solution**: Build a class name index:

```rust
pub struct DexIndex {
    class_name_to_idx: HashMap<String, usize>,
    dex_data: Arc<Vec<u8>>,
}

impl DexIndex {
    pub fn new(dex_data: Vec<u8>) -> Self {
        let parser = DexParser::new(dex_data.clone());
        let mut index = HashMap::new();

        for idx in 0..parser.class_count() {
            if let Ok(class_def) = parser.get_class_def(idx) {
                if let Ok(name) = parser.get_type_name(class_def.class_idx) {
                    index.insert(name, idx);
                }
            }
        }

        DexIndex {
            class_name_to_idx: index,
            dex_data: Arc::new(dex_data),
        }
    }

    pub fn find_class(&self, name: &str) -> Option<ClassDef> {
        let idx = self.class_name_to_idx.get(name)?;
        let parser = DexParser::new((*self.dex_data).clone()).ok()?;
        parser.get_class_def(*idx).ok()
    }
}
```

### Challenge 2: Backward Search Efficiency

**Problem**: Finding all callers of a method requires scanning all classes.

**Solution Option 1**: Build reverse index during forward pass:

```rust
struct ReverseCallIndex {
    callee_to_callers: HashMap<String, Vec<String>>,
}
```

**Solution Option 2**: Limit backward search to already-analyzed classes only.

### Challenge 3: Incremental Graph Building

**Problem**: `CallGraphBuilder` expects all classes upfront.

**Solution**: Make it incremental:

```rust
impl CallGraphBuilder {
    pub fn add_class(&mut self, decompiled: &DecompiledClass) {
        // Already incremental! No changes needed.
    }

    pub fn build_incremental(self) -> CallGraph {
        // Can call build() at any time
        self.build()
    }
}
```

## Performance Analysis

### Expected Improvements

**Scenario 1: Small entry point footprint**

- Entry points: 141
- Reachable methods: ~200 (estimate)
- Total methods: 669

**Savings**:

- Old: Analyze 669 methods = 142s
- New: Analyze 200 methods = **42s** (70% faster!)

**Scenario 2: Large APK with libraries**

- Entry points: 500
- Reachable methods: ~5,000
- Total methods: 50,000 (includes unused libraries)

**Savings**:

- Old: Analyze 50,000 methods = 35 minutes
- New: Analyze 5,000 methods = **3.5 minutes** (90% faster!)

### Worst Case

If ALL methods are reachable:

- New approach = Old approach + small index overhead (~5%)
- Still acceptable

## API Design

### New Public API

```rust
/// Build call graph starting from entry points (incremental)
#[pyfunction]
pub fn build_call_graph_from_entry_points_incremental(
    apk_path: String,
    entry_point_classes: Vec<String>,
    max_depth: usize,
) -> PyResult<CallGraph>

/// Optimized for WebView analysis (hybrid approach)
#[pyfunction]
pub fn build_call_graph_for_webview(
    apk_path: String,
    entry_points: Vec<String>,
    max_depth: usize,
) -> PyResult<CallGraph>
```

### Python Usage

```python
from playfast import core

# Get entry points
analyzer = core.analyze_entry_points_from_apk("app.apk")
entry_points = analyzer.analyze()

# Extract class names
entry_classes = [ep["class_name"] for ep in entry_points]

# Build incremental graph (only reachable methods)
graph = core.build_call_graph_from_entry_points_incremental(
    "app.apk", entry_classes, max_depth=10
)

# Or use optimized WebView version
graph = core.build_call_graph_for_webview("app.apk", entry_classes, max_depth=10)
```

### Backward Compatible

Keep existing API for full analysis:

```python
# Full analysis (all methods) - still available
graph = core.build_call_graph_from_apk_parallel("app.apk", None)

# Incremental analysis (recommended for WebView)
graph = core.build_call_graph_for_webview("app.apk", entry_classes, 10)
```

## Implementation Plan

### Phase 1: Infrastructure (Week 1)

1. **DexIndex**: Class name → ClassDef lookup
1. **Incremental decompilation**: Decompile single class by name
1. **Unit tests**: Verify index correctness

### Phase 2: Forward Reachability (Week 2)

1. **BFS from entry points**: Implement algorithm
1. **Parallel incremental**: Parallelize BFS exploration
1. **Benchmark**: Compare with full analysis

### Phase 3: Backward Reachability (Week 3)

1. **Reverse index**: Build caller→callee map
1. **Hybrid algorithm**: Forward + backward
1. **WebView optimization**: Specialized for security analysis

### Phase 4: Integration (Week 4)

1. **Update WebViewFlowAnalyzer**: Use incremental graph
1. **Documentation**: Update all guides
1. **Migration**: Add deprecation warnings for old API

## Success Metrics

- **Performance**: 50-90% faster for typical APKs
- **Correctness**: Same results as full analysis (for reachable code)
- **Memory**: Lower peak usage (incremental processing)
- **Usability**: Simpler API for security workflows

## Trade-offs

### Pros

✅ Much faster for typical use cases
✅ Better scalability
✅ Lower memory footprint
✅ Focused analysis (security-relevant code only)

### Cons

❌ Slightly more complex implementation
❌ Requires building index (one-time cost ~3s)
❌ May miss dead code (but that's usually desired!)
❌ Backward search can be expensive if not optimized

## Conclusion

Entry-point-driven analysis is a **significant optimization** for security analysis workflows. By analyzing only reachable code, we can:

- Reduce analysis time by 50-90%
- Handle larger APKs
- Focus on security-relevant code paths

**Recommendation**: Implement this as the new default for WebView analysis, while keeping full analysis available for completeness checking.

______________________________________________________________________

**Status**: Design complete, ready for implementation
**Estimated effort**: 3-4 weeks
**Expected improvement**: 50-90% faster
