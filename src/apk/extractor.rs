use crate::apk::error::{ApkError, Result};
use std::fs::File;
use std::io::{Read, Seek};
use std::path::{Path, PathBuf};
use zip::ZipArchive;

/// Represents a single DEX file within an APK
#[derive(Debug, Clone)]
pub struct DexEntry {
    pub name: String,
    pub index: usize,
    pub data: Vec<u8>,
}

impl DexEntry {
    /// Create a new DexEntry
    pub fn new(name: String, index: usize, data: Vec<u8>) -> Self {
        Self { name, index, data }
    }

    /// Check if this is the primary DEX file (classes.dex)
    pub fn is_primary(&self) -> bool {
        self.name == "classes.dex"
    }

    /// Get the DEX file number (e.g., 2 for classes2.dex)
    pub fn dex_number(&self) -> Option<usize> {
        if self.name == "classes.dex" {
            return Some(1);
        }

        if self.name.starts_with("classes") && self.name.ends_with(".dex") {
            let num_str = &self.name[7..self.name.len() - 4];
            num_str.parse().ok()
        } else {
            None
        }
    }
}

/// APK file extractor for DEX files and resources
pub struct ApkExtractor {
    apk_path: PathBuf,
    dex_entries: Vec<DexEntry>,
    has_manifest: bool,
    has_resources: bool,
}

impl ApkExtractor {
    /// Open an APK file and scan for DEX files
    pub fn new<P: AsRef<Path>>(apk_path: P) -> Result<Self> {
        let apk_path = apk_path.as_ref().to_path_buf();

        if !apk_path.exists() {
            return Err(ApkError::FileOpenError(format!(
                "File does not exist: {}",
                apk_path.display()
            )));
        }

        let file = File::open(&apk_path)
            .map_err(|e| ApkError::FileOpenError(e.to_string()))?;

        let mut archive = ZipArchive::new(file)?;

        let mut dex_entries = Vec::new();
        let mut has_manifest = false;
        let mut has_resources = false;

        // Scan ZIP entries
        for i in 0..archive.len() {
            let mut entry = archive.by_index(i)?;
            let entry_name = entry.name().to_string();

            // Detect DEX files
            if entry_name.ends_with(".dex") && !entry_name.contains("/") {
                let mut data = Vec::new();
                entry.read_to_end(&mut data)?;

                dex_entries.push(DexEntry::new(entry_name.clone(), i, data));
            }

            // Check for manifest
            if entry_name == "AndroidManifest.xml" {
                has_manifest = true;
            }

            // Check for resources
            if entry_name == "resources.arsc" {
                has_resources = true;
            }
        }

        // Validate APK
        if !has_manifest {
            return Err(ApkError::InvalidApk(
                "No AndroidManifest.xml found".to_string()
            ));
        }

        if dex_entries.is_empty() {
            return Err(ApkError::InvalidApk(
                "No DEX files found".to_string()
            ));
        }

        // Sort DEX entries by name (classes.dex, classes2.dex, ...)
        dex_entries.sort_by(|a, b| {
            match (a.dex_number(), b.dex_number()) {
                (Some(na), Some(nb)) => na.cmp(&nb),
                _ => a.name.cmp(&b.name),
            }
        });

        Ok(Self {
            apk_path,
            dex_entries,
            has_manifest,
            has_resources,
        })
    }

    /// Get all DEX entries
    pub fn dex_entries(&self) -> &[DexEntry] {
        &self.dex_entries
    }

    /// Get number of DEX files
    pub fn dex_count(&self) -> usize {
        self.dex_entries.len()
    }

    /// Check if AndroidManifest.xml exists
    pub fn has_manifest(&self) -> bool {
        self.has_manifest
    }

    /// Check if resources.arsc exists
    pub fn has_resources(&self) -> bool {
        self.has_resources
    }

    /// Get APK file path
    pub fn apk_path(&self) -> &Path {
        &self.apk_path
    }

    /// Extract AndroidManifest.xml as raw bytes
    pub fn extract_manifest(&self) -> Result<Vec<u8>> {
        let file = File::open(&self.apk_path)?;
        let mut archive = ZipArchive::new(file)?;

        let mut manifest = archive.by_name("AndroidManifest.xml")
            .map_err(|_| ApkError::ManifestNotFound)?;

        let mut data = Vec::new();
        manifest.read_to_end(&mut data)?;
        Ok(data)
    }

    /// Extract resources.arsc as raw bytes
    pub fn extract_resources(&self) -> Result<Vec<u8>> {
        if !self.has_resources {
            return Err(ApkError::InvalidApk(
                "resources.arsc not found".to_string()
            ));
        }

        let file = File::open(&self.apk_path)?;
        let mut archive = ZipArchive::new(file)?;

        let mut resources = archive.by_name("resources.arsc")
            .map_err(|e| ApkError::ZipReadError(e.to_string()))?;

        let mut data = Vec::new();
        resources.read_to_end(&mut data)?;
        Ok(data)
    }

    /// Get primary DEX file (classes.dex)
    pub fn primary_dex(&self) -> Option<&DexEntry> {
        self.dex_entries.iter().find(|e| e.is_primary())
    }

    /// Extract a specific file from the APK
    pub fn extract_file(&self, filename: &str) -> Result<Vec<u8>> {
        let file = File::open(&self.apk_path)?;
        let mut archive = ZipArchive::new(file)?;

        let mut entry = archive.by_name(filename)
            .map_err(|_| ApkError::ZipReadError(format!("File not found: {}", filename)))?;

        let mut data = Vec::new();
        entry.read_to_end(&mut data)?;
        Ok(data)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dex_number_parsing() {
        let dex1 = DexEntry::new("classes.dex".to_string(), 0, vec![]);
        assert_eq!(dex1.dex_number(), Some(1));
        assert!(dex1.is_primary());

        let dex2 = DexEntry::new("classes2.dex".to_string(), 1, vec![]);
        assert_eq!(dex2.dex_number(), Some(2));
        assert!(!dex2.is_primary());

        let dex15 = DexEntry::new("classes15.dex".to_string(), 2, vec![]);
        assert_eq!(dex15.dex_number(), Some(15));
    }
}
