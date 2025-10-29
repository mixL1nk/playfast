use thiserror::Error;

#[derive(Error, Debug)]
pub enum DexError {
    #[error("Failed to parse DEX file: {0}")]
    ParseError(String),

    #[error("Invalid DEX file: {0}")]
    InvalidDex(String),

    #[error("Class not found: {0}")]
    ClassNotFound(String),

    #[error("Method not found: {0}")]
    MethodNotFound(String),

    #[error("Field not found: {0}")]
    FieldNotFound(String),

    #[error("Invalid filter: {0}")]
    InvalidFilter(String),

    #[error("DEX file error: {0}")]
    DexFileError(String),

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
}

pub type Result<T> = std::result::Result<T, DexError>;
