/// DEX file format constants
/// Reference: https://source.android.com/docs/core/runtime/dex-format

/// Access flags for classes, fields, and methods
pub mod access_flags {
    // Used for classes, fields, and methods
    pub const ACC_PUBLIC: u32 = 0x0001;
    pub const ACC_PRIVATE: u32 = 0x0002;
    pub const ACC_PROTECTED: u32 = 0x0004;
    pub const ACC_STATIC: u32 = 0x0008;
    pub const ACC_FINAL: u32 = 0x0010;

    // Used for classes only
    pub const ACC_INTERFACE: u32 = 0x0200;
    pub const ACC_ABSTRACT: u32 = 0x0400;
    pub const ACC_SYNTHETIC: u32 = 0x1000;
    pub const ACC_ANNOTATION: u32 = 0x2000;
    pub const ACC_ENUM: u32 = 0x4000;

    // Used for methods only
    pub const ACC_SYNCHRONIZED: u32 = 0x0020;
    pub const ACC_BRIDGE: u32 = 0x0040;
    pub const ACC_VARARGS: u32 = 0x0080;
    pub const ACC_NATIVE: u32 = 0x0100;
    pub const ACC_STRICT: u32 = 0x0800;

    // Used for fields only
    pub const ACC_VOLATILE: u32 = 0x0040;
    pub const ACC_TRANSIENT: u32 = 0x0080;

    // Constructor flag (synthetic)
    pub const ACC_CONSTRUCTOR: u32 = 0x10000;
    pub const ACC_DECLARED_SYNCHRONIZED: u32 = 0x20000;

    /// Get human-readable string representation of access flags
    pub fn flags_to_string(flags: u32) -> Vec<&'static str> {
        let mut result = Vec::new();

        if flags & ACC_PUBLIC != 0 {
            result.push("public");
        }
        if flags & ACC_PRIVATE != 0 {
            result.push("private");
        }
        if flags & ACC_PROTECTED != 0 {
            result.push("protected");
        }
        if flags & ACC_STATIC != 0 {
            result.push("static");
        }
        if flags & ACC_FINAL != 0 {
            result.push("final");
        }
        if flags & ACC_SYNCHRONIZED != 0 {
            result.push("synchronized");
        }
        if flags & ACC_VOLATILE != 0 {
            result.push("volatile");
        }
        if flags & ACC_TRANSIENT != 0 {
            result.push("transient");
        }
        if flags & ACC_BRIDGE != 0 {
            result.push("bridge");
        }
        if flags & ACC_VARARGS != 0 {
            result.push("varargs");
        }
        if flags & ACC_NATIVE != 0 {
            result.push("native");
        }
        if flags & ACC_INTERFACE != 0 {
            result.push("interface");
        }
        if flags & ACC_ABSTRACT != 0 {
            result.push("abstract");
        }
        if flags & ACC_STRICT != 0 {
            result.push("strictfp");
        }
        if flags & ACC_SYNTHETIC != 0 {
            result.push("synthetic");
        }
        if flags & ACC_ANNOTATION != 0 {
            result.push("annotation");
        }
        if flags & ACC_ENUM != 0 {
            result.push("enum");
        }

        result
    }
}

/// Type descriptor constants
pub mod type_descriptors {
    pub const VOID: char = 'V';
    pub const BOOLEAN: char = 'Z';
    pub const BYTE: char = 'B';
    pub const SHORT: char = 'S';
    pub const CHAR: char = 'C';
    pub const INT: char = 'I';
    pub const LONG: char = 'J';
    pub const FLOAT: char = 'F';
    pub const DOUBLE: char = 'D';
    pub const OBJECT: char = 'L';
    pub const ARRAY: char = '[';

    /// Convert type descriptor character to Java type name
    pub fn descriptor_to_java(descriptor: char) -> &'static str {
        match descriptor {
            VOID => "void",
            BOOLEAN => "boolean",
            BYTE => "byte",
            SHORT => "short",
            CHAR => "char",
            INT => "int",
            LONG => "long",
            FLOAT => "float",
            DOUBLE => "double",
            _ => "unknown",
        }
    }
}

/// DEX file magic and version constants
pub mod dex_magic {
    pub const MAGIC: &[u8] = b"dex\n";
    pub const VERSION_035: &[u8] = b"035\0";
    pub const VERSION_037: &[u8] = b"037\0";
    pub const VERSION_038: &[u8] = b"038\0";
    pub const VERSION_039: &[u8] = b"039\0";
    pub const VERSION_040: &[u8] = b"040\0";

    /// Check if version is supported
    pub fn is_supported_version(version: &[u8; 4]) -> bool {
        matches!(
            version,
            b"035\0" | b"037\0" | b"038\0" | b"039\0" | b"040\0"
        )
    }
}

/// DEX file structure constants
pub mod structure {
    pub const HEADER_SIZE: u32 = 0x70; // 112 bytes
    pub const ENDIAN_CONSTANT: u32 = 0x12345678;
    pub const REVERSE_ENDIAN_CONSTANT: u32 = 0x78563412;

    pub const NO_INDEX: u32 = 0xFFFFFFFF;

    // Item sizes in bytes
    pub const STRING_ID_SIZE: usize = 4;
    pub const TYPE_ID_SIZE: usize = 4;
    pub const PROTO_ID_SIZE: usize = 12;
    pub const FIELD_ID_SIZE: usize = 8;
    pub const METHOD_ID_SIZE: usize = 8;
    pub const CLASS_DEF_SIZE: usize = 32;
}

/// DEX map item type codes
#[repr(u16)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MapItemType {
    HeaderItem = 0x0000,
    StringIdItem = 0x0001,
    TypeIdItem = 0x0002,
    ProtoIdItem = 0x0003,
    FieldIdItem = 0x0004,
    MethodIdItem = 0x0005,
    ClassDefItem = 0x0006,
    CallSiteIdItem = 0x0007,
    MethodHandleItem = 0x0008,
    MapList = 0x1000,
    TypeList = 0x1001,
    AnnotationSetRefList = 0x1002,
    AnnotationSetItem = 0x1003,
    ClassDataItem = 0x2000,
    CodeItem = 0x2001,
    StringDataItem = 0x2002,
    DebugInfoItem = 0x2003,
    AnnotationItem = 0x2004,
    EncodedArrayItem = 0x2005,
    AnnotationsDirectoryItem = 0x2006,
    HiddenapiClassDataItem = 0xF000,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_access_flags_to_string() {
        let flags = access_flags::ACC_PUBLIC | access_flags::ACC_STATIC | access_flags::ACC_FINAL;
        let strings = access_flags::flags_to_string(flags);
        assert!(strings.contains(&"public"));
        assert!(strings.contains(&"static"));
        assert!(strings.contains(&"final"));
    }

    #[test]
    fn test_type_descriptors() {
        assert_eq!(type_descriptors::descriptor_to_java('I'), "int");
        assert_eq!(type_descriptors::descriptor_to_java('V'), "void");
        assert_eq!(type_descriptors::descriptor_to_java('Z'), "boolean");
    }

    #[test]
    fn test_dex_version() {
        assert!(dex_magic::is_supported_version(b"035\0"));
        assert!(dex_magic::is_supported_version(b"038\0"));
        assert!(!dex_magic::is_supported_version(b"999\0"));
    }
}
