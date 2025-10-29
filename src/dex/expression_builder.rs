//! Phase 2: Simple Expression Reconstruction
//!
//! This module reconstructs simple Java-like expressions from Dalvik bytecode
//! by tracking register values and building expression trees.

use crate::dex::instruction::{Instruction, InstructionDecoder};
use crate::dex::method_resolver::{MethodResolver, MethodSignature};
use crate::dex::parser::DexParser;
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Represents a value in a register
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RegisterValue {
    /// Unknown value
    Unknown,
    /// Constant integer
    ConstInt(i64),
    /// Constant string
    ConstString(String),
    /// Method call result
    MethodCall {
        receiver: Box<RegisterValue>,
        signature: MethodSignature,
        args: Vec<RegisterValue>,
    },
    /// Field access
    FieldAccess {
        receiver: Box<RegisterValue>,
        field_name: String,
        field_type: String,
    },
    /// This reference
    This,
    /// Parameter reference
    Parameter(usize),
}

impl RegisterValue {
    /// Format as Java-like expression
    pub fn format(&self) -> String {
        match self {
            RegisterValue::Unknown => "?".to_string(),
            RegisterValue::ConstInt(val) => {
                // Format booleans specially
                if *val == 0 {
                    "false".to_string()
                } else if *val == 1 {
                    "true".to_string()
                } else {
                    val.to_string()
                }
            }
            RegisterValue::ConstString(s) => format!("\"{}\"", s),
            RegisterValue::MethodCall {
                receiver,
                signature,
                args,
            } => {
                let receiver_str = receiver.format();
                let args_str: Vec<String> = args.iter().map(|a| a.format()).collect();
                format!(
                    "{}.{}({})",
                    receiver_str,
                    signature.method_name,
                    args_str.join(", ")
                )
            }
            RegisterValue::FieldAccess {
                receiver,
                field_name,
                ..
            } => {
                let receiver_str = receiver.format();
                format!("{}.{}", receiver_str, field_name)
            }
            RegisterValue::This => "this".to_string(),
            RegisterValue::Parameter(idx) => format!("param{}", idx),
        }
    }

    /// Check if this is a boolean constant
    pub fn is_boolean(&self) -> Option<bool> {
        match self {
            RegisterValue::ConstInt(0) => Some(false),
            RegisterValue::ConstInt(1) => Some(true),
            _ => None,
        }
    }
}

/// Python-friendly reconstructed expression
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReconstructedExpression {
    #[pyo3(get)]
    pub expression: String,
    #[pyo3(get)]
    pub value_type: String,
    #[pyo3(get)]
    pub is_method_call: bool,
    #[pyo3(get)]
    pub method_signature: Option<String>,
}

#[pymethods]
impl ReconstructedExpression {
    fn __repr__(&self) -> String {
        format!(
            "ReconstructedExpression(expression='{}', type='{}')",
            self.expression, self.value_type
        )
    }
}

/// Expression reconstructor
pub struct ExpressionBuilder {
    resolver: MethodResolver,
    /// Track register values
    registers: HashMap<u8, RegisterValue>,
    /// Current instruction index
    pc: usize,
}

impl ExpressionBuilder {
    pub fn new(parser: DexParser) -> Self {
        Self {
            resolver: MethodResolver::new(parser),
            registers: HashMap::new(),
            pc: 0,
        }
    }

    /// Process bytecode and reconstruct expressions
    pub fn process_bytecode(&mut self, bytecode: &[u16]) -> std::result::Result<Vec<ReconstructedExpression>, String> {
        let instructions = InstructionDecoder::decode(bytecode);
        let mut expressions = Vec::new();

        self.pc = 0;
        for insn in instructions {
            if let Some(expr) = self.process_instruction(&insn)? {
                expressions.push(expr);
            }
            self.pc += 1;
        }

        Ok(expressions)
    }

    /// Process a single instruction
    fn process_instruction(&mut self, insn: &Instruction) -> std::result::Result<Option<ReconstructedExpression>, String> {
        match insn {
            // Const instructions
            Instruction::Const4 { dest, value } => {
                self.registers
                    .insert(*dest, RegisterValue::ConstInt(*value as i64));
                Ok(None)
            }
            Instruction::Const16 { dest, value } => {
                self.registers
                    .insert(*dest, RegisterValue::ConstInt(*value as i64));
                Ok(None)
            }
            Instruction::Const { dest, value } => {
                self.registers
                    .insert(*dest, RegisterValue::ConstInt(*value as i64));
                Ok(None)
            }

            // String constants
            Instruction::ConstString { dest, string_idx } => {
                // Try to resolve string - parser.get_string expects u32
                if let Ok(string_value) = self.resolver.resolve_string(*string_idx) {
                    self.registers
                        .insert(*dest, RegisterValue::ConstString(string_value));
                } else {
                    self.registers.insert(*dest, RegisterValue::Unknown);
                }
                Ok(None)
            }

            // Method invocations - this is where we reconstruct expressions
            Instruction::InvokeVirtual { args, method_idx }
            | Instruction::InvokeSuper { args, method_idx }
            | Instruction::InvokeDirect { args, method_idx }
            | Instruction::InvokeStatic { args, method_idx }
            | Instruction::InvokeInterface { args, method_idx } => {
                self.process_method_call(args, *method_idx)
            }

            // All other instructions (including moves) - just skip for now
            _ => Ok(None),
        }
    }

    /// Process method call and reconstruct expression
    fn process_method_call(
        &mut self,
        args: &[u8],
        method_idx: u32,
    ) -> std::result::Result<Option<ReconstructedExpression>, String> {
        // Resolve method signature
        let signature = match self.resolver.resolve(method_idx) {
            Ok(sig) => sig,
            Err(_) => return Ok(None), // Skip if we can't resolve
        };

        if args.is_empty() {
            return Ok(None);
        }

        // First arg is the receiver (for non-static methods)
        let receiver_reg = args[0];
        let receiver = self
            .registers
            .get(&receiver_reg)
            .cloned()
            .unwrap_or(RegisterValue::Unknown);

        // Rest are method arguments
        let method_args: Vec<RegisterValue> = args[1..]
            .iter()
            .map(|&reg| {
                self.registers
                    .get(&reg)
                    .cloned()
                    .unwrap_or(RegisterValue::Unknown)
            })
            .collect();

        // Create method call value
        let call_value = RegisterValue::MethodCall {
            receiver: Box::new(receiver),
            signature: signature.clone(),
            args: method_args,
        };

        // Format as expression
        let expression = call_value.format();

        // Determine if this is a significant call we want to report
        let is_significant = signature.is_set_javascript_enabled()
            || signature.is_webview_method()
            || expression.contains("WebSettings")
            || expression.contains("WebView");

        if is_significant {
            Ok(Some(ReconstructedExpression {
                expression,
                value_type: signature.return_type.clone(),
                is_method_call: true,
                method_signature: Some(signature.full_signature),
            }))
        } else {
            // Store for potential use in chain, but don't report
            // (Store in a hypothetical result register - simplified)
            Ok(None)
        }
    }
}

/// Python wrapper for ExpressionBuilder
#[pyclass]
pub struct ExpressionBuilderPy {
    builder: ExpressionBuilder,
}

#[pymethods]
impl ExpressionBuilderPy {
    /// Reconstruct expressions from bytecode
    pub fn reconstruct(&mut self, bytecode: Vec<u16>) -> PyResult<Vec<ReconstructedExpression>> {
        self.builder
            .process_bytecode(&bytecode)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }
}

/// Create an expression builder from DEX data
#[pyfunction]
pub fn create_expression_builder(dex_data: Vec<u8>) -> PyResult<ExpressionBuilderPy> {
    let parser = DexParser::new(dex_data)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(ExpressionBuilderPy {
        builder: ExpressionBuilder::new(parser),
    })
}

/// Reconstruct expressions from APK
#[pyfunction]
pub fn reconstruct_expressions_from_apk(
    apk_path: String,
    class_name: String,
    method_name: String,
) -> PyResult<Vec<ReconstructedExpression>> {
    use crate::apk::ApkExtractor;
    use crate::dex::code_extractor::find_method_bytecode;

    // Extract DEX files from APK
    let extractor = ApkExtractor::new(&apk_path)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

    for dex_entry in extractor.dex_entries() {
        if let Ok(parser) = DexParser::new(dex_entry.data.clone()) {
            // Try to find the method
            if let Ok(Some(bytecode)) = find_method_bytecode(&parser, &class_name, &method_name) {
                // Create a new parser for the builder
                if let Ok(parser2) = DexParser::new(dex_entry.data.clone()) {
                    let mut builder = ExpressionBuilder::new(parser2);
                    return builder
                        .process_bytecode(&bytecode)
                        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e));
                }
            }
        }
    }

    Ok(Vec::new())
}
