//! Dalvik bytecode instruction decoder
//!
//! Reference:
//! - https://source.android.com/docs/core/runtime/dalvik-bytecode
//! - https://github.com/androguard/androguard

use std::fmt;

/// Dalvik instruction opcodes
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum Opcode {
    Nop = 0x00,
    Move = 0x01,
    MoveFrom16 = 0x02,
    Move16 = 0x03,
    MoveWide = 0x04,
    MoveWideFrom16 = 0x05,
    MoveWide16 = 0x06,
    MoveObject = 0x07,
    MoveObjectFrom16 = 0x08,
    MoveObject16 = 0x09,
    MoveResult = 0x0a,
    MoveResultWide = 0x0b,
    MoveResultObject = 0x0c,
    MoveException = 0x0d,
    ReturnVoid = 0x0e,
    Return = 0x0f,
    ReturnWide = 0x10,
    ReturnObject = 0x11,

    // Constants
    Const4 = 0x12,
    Const16 = 0x13,
    Const = 0x14,
    ConstHigh16 = 0x15,
    ConstWide16 = 0x16,
    ConstWide32 = 0x17,
    ConstWide = 0x18,
    ConstWideHigh16 = 0x19,
    ConstString = 0x1a,
    ConstStringJumbo = 0x1b,
    ConstClass = 0x1c,

    // Monitor
    MonitorEnter = 0x1d,
    MonitorExit = 0x1e,

    // Type checking
    CheckCast = 0x1f,
    InstanceOf = 0x20,

    // Array operations
    ArrayLength = 0x21,
    NewInstance = 0x22,
    NewArray = 0x23,
    FilledNewArray = 0x24,
    FilledNewArrayRange = 0x25,
    FillArrayData = 0x26,

    // Exception handling
    Throw = 0x27,
    Goto = 0x28,
    Goto16 = 0x29,
    Goto32 = 0x2a,
    PackedSwitch = 0x2b,
    SparseSwitch = 0x2c,

    // Comparison
    CmplFloat = 0x2d,
    CmpgFloat = 0x2e,
    CmplDouble = 0x2f,
    CmpgDouble = 0x30,
    CmpLong = 0x31,

    // Conditional branches
    IfEq = 0x32,
    IfNe = 0x33,
    IfLt = 0x34,
    IfGe = 0x35,
    IfGt = 0x36,
    IfLe = 0x37,
    IfEqz = 0x38,
    IfNez = 0x39,
    IfLtz = 0x3a,
    IfGez = 0x3b,
    IfGtz = 0x3c,
    IfLez = 0x3d,

    // Array operations (continued)
    Aget = 0x44,
    AgetWide = 0x45,
    AgetObject = 0x46,
    AgetBoolean = 0x47,
    AgetByte = 0x48,
    AgetChar = 0x49,
    AgetShort = 0x4a,
    Aput = 0x4b,
    AputWide = 0x4c,
    AputObject = 0x4d,
    AputBoolean = 0x4e,
    AputByte = 0x4f,
    AputChar = 0x50,
    AputShort = 0x51,

    // Instance field operations
    Iget = 0x52,
    IgetWide = 0x53,
    IgetObject = 0x54,
    IgetBoolean = 0x55,
    IgetByte = 0x56,
    IgetChar = 0x57,
    IgetShort = 0x58,
    Iput = 0x59,
    IputWide = 0x5a,
    IputObject = 0x5b,
    IputBoolean = 0x5c,
    IputByte = 0x5d,
    IputChar = 0x5e,
    IputShort = 0x5f,

    // Static field operations
    Sget = 0x60,
    SgetWide = 0x61,
    SgetObject = 0x62,
    SgetBoolean = 0x63,
    SgetByte = 0x64,
    SgetChar = 0x65,
    SgetShort = 0x66,
    Sput = 0x67,
    SputWide = 0x68,
    SputObject = 0x69,
    SputBoolean = 0x6a,
    SputByte = 0x6b,
    SputChar = 0x6c,
    SputShort = 0x6d,

    // Method invocation
    InvokeVirtual = 0x6e,
    InvokeSuper = 0x6f,
    InvokeDirect = 0x70,
    InvokeStatic = 0x71,
    InvokeInterface = 0x72,

    InvokeVirtualRange = 0x74,
    InvokeSuperRange = 0x75,
    InvokeDirectRange = 0x76,
    InvokeStaticRange = 0x77,
    InvokeInterfaceRange = 0x78,

    // Unary operations
    NegInt = 0x7b,
    NotInt = 0x7c,
    NegLong = 0x7d,
    NotLong = 0x7e,
    NegFloat = 0x7f,
    NegDouble = 0x80,
    IntToLong = 0x81,
    IntToFloat = 0x82,
    IntToDouble = 0x83,
    LongToInt = 0x84,
    LongToFloat = 0x85,
    LongToDouble = 0x86,
    FloatToInt = 0x87,
    FloatToLong = 0x88,
    FloatToDouble = 0x89,
    DoubleToInt = 0x8a,
    DoubleToLong = 0x8b,
    DoubleToFloat = 0x8c,
    IntToByte = 0x8d,
    IntToChar = 0x8e,
    IntToShort = 0x8f,

    // Binary operations
    AddInt = 0x90,
    SubInt = 0x91,
    MulInt = 0x92,
    DivInt = 0x93,
    RemInt = 0x94,
    AndInt = 0x95,
    OrInt = 0x96,
    XorInt = 0x97,
    ShlInt = 0x98,
    ShrInt = 0x99,
    UshrInt = 0x9a,

    AddLong = 0x9b,
    SubLong = 0x9c,
    MulLong = 0x9d,
    DivLong = 0x9e,
    RemLong = 0x9f,
    AndLong = 0xa0,
    OrLong = 0xa1,
    XorLong = 0xa2,
    ShlLong = 0xa3,
    ShrLong = 0xa4,
    UshrLong = 0xa5,

    AddFloat = 0xa6,
    SubFloat = 0xa7,
    MulFloat = 0xa8,
    DivFloat = 0xa9,
    RemFloat = 0xaa,
    AddDouble = 0xab,
    SubDouble = 0xac,
    MulDouble = 0xad,
    DivDouble = 0xae,
    RemDouble = 0xaf,

    // Binary operations (2addr variants)
    AddInt2addr = 0xb0,
    SubInt2addr = 0xb1,
    MulInt2addr = 0xb2,
    DivInt2addr = 0xb3,
    RemInt2addr = 0xb4,
    AndInt2addr = 0xb5,
    OrInt2addr = 0xb6,
    XorInt2addr = 0xb7,
    ShlInt2addr = 0xb8,
    ShrInt2addr = 0xb9,
    UshrInt2addr = 0xba,

    AddLong2addr = 0xbb,
    SubLong2addr = 0xbc,
    MulLong2addr = 0xbd,
    DivLong2addr = 0xbe,
    RemLong2addr = 0xbf,
    AndLong2addr = 0xc0,
    OrLong2addr = 0xc1,
    XorLong2addr = 0xc2,
    ShlLong2addr = 0xc3,
    ShrLong2addr = 0xc4,
    UshrLong2addr = 0xc5,

    AddFloat2addr = 0xc6,
    SubFloat2addr = 0xc7,
    MulFloat2addr = 0xc8,
    DivFloat2addr = 0xc9,
    RemFloat2addr = 0xca,
    AddDouble2addr = 0xcb,
    SubDouble2addr = 0xcc,
    MulDouble2addr = 0xcd,
    DivDouble2addr = 0xce,
    RemDouble2addr = 0xcf,

    // Binary operations (lit16 and lit8 variants)
    AddIntLit16 = 0xd0,
    RsubInt = 0xd1,
    MulIntLit16 = 0xd2,
    DivIntLit16 = 0xd3,
    RemIntLit16 = 0xd4,
    AndIntLit16 = 0xd5,
    OrIntLit16 = 0xd6,
    XorIntLit16 = 0xd7,

    AddIntLit8 = 0xd8,
    RsubIntLit8 = 0xd9,
    MulIntLit8 = 0xda,
    DivIntLit8 = 0xdb,
    RemIntLit8 = 0xdc,
    AndIntLit8 = 0xdd,
    OrIntLit8 = 0xde,
    XorIntLit8 = 0xdf,
    ShlIntLit8 = 0xe0,
    ShrIntLit8 = 0xe1,
    UshrIntLit8 = 0xe2,

    Unknown = 0xff,
}

impl Opcode {
    /// Create opcode from byte value
    pub fn from_u8(value: u8) -> Self {
        match value {
            0x00 => Opcode::Nop,
            0x01 => Opcode::Move,
            0x02 => Opcode::MoveFrom16,
            0x03 => Opcode::Move16,
            0x04 => Opcode::MoveWide,
            0x05 => Opcode::MoveWideFrom16,
            0x06 => Opcode::MoveWide16,
            0x07 => Opcode::MoveObject,
            0x08 => Opcode::MoveObjectFrom16,
            0x09 => Opcode::MoveObject16,
            0x0a => Opcode::MoveResult,
            0x0b => Opcode::MoveResultWide,
            0x0c => Opcode::MoveResultObject,
            0x0d => Opcode::MoveException,
            0x0e => Opcode::ReturnVoid,
            0x0f => Opcode::Return,
            0x10 => Opcode::ReturnWide,
            0x11 => Opcode::ReturnObject,
            0x12 => Opcode::Const4,
            0x13 => Opcode::Const16,
            0x14 => Opcode::Const,
            0x15 => Opcode::ConstHigh16,
            0x16 => Opcode::ConstWide16,
            0x17 => Opcode::ConstWide32,
            0x18 => Opcode::ConstWide,
            0x19 => Opcode::ConstWideHigh16,
            0x1a => Opcode::ConstString,
            0x1b => Opcode::ConstStringJumbo,
            0x1c => Opcode::ConstClass,
            0x1d => Opcode::MonitorEnter,
            0x1e => Opcode::MonitorExit,
            0x1f => Opcode::CheckCast,
            0x20 => Opcode::InstanceOf,
            0x21 => Opcode::ArrayLength,
            0x22 => Opcode::NewInstance,
            0x23 => Opcode::NewArray,
            0x24 => Opcode::FilledNewArray,
            0x25 => Opcode::FilledNewArrayRange,
            0x26 => Opcode::FillArrayData,
            0x27 => Opcode::Throw,
            0x28 => Opcode::Goto,
            0x29 => Opcode::Goto16,
            0x2a => Opcode::Goto32,
            0x2b => Opcode::PackedSwitch,
            0x2c => Opcode::SparseSwitch,
            0x2d => Opcode::CmplFloat,
            0x2e => Opcode::CmpgFloat,
            0x2f => Opcode::CmplDouble,
            0x30 => Opcode::CmpgDouble,
            0x31 => Opcode::CmpLong,
            0x32 => Opcode::IfEq,
            0x33 => Opcode::IfNe,
            0x34 => Opcode::IfLt,
            0x35 => Opcode::IfGe,
            0x36 => Opcode::IfGt,
            0x37 => Opcode::IfLe,
            0x38 => Opcode::IfEqz,
            0x39 => Opcode::IfNez,
            0x3a => Opcode::IfLtz,
            0x3b => Opcode::IfGez,
            0x3c => Opcode::IfGtz,
            0x3d => Opcode::IfLez,
            0x44 => Opcode::Aget,
            0x45 => Opcode::AgetWide,
            0x46 => Opcode::AgetObject,
            0x47 => Opcode::AgetBoolean,
            0x48 => Opcode::AgetByte,
            0x49 => Opcode::AgetChar,
            0x4a => Opcode::AgetShort,
            0x4b => Opcode::Aput,
            0x4c => Opcode::AputWide,
            0x4d => Opcode::AputObject,
            0x4e => Opcode::AputBoolean,
            0x4f => Opcode::AputByte,
            0x50 => Opcode::AputChar,
            0x51 => Opcode::AputShort,
            0x52 => Opcode::Iget,
            0x53 => Opcode::IgetWide,
            0x54 => Opcode::IgetObject,
            0x55 => Opcode::IgetBoolean,
            0x56 => Opcode::IgetByte,
            0x57 => Opcode::IgetChar,
            0x58 => Opcode::IgetShort,
            0x59 => Opcode::Iput,
            0x5a => Opcode::IputWide,
            0x5b => Opcode::IputObject,
            0x5c => Opcode::IputBoolean,
            0x5d => Opcode::IputByte,
            0x5e => Opcode::IputChar,
            0x5f => Opcode::IputShort,
            0x60 => Opcode::Sget,
            0x61 => Opcode::SgetWide,
            0x62 => Opcode::SgetObject,
            0x63 => Opcode::SgetBoolean,
            0x64 => Opcode::SgetByte,
            0x65 => Opcode::SgetChar,
            0x66 => Opcode::SgetShort,
            0x67 => Opcode::Sput,
            0x68 => Opcode::SputWide,
            0x69 => Opcode::SputObject,
            0x6a => Opcode::SputBoolean,
            0x6b => Opcode::SputByte,
            0x6c => Opcode::SputChar,
            0x6d => Opcode::SputShort,
            0x6e => Opcode::InvokeVirtual,
            0x6f => Opcode::InvokeSuper,
            0x70 => Opcode::InvokeDirect,
            0x71 => Opcode::InvokeStatic,
            0x72 => Opcode::InvokeInterface,
            0x74 => Opcode::InvokeVirtualRange,
            0x75 => Opcode::InvokeSuperRange,
            0x76 => Opcode::InvokeDirectRange,
            0x77 => Opcode::InvokeStaticRange,
            0x78 => Opcode::InvokeInterfaceRange,
            0x7b => Opcode::NegInt,
            0x7c => Opcode::NotInt,
            0x7d => Opcode::NegLong,
            0x7e => Opcode::NotLong,
            0x7f => Opcode::NegFloat,
            0x80 => Opcode::NegDouble,
            0x81 => Opcode::IntToLong,
            0x82 => Opcode::IntToFloat,
            0x83 => Opcode::IntToDouble,
            0x84 => Opcode::LongToInt,
            0x85 => Opcode::LongToFloat,
            0x86 => Opcode::LongToDouble,
            0x87 => Opcode::FloatToInt,
            0x88 => Opcode::FloatToLong,
            0x89 => Opcode::FloatToDouble,
            0x8a => Opcode::DoubleToInt,
            0x8b => Opcode::DoubleToLong,
            0x8c => Opcode::DoubleToFloat,
            0x8d => Opcode::IntToByte,
            0x8e => Opcode::IntToChar,
            0x8f => Opcode::IntToShort,
            0x90..=0xe2 => {
                // Binary operations - mapped individually above
                match value {
                    0x90 => Opcode::AddInt,
                    0x91 => Opcode::SubInt,
                    0x92 => Opcode::MulInt,
                    0x93 => Opcode::DivInt,
                    0x94 => Opcode::RemInt,
                    0x95 => Opcode::AndInt,
                    0x96 => Opcode::OrInt,
                    0x97 => Opcode::XorInt,
                    0x98 => Opcode::ShlInt,
                    0x99 => Opcode::ShrInt,
                    0x9a => Opcode::UshrInt,
                    0x9b => Opcode::AddLong,
                    0x9c => Opcode::SubLong,
                    0x9d => Opcode::MulLong,
                    0x9e => Opcode::DivLong,
                    0x9f => Opcode::RemLong,
                    0xa0 => Opcode::AndLong,
                    0xa1 => Opcode::OrLong,
                    0xa2 => Opcode::XorLong,
                    0xa3 => Opcode::ShlLong,
                    0xa4 => Opcode::ShrLong,
                    0xa5 => Opcode::UshrLong,
                    0xa6 => Opcode::AddFloat,
                    0xa7 => Opcode::SubFloat,
                    0xa8 => Opcode::MulFloat,
                    0xa9 => Opcode::DivFloat,
                    0xaa => Opcode::RemFloat,
                    0xab => Opcode::AddDouble,
                    0xac => Opcode::SubDouble,
                    0xad => Opcode::MulDouble,
                    0xae => Opcode::DivDouble,
                    0xaf => Opcode::RemDouble,
                    0xb0 => Opcode::AddInt2addr,
                    0xb1 => Opcode::SubInt2addr,
                    0xb2 => Opcode::MulInt2addr,
                    0xb3 => Opcode::DivInt2addr,
                    0xb4 => Opcode::RemInt2addr,
                    0xb5 => Opcode::AndInt2addr,
                    0xb6 => Opcode::OrInt2addr,
                    0xb7 => Opcode::XorInt2addr,
                    0xb8 => Opcode::ShlInt2addr,
                    0xb9 => Opcode::ShrInt2addr,
                    0xba => Opcode::UshrInt2addr,
                    0xbb => Opcode::AddLong2addr,
                    0xbc => Opcode::SubLong2addr,
                    0xbd => Opcode::MulLong2addr,
                    0xbe => Opcode::DivLong2addr,
                    0xbf => Opcode::RemLong2addr,
                    0xc0 => Opcode::AndLong2addr,
                    0xc1 => Opcode::OrLong2addr,
                    0xc2 => Opcode::XorLong2addr,
                    0xc3 => Opcode::ShlLong2addr,
                    0xc4 => Opcode::ShrLong2addr,
                    0xc5 => Opcode::UshrLong2addr,
                    0xc6 => Opcode::AddFloat2addr,
                    0xc7 => Opcode::SubFloat2addr,
                    0xc8 => Opcode::MulFloat2addr,
                    0xc9 => Opcode::DivFloat2addr,
                    0xca => Opcode::RemFloat2addr,
                    0xcb => Opcode::AddDouble2addr,
                    0xcc => Opcode::SubDouble2addr,
                    0xcd => Opcode::MulDouble2addr,
                    0xce => Opcode::DivDouble2addr,
                    0xcf => Opcode::RemDouble2addr,
                    0xd0 => Opcode::AddIntLit16,
                    0xd1 => Opcode::RsubInt,
                    0xd2 => Opcode::MulIntLit16,
                    0xd3 => Opcode::DivIntLit16,
                    0xd4 => Opcode::RemIntLit16,
                    0xd5 => Opcode::AndIntLit16,
                    0xd6 => Opcode::OrIntLit16,
                    0xd7 => Opcode::XorIntLit16,
                    0xd8 => Opcode::AddIntLit8,
                    0xd9 => Opcode::RsubIntLit8,
                    0xda => Opcode::MulIntLit8,
                    0xdb => Opcode::DivIntLit8,
                    0xdc => Opcode::RemIntLit8,
                    0xdd => Opcode::AndIntLit8,
                    0xde => Opcode::OrIntLit8,
                    0xdf => Opcode::XorIntLit8,
                    0xe0 => Opcode::ShlIntLit8,
                    0xe1 => Opcode::ShrIntLit8,
                    0xe2 => Opcode::UshrIntLit8,
                    _ => Opcode::Unknown,
                }
            }
            _ => Opcode::Unknown,
        }
    }
}

/// Decoded Dalvik instruction
#[derive(Debug, Clone)]
#[cfg_attr(feature = "python", pyo3::pyclass)]
pub enum Instruction {
    /// const/4 vA, #+B
    Const4 { dest: u8, value: i8 },

    /// const/16 vAA, #+BBBB
    Const16 { dest: u8, value: i16 },

    /// const vAA, #+BBBBBBBB
    Const { dest: u8, value: i32 },

    /// const-string vAA, string@BBBB
    ConstString { dest: u8, string_idx: u32 },

    /// invoke-virtual {vC, vD, vE, vF, vG}, meth@BBBB
    InvokeVirtual { args: Vec<u8>, method_idx: u32 },

    /// invoke-super {vC, vD, vE, vF, vG}, meth@BBBB
    InvokeSuper { args: Vec<u8>, method_idx: u32 },

    /// invoke-direct {vC, vD, vE, vF, vG}, meth@BBBB
    InvokeDirect { args: Vec<u8>, method_idx: u32 },

    /// invoke-static {vC, vD, vE, vF, vG}, meth@BBBB
    InvokeStatic { args: Vec<u8>, method_idx: u32 },

    /// invoke-interface {vC, vD, vE, vF, vG}, meth@BBBB
    InvokeInterface { args: Vec<u8>, method_idx: u32 },

    /// invoke-virtual/range {vCCCC .. vNNNN}, meth@BBBB
    InvokeVirtualRange { first_arg: u16, arg_count: u8, method_idx: u32 },

    /// invoke-static/range {vCCCC .. vNNNN}, meth@BBBB
    InvokeStaticRange { first_arg: u16, arg_count: u8, method_idx: u32 },

    /// Unknown or unimplemented instruction
    Unknown { opcode: u8, data: Vec<u16> },
}

impl fmt::Display for Instruction {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Instruction::Const4 { dest, value } => {
                write!(f, "const/4 v{}, #{}", dest, value)
            }
            Instruction::Const16 { dest, value } => {
                write!(f, "const/16 v{}, #{}", dest, value)
            }
            Instruction::Const { dest, value } => {
                write!(f, "const v{}, #{}", dest, value)
            }
            Instruction::ConstString { dest, string_idx } => {
                write!(f, "const-string v{}, string@{}", dest, string_idx)
            }
            Instruction::InvokeVirtual { args, method_idx } => {
                write!(f, "invoke-virtual {{v{}}}, method@{}",
                    args.iter().map(|a| a.to_string()).collect::<Vec<_>>().join(", v"),
                    method_idx)
            }
            Instruction::InvokeStatic { args, method_idx } => {
                write!(f, "invoke-static {{v{}}}, method@{}",
                    args.iter().map(|a| a.to_string()).collect::<Vec<_>>().join(", v"),
                    method_idx)
            }
            Instruction::InvokeDirect { args, method_idx } => {
                write!(f, "invoke-direct {{v{}}}, method@{}",
                    args.iter().map(|a| a.to_string()).collect::<Vec<_>>().join(", v"),
                    method_idx)
            }
            Instruction::InvokeSuper { args, method_idx } => {
                write!(f, "invoke-super {{v{}}}, method@{}",
                    args.iter().map(|a| a.to_string()).collect::<Vec<_>>().join(", v"),
                    method_idx)
            }
            Instruction::InvokeInterface { args, method_idx } => {
                write!(f, "invoke-interface {{v{}}}, method@{}",
                    args.iter().map(|a| a.to_string()).collect::<Vec<_>>().join(", v"),
                    method_idx)
            }
            Instruction::InvokeVirtualRange { first_arg, arg_count, method_idx } => {
                write!(f, "invoke-virtual/range {{v{} .. v{}}}, method@{}",
                    first_arg, first_arg + *arg_count as u16 - 1, method_idx)
            }
            Instruction::InvokeStaticRange { first_arg, arg_count, method_idx } => {
                write!(f, "invoke-static/range {{v{} .. v{}}}, method@{}",
                    first_arg, first_arg + *arg_count as u16 - 1, method_idx)
            }
            Instruction::Unknown { opcode, .. } => {
                write!(f, "unknown (opcode: 0x{:02x})", opcode)
            }
        }
    }
}

/// Decode Dalvik bytecode instructions
pub struct InstructionDecoder;

impl InstructionDecoder {
    /// Decode instructions from bytecode
    pub fn decode(bytecode: &[u16]) -> Vec<Instruction> {
        let mut instructions = Vec::new();
        let mut i = 0;

        while i < bytecode.len() {
            let word = bytecode[i];
            let opcode_byte = (word & 0xFF) as u8;
            let opcode = Opcode::from_u8(opcode_byte);

            let instruction = match opcode {
                // const/4 vA, #+B
                // Format: |B|A|op where op=0x12, A=dest (low nibble of high byte), B=value (high nibble of high byte)
                Opcode::Const4 => {
                    let dest = ((word >> 8) & 0xF) as u8;  // Low nibble of high byte
                    let value_bits = ((word >> 12) & 0xF) as u8;  // High nibble of high byte
                    // Sign extend 4-bit value to 8-bit
                    let value = if value_bits & 0x8 != 0 {
                        // Negative: extend with 1s
                        (value_bits | 0xF0u8) as i8
                    } else {
                        // Positive: just cast
                        value_bits as i8
                    };
                    i += 1;
                    Instruction::Const4 { dest, value }
                }

                // const/16 vAA, #+BBBB
                Opcode::Const16 => {
                    let dest = (word >> 8) as u8;
                    let value = if i + 1 < bytecode.len() {
                        bytecode[i + 1] as i16
                    } else {
                        0
                    };
                    i += 2;
                    Instruction::Const16 { dest, value }
                }

                // const vAA, #+BBBBBBBB
                Opcode::Const => {
                    let dest = (word >> 8) as u8;
                    let value = if i + 2 < bytecode.len() {
                        let low = bytecode[i + 1] as u32;
                        let high = bytecode[i + 2] as u32;
                        ((high << 16) | low) as i32
                    } else {
                        0
                    };
                    i += 3;
                    Instruction::Const { dest, value }
                }

                // const-string vAA, string@BBBB
                Opcode::ConstString => {
                    let dest = (word >> 8) as u8;
                    let string_idx = if i + 1 < bytecode.len() {
                        bytecode[i + 1] as u32
                    } else {
                        0
                    };
                    i += 2;
                    Instruction::ConstString { dest, string_idx }
                }

                // invoke-virtual {vC, vD, vE, vF, vG}, meth@BBBB
                Opcode::InvokeVirtual => {
                    let arg_count = ((word >> 12) & 0xF) as u8;
                    let method_idx = if i + 1 < bytecode.len() {
                        bytecode[i + 1] as u32
                    } else {
                        0
                    };
                    let args_word = if i + 2 < bytecode.len() {
                        bytecode[i + 2]
                    } else {
                        0
                    };

                    let mut args = Vec::new();
                    for j in 0..arg_count {
                        let arg = if j == 0 {
                            ((word >> 8) & 0xF) as u8
                        } else if j <= 4 {
                            ((args_word >> ((j - 1) * 4)) & 0xF) as u8
                        } else {
                            0
                        };
                        args.push(arg);
                    }
                    i += 3;
                    Instruction::InvokeVirtual { args, method_idx }
                }

                // invoke-static {vC, vD, vE, vF, vG}, meth@BBBB
                Opcode::InvokeStatic => {
                    let arg_count = ((word >> 12) & 0xF) as u8;
                    let method_idx = if i + 1 < bytecode.len() {
                        bytecode[i + 1] as u32
                    } else {
                        0
                    };
                    let args_word = if i + 2 < bytecode.len() {
                        bytecode[i + 2]
                    } else {
                        0
                    };

                    let mut args = Vec::new();
                    for j in 0..arg_count {
                        let arg = if j == 0 {
                            ((word >> 8) & 0xF) as u8
                        } else if j <= 4 {
                            ((args_word >> ((j - 1) * 4)) & 0xF) as u8
                        } else {
                            0
                        };
                        args.push(arg);
                    }
                    i += 3;
                    Instruction::InvokeStatic { args, method_idx }
                }

                // invoke-direct {vC, vD, vE, vF, vG}, meth@BBBB
                Opcode::InvokeDirect => {
                    let arg_count = ((word >> 12) & 0xF) as u8;
                    let method_idx = if i + 1 < bytecode.len() {
                        bytecode[i + 1] as u32
                    } else {
                        0
                    };
                    let args_word = if i + 2 < bytecode.len() {
                        bytecode[i + 2]
                    } else {
                        0
                    };

                    let mut args = Vec::new();
                    for j in 0..arg_count {
                        let arg = if j == 0 {
                            ((word >> 8) & 0xF) as u8
                        } else if j <= 4 {
                            ((args_word >> ((j - 1) * 4)) & 0xF) as u8
                        } else {
                            0
                        };
                        args.push(arg);
                    }
                    i += 3;
                    Instruction::InvokeDirect { args, method_idx }
                }

                // invoke-super {vC, vD, vE, vF, vG}, meth@BBBB
                Opcode::InvokeSuper => {
                    let arg_count = ((word >> 12) & 0xF) as u8;
                    let method_idx = if i + 1 < bytecode.len() {
                        bytecode[i + 1] as u32
                    } else {
                        0
                    };
                    let args_word = if i + 2 < bytecode.len() {
                        bytecode[i + 2]
                    } else {
                        0
                    };

                    let mut args = Vec::new();
                    for j in 0..arg_count {
                        let arg = if j == 0 {
                            ((word >> 8) & 0xF) as u8
                        } else if j <= 4 {
                            ((args_word >> ((j - 1) * 4)) & 0xF) as u8
                        } else {
                            0
                        };
                        args.push(arg);
                    }
                    i += 3;
                    Instruction::InvokeSuper { args, method_idx }
                }

                // invoke-interface {vC, vD, vE, vF, vG}, meth@BBBB
                Opcode::InvokeInterface => {
                    let arg_count = ((word >> 12) & 0xF) as u8;
                    let method_idx = if i + 1 < bytecode.len() {
                        bytecode[i + 1] as u32
                    } else {
                        0
                    };
                    let args_word = if i + 2 < bytecode.len() {
                        bytecode[i + 2]
                    } else {
                        0
                    };

                    let mut args = Vec::new();
                    for j in 0..arg_count {
                        let arg = if j == 0 {
                            ((word >> 8) & 0xF) as u8
                        } else if j <= 4 {
                            ((args_word >> ((j - 1) * 4)) & 0xF) as u8
                        } else {
                            0
                        };
                        args.push(arg);
                    }
                    i += 3;
                    Instruction::InvokeInterface { args, method_idx }
                }

                // invoke-virtual/range {vCCCC .. vNNNN}, meth@BBBB
                Opcode::InvokeVirtualRange => {
                    let arg_count = (word >> 8) as u8;
                    let method_idx = if i + 1 < bytecode.len() {
                        bytecode[i + 1] as u32
                    } else {
                        0
                    };
                    let first_arg = if i + 2 < bytecode.len() {
                        bytecode[i + 2]
                    } else {
                        0
                    };
                    i += 3;
                    Instruction::InvokeVirtualRange { first_arg, arg_count, method_idx }
                }

                // invoke-static/range {vCCCC .. vNNNN}, meth@BBBB
                Opcode::InvokeStaticRange => {
                    let arg_count = (word >> 8) as u8;
                    let method_idx = if i + 1 < bytecode.len() {
                        bytecode[i + 1] as u32
                    } else {
                        0
                    };
                    let first_arg = if i + 2 < bytecode.len() {
                        bytecode[i + 2]
                    } else {
                        0
                    };
                    i += 3;
                    Instruction::InvokeStaticRange { first_arg, arg_count, method_idx }
                }

                // Unknown instruction - skip
                _ => {
                    let data = vec![word];
                    i += 1;
                    Instruction::Unknown { opcode: opcode_byte, data }
                }
            };

            instructions.push(instruction);
        }

        instructions
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_const4_decode() {
        // const/4 v0, #1
        let bytecode = vec![0x1201];  // opcode=0x12, dest=0, value=1
        let instructions = InstructionDecoder::decode(&bytecode);

        assert_eq!(instructions.len(), 1);
        match &instructions[0] {
            Instruction::Const4 { dest, value } => {
                assert_eq!(*dest, 0);
                assert_eq!(*value, 1);
            }
            _ => panic!("Expected Const4 instruction"),
        }
    }

    #[test]
    fn test_const4_negative() {
        // const/4 v0, #-1
        let bytecode = vec![0xF201];  // opcode=0x12, dest=0, value=-1 (0xF)
        let instructions = InstructionDecoder::decode(&bytecode);

        assert_eq!(instructions.len(), 1);
        match &instructions[0] {
            Instruction::Const4 { dest, value } => {
                assert_eq!(*dest, 0);
                assert_eq!(*value, -1);
            }
            _ => panic!("Expected Const4 instruction"),
        }
    }
}
