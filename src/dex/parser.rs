use crate::dex::error::{DexError, Result};
use crate::dex::constants::{dex_magic, structure, type_descriptors};
use byteorder::{LittleEndian, ReadBytesExt};
use std::io::{Cursor, Read, Seek, SeekFrom};

/// DEX file header structure
/// Reference: https://source.android.com/docs/core/runtime/dex-format
#[derive(Debug, Clone)]
pub struct DexHeader {
    pub magic: [u8; 4],
    pub version: [u8; 4],
    pub checksum: u32,
    pub signature: [u8; 20],
    pub file_size: u32,
    pub header_size: u32,
    pub endian_tag: u32,
    pub link_size: u32,
    pub link_off: u32,
    pub map_off: u32,
    pub string_ids_size: u32,
    pub string_ids_off: u32,
    pub type_ids_size: u32,
    pub type_ids_off: u32,
    pub proto_ids_size: u32,
    pub proto_ids_off: u32,
    pub field_ids_size: u32,
    pub field_ids_off: u32,
    pub method_ids_size: u32,
    pub method_ids_off: u32,
    pub class_defs_size: u32,
    pub class_defs_off: u32,
    pub data_size: u32,
    pub data_off: u32,
}

/// Simple DEX parser
pub struct DexParser {
    data: Vec<u8>,
    header: DexHeader,
}

impl DexParser {
    /// Create a new DEX parser from raw bytes
    pub fn new(data: Vec<u8>) -> Result<Self> {
        let header = Self::parse_header(&data)?;

        Ok(Self { data, header })
    }

    /// Parse the DEX file header
    fn parse_header(data: &[u8]) -> Result<DexHeader> {
        if data.len() < 112 {
            return Err(DexError::InvalidDex("File too small".to_string()));
        }

        let mut cursor = Cursor::new(data);

        // Read magic
        let mut magic = [0u8; 4];
        cursor.read_exact(&mut magic)?;
        if &magic != dex_magic::MAGIC {
            return Err(DexError::InvalidDex(format!(
                "Invalid magic: {:?}",
                magic
            )));
        }

        // Read version
        let mut version = [0u8; 4];
        cursor.read_exact(&mut version)?;

        // Validate version
        if !dex_magic::is_supported_version(&version) {
            eprintln!("Warning: DEX version {:?} may not be fully supported",
                     String::from_utf8_lossy(&version));
        }

        // Read checksum
        let checksum = cursor.read_u32::<LittleEndian>()?;

        // Read SHA-1 signature
        let mut signature = [0u8; 20];
        cursor.read_exact(&mut signature)?;

        // Read file size
        let file_size = cursor.read_u32::<LittleEndian>()?;

        // Read header size (should be 0x70 = 112)
        let header_size = cursor.read_u32::<LittleEndian>()?;
        if header_size != structure::HEADER_SIZE {
            return Err(DexError::InvalidDex(format!(
                "Invalid header size: {} (expected {})",
                header_size,
                structure::HEADER_SIZE
            )));
        }

        // Read endian tag
        let endian_tag = cursor.read_u32::<LittleEndian>()?;

        // Read link section
        let link_size = cursor.read_u32::<LittleEndian>()?;
        let link_off = cursor.read_u32::<LittleEndian>()?;

        // Read map offset
        let map_off = cursor.read_u32::<LittleEndian>()?;

        // Read string IDs
        let string_ids_size = cursor.read_u32::<LittleEndian>()?;
        let string_ids_off = cursor.read_u32::<LittleEndian>()?;

        // Read type IDs
        let type_ids_size = cursor.read_u32::<LittleEndian>()?;
        let type_ids_off = cursor.read_u32::<LittleEndian>()?;

        // Read proto IDs
        let proto_ids_size = cursor.read_u32::<LittleEndian>()?;
        let proto_ids_off = cursor.read_u32::<LittleEndian>()?;

        // Read field IDs
        let field_ids_size = cursor.read_u32::<LittleEndian>()?;
        let field_ids_off = cursor.read_u32::<LittleEndian>()?;

        // Read method IDs
        let method_ids_size = cursor.read_u32::<LittleEndian>()?;
        let method_ids_off = cursor.read_u32::<LittleEndian>()?;

        // Read class definitions
        let class_defs_size = cursor.read_u32::<LittleEndian>()?;
        let class_defs_off = cursor.read_u32::<LittleEndian>()?;

        // Read data section
        let data_size = cursor.read_u32::<LittleEndian>()?;
        let data_off = cursor.read_u32::<LittleEndian>()?;

        Ok(DexHeader {
            magic,
            version,
            checksum,
            signature,
            file_size,
            header_size,
            endian_tag,
            link_size,
            link_off,
            map_off,
            string_ids_size,
            string_ids_off,
            type_ids_size,
            type_ids_off,
            proto_ids_size,
            proto_ids_off,
            field_ids_size,
            field_ids_off,
            method_ids_size,
            method_ids_off,
            class_defs_size,
            class_defs_off,
            data_size,
            data_off,
        })
    }

    /// Get header
    pub fn header(&self) -> &DexHeader {
        &self.header
    }

    /// Read a string from the string pool
    pub fn get_string(&self, string_idx: u32) -> Result<String> {
        if string_idx >= self.header.string_ids_size {
            return Err(DexError::ParseError(format!(
                "String index {} out of bounds",
                string_idx
            )));
        }

        // Get string data offset from string_ids table
        let string_id_offset = self.header.string_ids_off as usize + (string_idx as usize * structure::STRING_ID_SIZE);
        let mut cursor = Cursor::new(&self.data);
        cursor.seek(SeekFrom::Start(string_id_offset as u64))?;
        let string_data_off = cursor.read_u32::<LittleEndian>()? as usize;

        // Read the string data (MUTF-8 format)
        cursor.seek(SeekFrom::Start(string_data_off as u64))?;

        // Read ULEB128 string length
        let _length = self.read_uleb128(&mut cursor)?;

        // Read MUTF-8 string
        let mut bytes = Vec::new();
        loop {
            let b = cursor.read_u8()?;
            if b == 0 {
                break;
            }
            bytes.push(b);
        }

        // Convert MUTF-8 to UTF-8 (simplified - works for most cases)
        String::from_utf8(bytes).map_err(|e| DexError::ParseError(format!("Invalid UTF-8: {}", e)))
    }

    /// Read ULEB128 (unsigned little-endian base 128)
    fn read_uleb128(&self, cursor: &mut Cursor<&Vec<u8>>) -> Result<u32> {
        let mut result = 0u32;
        let mut shift = 0;

        loop {
            let byte = cursor.read_u8()?;
            result |= ((byte & 0x7F) as u32) << shift;

            if (byte & 0x80) == 0 {
                break;
            }

            shift += 7;
            if shift >= 35 {
                return Err(DexError::ParseError("ULEB128 overflow".to_string()));
            }
        }

        Ok(result)
    }

    /// Get type name by type ID
    pub fn get_type_name(&self, type_idx: u32) -> Result<String> {
        if type_idx >= self.header.type_ids_size {
            return Err(DexError::ParseError(format!(
                "Type index {} out of bounds",
                type_idx
            )));
        }

        // Get string index from type_ids table
        let type_id_offset = self.header.type_ids_off as usize + (type_idx as usize * structure::TYPE_ID_SIZE);
        let mut cursor = Cursor::new(&self.data);
        cursor.seek(SeekFrom::Start(type_id_offset as u64))?;
        let descriptor_idx = cursor.read_u32::<LittleEndian>()?;

        // Get the type descriptor string
        let descriptor = self.get_string(descriptor_idx)?;

        // Convert descriptor to Java type (e.g., "Ljava/lang/String;" -> "java.lang.String")
        Ok(self.descriptor_to_java_type(&descriptor))
    }

    /// Convert type descriptor to Java type name
    fn descriptor_to_java_type(&self, descriptor: &str) -> String {
        if descriptor.is_empty() {
            return "void".to_string();
        }

        let first_char = descriptor.chars().next().unwrap();

        match first_char {
            type_descriptors::VOID => "void".to_string(),
            type_descriptors::BOOLEAN => "boolean".to_string(),
            type_descriptors::BYTE => "byte".to_string(),
            type_descriptors::SHORT => "short".to_string(),
            type_descriptors::CHAR => "char".to_string(),
            type_descriptors::INT => "int".to_string(),
            type_descriptors::LONG => "long".to_string(),
            type_descriptors::FLOAT => "float".to_string(),
            type_descriptors::DOUBLE => "double".to_string(),
            type_descriptors::OBJECT => {
                // Class type: Ljava/lang/String; -> java.lang.String
                let without_l = &descriptor[1..];
                let without_semicolon = without_l.trim_end_matches(';');
                without_semicolon.replace('/', ".")
            }
            type_descriptors::ARRAY => {
                // Array type: [I -> int[], [[Ljava/lang/String; -> java.lang.String[][]
                let mut array_depth = 0;
                let mut chars = descriptor.chars();
                while let Some(type_descriptors::ARRAY) = chars.next() {
                    array_depth += 1;
                }
                let base_descriptor = &descriptor[array_depth..];
                let base_type = self.descriptor_to_java_type(base_descriptor);
                format!("{}{}", base_type, "[]".repeat(array_depth))
            }
            _ => {
                // Unknown type, return as-is
                eprintln!("Warning: Unknown type descriptor: {}", descriptor);
                descriptor.to_string()
            }
        }
    }

    /// Get total number of classes
    pub fn class_count(&self) -> u32 {
        self.header.class_defs_size
    }

    /// Get class definition by index
    pub fn get_class_def(&self, class_idx: u32) -> Result<ClassDef> {
        if class_idx >= self.header.class_defs_size {
            return Err(DexError::ParseError(format!(
                "Class index {} out of bounds",
                class_idx
            )));
        }

        // Each class_def_item is 32 bytes
        let class_def_offset = self.header.class_defs_off as usize + (class_idx as usize * structure::CLASS_DEF_SIZE);
        let mut cursor = Cursor::new(&self.data);
        cursor.seek(SeekFrom::Start(class_def_offset as u64))?;

        let class_idx = cursor.read_u32::<LittleEndian>()?;
        let access_flags = cursor.read_u32::<LittleEndian>()?;
        let superclass_idx = cursor.read_u32::<LittleEndian>()?;
        let interfaces_off = cursor.read_u32::<LittleEndian>()?;
        let source_file_idx = cursor.read_u32::<LittleEndian>()?;
        let annotations_off = cursor.read_u32::<LittleEndian>()?;
        let class_data_off = cursor.read_u32::<LittleEndian>()?;
        let static_values_off = cursor.read_u32::<LittleEndian>()?;

        Ok(ClassDef {
            class_idx,
            access_flags,
            superclass_idx,
            interfaces_off,
            source_file_idx,
            annotations_off,
            class_data_off,
            static_values_off,
        })
    }

    /// Parse class data (fields and methods)
    pub fn parse_class_data(&self, class_data_off: u32) -> Result<ClassData> {
        if class_data_off == 0 {
            return Ok(ClassData::default());
        }

        let mut cursor = Cursor::new(&self.data);
        cursor.seek(SeekFrom::Start(class_data_off as u64))?;

        let static_fields_size = self.read_uleb128(&mut cursor)?;
        let instance_fields_size = self.read_uleb128(&mut cursor)?;
        let direct_methods_size = self.read_uleb128(&mut cursor)?;
        let virtual_methods_size = self.read_uleb128(&mut cursor)?;

        let mut static_fields = Vec::new();
        let mut field_idx = 0u32;
        for _ in 0..static_fields_size {
            let field_idx_diff = self.read_uleb128(&mut cursor)?;
            field_idx += field_idx_diff;
            let access_flags = self.read_uleb128(&mut cursor)?;
            static_fields.push(EncodedField {
                field_idx,
                access_flags,
            });
        }

        let mut instance_fields = Vec::new();
        field_idx = 0;
        for _ in 0..instance_fields_size {
            let field_idx_diff = self.read_uleb128(&mut cursor)?;
            field_idx += field_idx_diff;
            let access_flags = self.read_uleb128(&mut cursor)?;
            instance_fields.push(EncodedField {
                field_idx,
                access_flags,
            });
        }

        let mut direct_methods = Vec::new();
        let mut method_idx = 0u32;
        for _ in 0..direct_methods_size {
            let method_idx_diff = self.read_uleb128(&mut cursor)?;
            method_idx += method_idx_diff;
            let access_flags = self.read_uleb128(&mut cursor)?;
            let code_off = self.read_uleb128(&mut cursor)?;
            direct_methods.push(EncodedMethod {
                method_idx,
                access_flags,
                code_off,
            });
        }

        let mut virtual_methods = Vec::new();
        method_idx = 0;
        for _ in 0..virtual_methods_size {
            let method_idx_diff = self.read_uleb128(&mut cursor)?;
            method_idx += method_idx_diff;
            let access_flags = self.read_uleb128(&mut cursor)?;
            let code_off = self.read_uleb128(&mut cursor)?;
            virtual_methods.push(EncodedMethod {
                method_idx,
                access_flags,
                code_off,
            });
        }

        Ok(ClassData {
            static_fields,
            instance_fields,
            direct_methods,
            virtual_methods,
        })
    }

    /// Get field information
    pub fn get_field_info(&self, field_idx: u32) -> Result<FieldInfo> {
        if field_idx >= self.header.field_ids_size {
            return Err(DexError::ParseError(format!(
                "Field index {} out of bounds",
                field_idx
            )));
        }

        // Each field_id_item is 8 bytes
        let field_id_offset = self.header.field_ids_off as usize + (field_idx as usize * structure::FIELD_ID_SIZE);
        let mut cursor = Cursor::new(&self.data);
        cursor.seek(SeekFrom::Start(field_id_offset as u64))?;

        let class_idx = cursor.read_u16::<LittleEndian>()?;
        let type_idx = cursor.read_u16::<LittleEndian>()?;
        let name_idx = cursor.read_u32::<LittleEndian>()?;

        Ok(FieldInfo {
            class_idx: class_idx as u32,
            type_idx: type_idx as u32,
            name_idx,
        })
    }

    /// Get method information
    pub fn get_method_info(&self, method_idx: u32) -> Result<MethodInfo> {
        if method_idx >= self.header.method_ids_size {
            return Err(DexError::ParseError(format!(
                "Method index {} out of bounds",
                method_idx
            )));
        }

        // Each method_id_item is 8 bytes
        let method_id_offset = self.header.method_ids_off as usize + (method_idx as usize * structure::METHOD_ID_SIZE);
        let mut cursor = Cursor::new(&self.data);
        cursor.seek(SeekFrom::Start(method_id_offset as u64))?;

        let class_idx = cursor.read_u16::<LittleEndian>()?;
        let proto_idx = cursor.read_u16::<LittleEndian>()?;
        let name_idx = cursor.read_u32::<LittleEndian>()?;

        Ok(MethodInfo {
            class_idx: class_idx as u32,
            proto_idx: proto_idx as u32,
            name_idx,
        })
    }

    /// Get method bytecode (instructions) from code_off
    pub fn get_method_bytecode(&self, code_off: u32) -> Result<Vec<u16>> {
        if code_off == 0 {
            // No code (abstract/native method)
            return Ok(Vec::new());
        }

        let mut cursor = Cursor::new(&self.data);
        cursor.seek(SeekFrom::Start(code_off as u64))?;

        // Read code_item structure
        // ref: https://source.android.com/docs/core/runtime/dex-format#code-item
        let _registers_size = cursor.read_u16::<LittleEndian>()?;  // u16
        let _ins_size = cursor.read_u16::<LittleEndian>()?;        // u16
        let _outs_size = cursor.read_u16::<LittleEndian>()?;       // u16
        let _tries_size = cursor.read_u16::<LittleEndian>()?;      // u16
        let _debug_info_off = cursor.read_u32::<LittleEndian>()?;  // u32
        let insns_size = cursor.read_u32::<LittleEndian>()?;       // u32

        // Read bytecode instructions (array of u16)
        let mut instructions = Vec::new();
        for _ in 0..insns_size {
            let insn = cursor.read_u16::<LittleEndian>()?;
            instructions.push(insn);
        }

        Ok(instructions)
    }

    /// Get prototype (method signature) information
    pub fn get_proto_info(&self, proto_idx: u32) -> Result<ProtoInfo> {
        if proto_idx >= self.header.proto_ids_size {
            return Err(DexError::ParseError(format!(
                "Proto index {} out of bounds",
                proto_idx
            )));
        }

        // Each proto_id_item is 12 bytes
        let proto_id_offset = self.header.proto_ids_off as usize + (proto_idx as usize * structure::PROTO_ID_SIZE);
        let mut cursor = Cursor::new(&self.data);
        cursor.seek(SeekFrom::Start(proto_id_offset as u64))?;

        let _shorty_idx = cursor.read_u32::<LittleEndian>()?;
        let return_type_idx = cursor.read_u32::<LittleEndian>()?;
        let parameters_off = cursor.read_u32::<LittleEndian>()?;

        // Parse parameters if present
        let mut parameters = Vec::new();
        if parameters_off != 0 {
            cursor.seek(SeekFrom::Start(parameters_off as u64))?;
            let size = cursor.read_u32::<LittleEndian>()?;
            for _ in 0..size {
                let type_idx = cursor.read_u16::<LittleEndian>()?;
                parameters.push(type_idx as u32);
            }
        }

        Ok(ProtoInfo {
            return_type_idx,
            parameters,
        })
    }
}

/// Class definition structure
#[derive(Debug, Clone)]
pub struct ClassDef {
    pub class_idx: u32,
    pub access_flags: u32,
    pub superclass_idx: u32,
    pub interfaces_off: u32,
    pub source_file_idx: u32,
    pub annotations_off: u32,
    pub class_data_off: u32,
    pub static_values_off: u32,
}

/// Class data (fields and methods)
#[derive(Debug, Clone, Default)]
pub struct ClassData {
    pub static_fields: Vec<EncodedField>,
    pub instance_fields: Vec<EncodedField>,
    pub direct_methods: Vec<EncodedMethod>,
    pub virtual_methods: Vec<EncodedMethod>,
}

/// Encoded field
#[derive(Debug, Clone)]
pub struct EncodedField {
    pub field_idx: u32,
    pub access_flags: u32,
}

/// Encoded method
#[derive(Debug, Clone)]
pub struct EncodedMethod {
    pub method_idx: u32,
    pub access_flags: u32,
    pub code_off: u32,
}

/// Field information
#[derive(Debug, Clone)]
pub struct FieldInfo {
    pub class_idx: u32,
    pub type_idx: u32,
    pub name_idx: u32,
}

/// Method information
#[derive(Debug, Clone)]
pub struct MethodInfo {
    pub class_idx: u32,
    pub proto_idx: u32,
    pub name_idx: u32,
}

/// Prototype (method signature) information
#[derive(Debug, Clone)]
pub struct ProtoInfo {
    pub return_type_idx: u32,
    pub parameters: Vec<u32>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_descriptor_conversion() {
        let parser = DexParser {
            data: vec![],
            header: unsafe { std::mem::zeroed() },
        };

        assert_eq!(parser.descriptor_to_java_type("V"), "void");
        assert_eq!(parser.descriptor_to_java_type("I"), "int");
        assert_eq!(parser.descriptor_to_java_type("Ljava/lang/String;"), "java.lang.String");
        assert_eq!(parser.descriptor_to_java_type("[I"), "int[]");
        assert_eq!(parser.descriptor_to_java_type("[[Ljava/lang/String;"), "java.lang.String[][]");
    }
}
