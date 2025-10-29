pub mod error;
pub mod models;
pub mod decoder;
pub mod filter;
pub mod container;
pub mod search;
pub mod parser;
pub mod constants;
pub mod instruction;
pub mod bytecode;
pub mod code_extractor;
pub mod method_resolver;
pub mod expression_builder;
pub mod class_decompiler;
pub mod entry_point_analyzer;
pub mod call_graph;
pub mod data_flow_analyzer;

pub use error::DexError;
pub use models::{RustDexClass, RustDexMethod, RustDexField, RustReferencePool};
pub use filter::{ClassFilter, MethodFilter};
pub use container::DexContainer;
pub use search::DexSearcher;
pub use parser::DexParser;
pub use constants::access_flags;
pub use instruction::{Instruction, InstructionDecoder, Opcode};
pub use bytecode::{RustInstruction, decode_bytecode, extract_constants, extract_method_calls};
pub use code_extractor::{extract_methods_bytecode, get_method_bytecode_from_apk};
pub use method_resolver::{MethodSignature, MethodResolverPy, create_method_resolver, resolve_method_from_apk};
pub use expression_builder::{ReconstructedExpression, ExpressionBuilderPy, create_expression_builder, reconstruct_expressions_from_apk};
pub use class_decompiler::{DecompiledClass, DecompiledMethod, decompile_class_from_apk};
pub use entry_point_analyzer::{EntryPoint, ComponentType, PyEntryPointAnalyzer, analyze_entry_points_from_apk};
pub use call_graph::{CallGraph, CallPath, MethodCall, PyCallGraphBuilder, build_call_graph_from_apk, build_call_graph_from_apk_parallel};
// New generic API
pub use data_flow_analyzer::{
    Flow, DataFlow, DataFlowAnalyzer,
    create_data_flow_analyzer,
    find_flows_from_apk,
    find_webview_flows_from_apk,
    find_file_flows_from_apk,
    find_network_flows_from_apk,
    // Backward compatibility
    WebViewFlow, WebViewFlowAnalyzer,
    analyze_webview_flows_from_apk,
    create_webview_analyzer_from_apk,
};
