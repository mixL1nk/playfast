use thiserror::Error;

#[derive(Error, Debug)]
pub enum ApkError {
    #[error("Failed to open APK file: {0}")]
    FileOpenError(String),

    #[error("Failed to read ZIP entry: {0}")]
    ZipReadError(String),

    #[error("Invalid APK: {0}")]
    InvalidApk(String),

    #[error("DEX file not found: {0}")]
    DexNotFound(String),

    #[error("Manifest not found")]
    ManifestNotFound,

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("ZIP error: {0}")]
    ZipError(#[from] zip::result::ZipError),
}

pub type Result<T> = std::result::Result<T, ApkError>;
