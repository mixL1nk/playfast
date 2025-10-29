//! High-level bytecode analysis API
//!
//! This module provides Python-friendly wrappers for bytecode analysis

use pyo3::prelude::*;
use serde::{Deserialize, Serialize};

use super::instruction::{Instruction, InstructionDecoder};

/// Python-friendly instruction representation
#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RustInstruction {
    /// Instruction type (e.g., "const/4", "invoke-virtual")
    #[pyo3(get)]
    pub opcode: String,

    /// Destination register (if applicable)
    #[pyo3(get)]
    pub dest: Option<u8>,

    /// Constant value (for const instructions)
    #[pyo3(get)]
    pub value: Option<i64>,

    /// String value (for const-string)
    #[pyo3(get)]
    pub string_idx: Option<u32>,

    /// Method index (for invoke instructions)
    #[pyo3(get)]
    pub method_idx: Option<u32>,

    /// Argument registers (for invoke instructions)
    #[pyo3(get)]
    pub args: Vec<u8>,

    /// Raw instruction for debugging
    #[pyo3(get)]
    pub raw: String,
}

#[pymethods]
impl RustInstruction {
    /// Check if this is a const instruction
    pub fn is_const(&self) -> bool {
        self.opcode.starts_with("const")
    }

    /// Check if this is an invoke instruction
    pub fn is_invoke(&self) -> bool {
        self.opcode.starts_with("invoke")
    }

    /// Get boolean value (for const/4 with 0 or 1)
    pub fn get_boolean_value(&self) -> Option<bool> {
        if self.opcode == "const/4" {
            self.value.map(|v| v != 0)
        } else {
            None
        }
    }

    /// Convert to string representation
    pub fn __repr__(&self) -> String {
        self.raw.clone()
    }

    /// Convert to dict for JSON serialization
    pub fn to_dict(&self, py: Python) -> PyResult<Py<pyo3::types::PyAny>> {
        let dict = pyo3::types::PyDict::new(py);
        dict.set_item("opcode", &self.opcode)?;
        dict.set_item("dest", &self.dest)?;
        dict.set_item("value", &self.value)?;
        dict.set_item("string_idx", &self.string_idx)?;
        dict.set_item("method_idx", &self.method_idx)?;
        dict.set_item("args", &self.args)?;
        dict.set_item("raw", &self.raw)?;
        Ok(dict.into())
    }
}

impl From<&Instruction> for RustInstruction {
    fn from(insn: &Instruction) -> Self {
        match insn {
            Instruction::Const4 { dest, value } => RustInstruction {
                opcode: "const/4".to_string(),
                dest: Some(*dest),
                value: Some(*value as i64),
                string_idx: None,
                method_idx: None,
                args: Vec::new(),
                raw: format!("const/4 v{}, #{}", dest, value),
            },
            Instruction::Const16 { dest, value } => RustInstruction {
                opcode: "const/16".to_string(),
                dest: Some(*dest),
                value: Some(*value as i64),
                string_idx: None,
                method_idx: None,
                args: Vec::new(),
                raw: format!("const/16 v{}, #{}", dest, value),
            },
            Instruction::Const { dest, value } => RustInstruction {
                opcode: "const".to_string(),
                dest: Some(*dest),
                value: Some(*value as i64),
                string_idx: None,
                method_idx: None,
                args: Vec::new(),
                raw: format!("const v{}, #{}", dest, value),
            },
            Instruction::ConstString { dest, string_idx } => RustInstruction {
                opcode: "const-string".to_string(),
                dest: Some(*dest),
                value: None,
                string_idx: Some(*string_idx),
                method_idx: None,
                args: Vec::new(),
                raw: format!("const-string v{}, string@{}", dest, string_idx),
            },
            Instruction::InvokeVirtual { args, method_idx } => RustInstruction {
                opcode: "invoke-virtual".to_string(),
                dest: None,
                value: None,
                string_idx: None,
                method_idx: Some(*method_idx),
                args: args.clone(),
                raw: format!(
                    "invoke-virtual {{v{}}}, method@{}",
                    args.iter()
                        .map(|a| a.to_string())
                        .collect::<Vec<_>>()
                        .join(", v"),
                    method_idx
                ),
            },
            Instruction::InvokeStatic { args, method_idx } => RustInstruction {
                opcode: "invoke-static".to_string(),
                dest: None,
                value: None,
                string_idx: None,
                method_idx: Some(*method_idx),
                args: args.clone(),
                raw: format!(
                    "invoke-static {{v{}}}, method@{}",
                    args.iter()
                        .map(|a| a.to_string())
                        .collect::<Vec<_>>()
                        .join(", v"),
                    method_idx
                ),
            },
            Instruction::InvokeDirect { args, method_idx } => RustInstruction {
                opcode: "invoke-direct".to_string(),
                dest: None,
                value: None,
                string_idx: None,
                method_idx: Some(*method_idx),
                args: args.clone(),
                raw: format!(
                    "invoke-direct {{v{}}}, method@{}",
                    args.iter()
                        .map(|a| a.to_string())
                        .collect::<Vec<_>>()
                        .join(", v"),
                    method_idx
                ),
            },
            Instruction::InvokeSuper { args, method_idx } => RustInstruction {
                opcode: "invoke-super".to_string(),
                dest: None,
                value: None,
                string_idx: None,
                method_idx: Some(*method_idx),
                args: args.clone(),
                raw: format!(
                    "invoke-super {{v{}}}, method@{}",
                    args.iter()
                        .map(|a| a.to_string())
                        .collect::<Vec<_>>()
                        .join(", v"),
                    method_idx
                ),
            },
            Instruction::InvokeInterface { args, method_idx } => RustInstruction {
                opcode: "invoke-interface".to_string(),
                dest: None,
                value: None,
                string_idx: None,
                method_idx: Some(*method_idx),
                args: args.clone(),
                raw: format!(
                    "invoke-interface {{v{}}}, method@{}",
                    args.iter()
                        .map(|a| a.to_string())
                        .collect::<Vec<_>>()
                        .join(", v"),
                    method_idx
                ),
            },
            Instruction::InvokeVirtualRange {
                first_arg,
                arg_count,
                method_idx,
            } => RustInstruction {
                opcode: "invoke-virtual/range".to_string(),
                dest: None,
                value: None,
                string_idx: None,
                method_idx: Some(*method_idx),
                args: (*first_arg..(*first_arg + *arg_count as u16))
                    .map(|r| r as u8)
                    .collect(),
                raw: format!(
                    "invoke-virtual/range {{v{} .. v{}}}, method@{}",
                    first_arg,
                    first_arg + *arg_count as u16 - 1,
                    method_idx
                ),
            },
            Instruction::InvokeStaticRange {
                first_arg,
                arg_count,
                method_idx,
            } => RustInstruction {
                opcode: "invoke-static/range".to_string(),
                dest: None,
                value: None,
                string_idx: None,
                method_idx: Some(*method_idx),
                args: (*first_arg..(*first_arg + *arg_count as u16))
                    .map(|r| r as u8)
                    .collect(),
                raw: format!(
                    "invoke-static/range {{v{} .. v{}}}, method@{}",
                    first_arg,
                    first_arg + *arg_count as u16 - 1,
                    method_idx
                ),
            },
            Instruction::Unknown { opcode, .. } => RustInstruction {
                opcode: format!("unknown(0x{:02x})", opcode),
                dest: None,
                value: None,
                string_idx: None,
                method_idx: None,
                args: Vec::new(),
                raw: format!("unknown (opcode: 0x{:02x})", opcode),
            },
        }
    }
}

/// Decode bytecode into instructions
#[pyfunction]
pub fn decode_bytecode(bytecode: Vec<u16>) -> Vec<RustInstruction> {
    let instructions = InstructionDecoder::decode(&bytecode);
    instructions.iter().map(RustInstruction::from).collect()
}

/// Extract constant values from bytecode
#[pyfunction]
pub fn extract_constants(bytecode: Vec<u16>) -> Vec<i64> {
    let instructions = InstructionDecoder::decode(&bytecode);
    let mut constants = Vec::new();

    for insn in instructions {
        match insn {
            Instruction::Const4 { value, .. } => constants.push(value as i64),
            Instruction::Const16 { value, .. } => constants.push(value as i64),
            Instruction::Const { value, .. } => constants.push(value as i64),
            _ => {}
        }
    }

    constants
}

/// Extract method calls from bytecode
#[pyfunction]
pub fn extract_method_calls(bytecode: Vec<u16>) -> Vec<u32> {
    let instructions = InstructionDecoder::decode(&bytecode);
    let mut method_calls = Vec::new();

    for insn in instructions {
        match insn {
            Instruction::InvokeVirtual { method_idx, .. }
            | Instruction::InvokeStatic { method_idx, .. }
            | Instruction::InvokeDirect { method_idx, .. }
            | Instruction::InvokeSuper { method_idx, .. }
            | Instruction::InvokeInterface { method_idx, .. }
            | Instruction::InvokeVirtualRange { method_idx, .. }
            | Instruction::InvokeStaticRange { method_idx, .. } => {
                method_calls.push(method_idx);
            }
            _ => {}
        }
    }

    method_calls
}
