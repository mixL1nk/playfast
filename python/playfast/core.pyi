# ============================================================================
# Google Play Store Types
# ============================================================================

class RustAppInfo:
    app_id: str
    title: str
    developer: str
    icon: str
    score: float
    ratings: int
    price: float
    currency: str
    free: bool
    description: str | None
    summary: str | None
    installs: str | None
    min_installs: int | None
    score_text: str | None
    released: str | None
    updated: str | None
    version: str | None
    required_android_version: str | None
    content_rating: str | None
    content_rating_description: str | None
    ad_supported: bool | None
    contains_ads: bool | None
    in_app_purchases: bool | None
    editors_choice: bool | None
    developer_id: str | None
    developer_email: str | None
    developer_website: str | None
    developer_address: str | None
    privacy_policy: str | None
    genre: str | None
    genre_id: str | None
    category: str | None
    video: str | None
    video_image: str | None
    screenshots: list[str]
    similar: list[str]
    permissions: list[RustPermission]

class RustReview:
    review_id: str
    user_name: str
    user_image: str
    content: str
    score: int
    thumbs_up: int
    created_at: int
    reply_content: str | None
    reply_at: int | None

class RustSearchResult:
    app_id: str
    title: str
    developer: str
    icon: str
    score: float | None
    price: float
    currency: str

class RustPermission:
    group: str
    permissions: list[str]
    def __len__(self) -> int: ...

def parse_app_page(html: str, app_id: str) -> RustAppInfo: ...
def parse_review_batch(html: str) -> list[RustReview]: ...
def parse_search_results(html: str) -> list[RustSearchResult]: ...
def extract_continuation_token(html: str) -> str | None: ...
def parse_batchexecute_list_response(response_text: str) -> list[RustSearchResult]: ...
def build_list_request_body(
    category: str | None, collection: str, num: int = 100
) -> str: ...
def build_reviews_request_body(
    app_id: str, sort: int, continuation_token: str | None, lang: str, country: str
) -> str: ...
def parse_batchexecute_reviews_response(
    response_text: str,
) -> tuple[list[RustReview], str | None]: ...

# Single request functions (HTTP + parsing)
def fetch_and_parse_app(
    app_id: str, lang: str, country: str, _timeout: int = 30
) -> RustAppInfo: ...
def fetch_and_parse_reviews(
    app_id: str,
    lang: str,
    country: str,
    sort: int = 1,
    continuation_token: str | None = None,
    _timeout: int = 30,
) -> tuple[list[RustReview], str | None]: ...
def fetch_and_parse_search(
    query: str, lang: str, country: str, _timeout: int = 30
) -> list[RustSearchResult]: ...
def fetch_and_parse_list(
    category: str | None,
    collection: str,
    lang: str,
    country: str,
    num: int = 100,
    _timeout: int = 30,
) -> list[RustSearchResult]: ...

# Batch functions for parallel processing (recommended for multiple requests)
def fetch_and_parse_apps_batch(
    requests: list[tuple[str, str, str]],
) -> list[RustAppInfo]: ...
def fetch_and_parse_list_batch(
    requests: list[tuple[str | None, str, str, str, int]],
) -> list[list[RustSearchResult]]: ...
def fetch_and_parse_search_batch(
    requests: list[tuple[str, str, str]],
) -> list[list[RustSearchResult]]: ...
def fetch_and_parse_reviews_batch(
    requests: list[tuple[str, str, str, int, str | None]],
) -> list[tuple[list[RustReview], str | None]]: ...

# ============================================================================
# APK Analysis Types
# ============================================================================

class RustDexClass:
    """DEX class information"""
    class_name: str
    access_flags: int
    superclass: str | None
    interfaces: list[str]
    source_file: str | None
    methods: list[RustDexMethod]
    fields: list[RustDexField]

class RustDexMethod:
    """DEX method information"""
    class_name: str
    method_name: str
    descriptor: str
    access_flags: int
    code_off: int

class RustDexField:
    """DEX field information"""
    class_name: str
    field_name: str
    type_descriptor: str
    access_flags: int

class RustReferencePool:
    """Reference pool for DEX file"""
    def __len__(self) -> int: ...

class RustManifestInfo:
    """Android manifest information"""
    package: str
    version_code: str | None
    version_name: str | None
    min_sdk_version: int | None
    target_sdk_version: int | None
    permissions: list[str]
    activities: list[str]
    services: list[str]
    receivers: list[str]
    providers: list[str]

class IntentFilterData:
    """Intent filter data"""
    actions: list[str]
    categories: list[str]
    schemes: list[str]
    hosts: list[str]

class ActivityIntentFilter:
    """Activity with intent filters"""
    activity: str
    filters: list[IntentFilterData]

class RustInstruction:
    """DEX bytecode instruction"""
    opcode: str
    operands: list[int]

class MethodSignature:
    """Method signature for resolution"""
    class_name: str
    method_name: str
    descriptor: str

# ============================================================================
# Entry Point Analysis
# ============================================================================

class ComponentType:
    """Android component type enum"""
    Activity: str
    Service: str
    BroadcastReceiver: str
    ContentProvider: str

class EntryPoint:
    """Android entry point (Activity, Service, etc.)"""
    class_name: str
    component_type: str
    lifecycle_methods: list[str]
    is_exported: bool
    intent_filters: list[IntentFilterData]
    is_deeplink_handler: bool

class PyEntryPointAnalyzer:
    """Entry point analyzer"""
    def analyze(self) -> list[EntryPoint]:
        """Analyze all entry points"""
        ...

    def get_deeplink_handlers(self) -> list[EntryPoint]:
        """Get only deeplink handler entry points"""
        ...

    def get_stats(self) -> dict[str, int]:
        """Get analysis statistics"""
        ...

def analyze_entry_points_from_apk(apk_path: str) -> PyEntryPointAnalyzer:
    """Create entry point analyzer from APK"""
    ...

# ============================================================================
# Call Graph Analysis
# ============================================================================

class MethodCall:
    """A method call in the call graph"""
    caller: str
    callee: str
    call_sites: int

class CallPath:
    """A path through the call graph"""
    methods: list[str]
    length: int

class CallGraph:
    """Call graph for an APK"""
    def find_methods_matching(self, pattern: str) -> list[str]:
        """Find methods matching a pattern"""
        ...

    def find_paths(
        self,
        start_methods: list[str],
        target_methods: list[str],
        max_depth: int
    ) -> list[CallPath]:
        """Find paths from start to target methods"""
        ...

    def get_stats(self) -> dict[str, int]:
        """Get call graph statistics"""
        ...

class PyCallGraphBuilder:
    """Call graph builder"""
    def build(self) -> CallGraph:
        """Build the call graph"""
        ...

def build_call_graph_from_apk(
    apk_path: str,
    package_filter: str | None = None
) -> CallGraph:
    """Build call graph from APK (single-threaded)"""
    ...

def build_call_graph_from_apk_parallel(
    apk_path: str,
    package_prefixes: list[str] | None = None
) -> CallGraph:
    """Build call graph from APK (parallel)"""
    ...

# ============================================================================
# Data Flow Analysis (New Generic API)
# ============================================================================

class Flow:
    """Data flow from entry point to sink method"""
    entry_point: str
    component_type: str
    sink_method: str
    paths: list[CallPath]
    is_deeplink_handler: bool
    min_path_length: int
    path_count: int

    def get_shortest_path(self) -> CallPath | None:
        """Get the shortest path"""
        ...

    def get_lifecycle_methods(self) -> list[str]:
        """Get all lifecycle methods involved"""
        ...

class DataFlow:
    """Data flow from source to sink with confidence"""
    source: str
    sink: str
    flow_path: list[str]
    confidence: float

class DataFlowAnalyzer:
    """Generic data flow analyzer"""
    def find_flows_to(
        self,
        sink_patterns: list[str],
        max_depth: int = 10
    ) -> list[Flow]:
        """Find flows to sinks matching patterns"""
        ...

    def find_webview_flows(self, max_depth: int = 10) -> list[Flow]:
        """Find flows to WebView methods"""
        ...

    def find_file_flows(self, max_depth: int = 10) -> list[Flow]:
        """Find flows to file I/O methods"""
        ...

    def find_network_flows(self, max_depth: int = 10) -> list[Flow]:
        """Find flows to network methods"""
        ...

    def find_sql_flows(self, max_depth: int = 10) -> list[Flow]:
        """Find flows to SQL methods"""
        ...

def create_data_flow_analyzer(apk_path: str) -> DataFlowAnalyzer:
    """Create data flow analyzer from APK (optimized with entry point filtering)"""
    ...

def find_flows_from_apk(
    apk_path: str,
    sink_patterns: list[str],
    max_depth: int = 10
) -> list[Flow]:
    """Find flows to custom sink patterns"""
    ...

def find_webview_flows_from_apk(
    apk_path: str,
    max_depth: int = 10
) -> list[Flow]:
    """Find WebView flows (optimized)"""
    ...

def find_file_flows_from_apk(
    apk_path: str,
    max_depth: int = 10
) -> list[Flow]:
    """Find file I/O flows (optimized)"""
    ...

def find_network_flows_from_apk(
    apk_path: str,
    max_depth: int = 10
) -> list[Flow]:
    """Find network flows (optimized)"""
    ...

# ============================================================================
# Backward Compatibility (Deprecated - use DataFlowAnalyzer instead)
# ============================================================================

# Type aliases for backward compatibility
WebViewFlow = Flow
WebViewFlowAnalyzer = DataFlowAnalyzer

def analyze_webview_flows_from_apk(
    apk_path: str,
    max_depth: int = 5
) -> list[Flow]:
    """Deprecated: Use find_webview_flows_from_apk instead"""
    ...

def create_webview_analyzer_from_apk(apk_path: str) -> DataFlowAnalyzer:
    """Deprecated: Use create_data_flow_analyzer instead"""
    ...

# ============================================================================
# APK Extraction Functions
# ============================================================================

def extract_apk_info(apk_path: str) -> tuple[int, bool, bool, list[str]]:
    """Extract basic APK info (size, signed, multidex, dex_files)"""
    ...

def extract_manifest_raw(apk_path: str) -> bytes:
    """Extract raw AndroidManifest.xml"""
    ...

def parse_manifest_from_apk(apk_path: str) -> RustManifestInfo:
    """Parse AndroidManifest.xml from APK"""
    ...

def extract_classes_from_apk(
    apk_path: str,
    parallel: bool = True
) -> list[RustDexClass]:
    """Extract all classes from APK"""
    ...

def search_classes(
    apk_path: str,
    name: str | None = None,
    package: str | None = None,
    extends: str | None = None,
    implements: str | None = None,
    parallel: bool = True
) -> list[RustDexClass]:
    """Search for classes matching criteria"""
    ...

def search_methods(
    apk_path: str,
    class_name: str | None = None,
    method_name: str | None = None,
    descriptor: str | None = None,
    access_flags: int | None = None,
    parallel: bool = True
) -> list[RustDexMethod]:
    """Search for methods matching criteria"""
    ...

# ============================================================================
# Bytecode Analysis Functions
# ============================================================================

def decode_bytecode(bytecode: bytes) -> list[RustInstruction]:
    """Decode DEX bytecode to instructions"""
    ...

def extract_constants(bytecode: bytes) -> list[str]:
    """Extract string constants from bytecode"""
    ...

def extract_method_calls(bytecode: bytes) -> list[str]:
    """Extract method calls from bytecode"""
    ...

def extract_methods_bytecode(
    classes: list[RustDexClass]
) -> dict[str, bytes]:
    """Extract bytecode for all methods"""
    ...

def get_method_bytecode_from_apk(
    apk_path: str,
    class_name: str,
    method_name: str
) -> bytes | None:
    """Get bytecode for a specific method"""
    ...

# ============================================================================
# Method Resolution Functions
# ============================================================================

class MethodResolverPy:
    """Method resolver for virtual/interface calls"""
    def resolve_method(
        self,
        class_name: str,
        method_name: str,
        descriptor: str
    ) -> str | None:
        """Resolve method to actual implementation"""
        ...

def create_method_resolver(apk_path: str) -> MethodResolverPy:
    """Create method resolver from APK"""
    ...

def resolve_method_from_apk(
    apk_path: str,
    class_name: str,
    method_name: str,
    descriptor: str
) -> str | None:
    """Resolve a single method"""
    ...

# ============================================================================
# Expression Reconstruction Functions
# ============================================================================

class ReconstructedExpression:
    """Reconstructed high-level expression"""
    method: str
    expressions: list[str]

class ExpressionBuilderPy:
    """Expression builder"""
    def reconstruct_expressions(
        self,
        class_name: str,
        method_name: str
    ) -> ReconstructedExpression | None:
        """Reconstruct expressions for a method"""
        ...

def create_expression_builder(apk_path: str) -> ExpressionBuilderPy:
    """Create expression builder from APK"""
    ...

def reconstruct_expressions_from_apk(
    apk_path: str,
    class_name: str,
    method_name: str
) -> ReconstructedExpression | None:
    """Reconstruct expressions for a specific method"""
    ...

# ============================================================================
# Class Decompilation Functions
# ============================================================================

class DecompiledMethod:
    """Decompiled method"""
    name: str
    descriptor: str
    access_flags: int
    code: str

class DecompiledClass:
    """Decompiled class"""
    class_name: str
    access_flags: int
    superclass: str | None
    interfaces: list[str]
    fields: list[str]
    methods: list[DecompiledMethod]

def decompile_class_from_apk(
    apk_path: str,
    class_name: str
) -> DecompiledClass | None:
    """Decompile a class to pseudo-Java code"""
    ...

# ============================================================================
# Resources Functions
# ============================================================================

class PyResolvedResource:
    """Resolved resource"""
    resource_id: int
    resource_type: str
    resource_name: str
    value: str

class PyResourceResolver:
    """Resource resolver"""
    def resolve_resource(self, resource_id: int) -> PyResolvedResource | None:
        """Resolve resource ID to value"""
        ...

    def get_string(self, resource_id: int) -> str | None:
        """Get string resource"""
        ...

def parse_resources_from_apk(apk_path: str) -> PyResourceResolver:
    """Parse resources.arsc from APK"""
    ...

# ============================================================================
# DEX Filter Classes
# ============================================================================

class ClassFilter:
    """Filter for DEX classes"""
    def __init__(
        self,
        name: str | None = None,
        package: str | None = None,
        extends: str | None = None,
        implements: str | None = None
    ): ...

class MethodFilter:
    """Filter for DEX methods"""
    def __init__(
        self,
        class_name: str | None = None,
        method_name: str | None = None,
        descriptor: str | None = None,
        access_flags: int | None = None
    ): ...
