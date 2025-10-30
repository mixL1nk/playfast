pub mod error;
pub mod models;
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
// New generic API
