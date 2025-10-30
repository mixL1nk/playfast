//! Google Play API Client for APK downloads
//!
//! This module wraps the gpapi crate to provide Python bindings for downloading
//! APKs from Google Play Store.

use pyo3::prelude::*;
use pyo3::exceptions::{PyValueError, PyRuntimeError};
use std::path::PathBuf;
use std::sync::{Arc, atomic::{AtomicBool, Ordering}};
use std::time::Duration;
use serde_json;

/// Google Play API client for downloading APKs
#[pyclass]
pub struct GpapiClient {
    inner: Option<gpapi::Gpapi>,
    email: String,
    oauth_token: Option<String>,
    aas_token: Option<String>,
    device: String,
    locale: String,
    timezone: String,
    is_logged_in: bool,
}

#[pymethods]
impl GpapiClient {
    /// Create new Google Play API client
    ///
    /// Args:
    ///     email (str): Google account email
    ///     oauth_token (str, optional): OAuth token for first-time setup
    ///     aas_token (str, optional): AAS token for returning users
    ///     device (str): Device codename (default: "px_9a" = Pixel 9a)
    ///     locale (str): Locale (default: "en_US")
    ///     timezone (str): Timezone (default: "America/New_York")
    ///
    /// At least one of oauth_token or aas_token must be provided.
    #[new]
    #[pyo3(signature = (email, oauth_token=None, aas_token=None, device="px_9a", locale="en_US", timezone="America/New_York"))]
    fn new(
        email: String,
        oauth_token: Option<String>,
        aas_token: Option<String>,
        device: &str,
        locale: &str,
        timezone: &str,
    ) -> PyResult<Self> {
        // Validation: must have either oauth_token or aas_token
        if oauth_token.is_none() && aas_token.is_none() {
            return Err(PyValueError::new_err(
                "Must provide either oauth_token or aas_token"
            ));
        }

        Ok(Self {
            inner: None,
            email,
            oauth_token,
            aas_token,
            device: device.to_string(),
            locale: locale.to_string(),
            timezone: timezone.to_string(),
            is_logged_in: false,
        })
    }

    /// Login to Google Play
    ///
    /// This method:
    /// 1. Exchanges OAuth token for AAS token if needed
    /// 2. Performs device checkin
    /// 3. Authenticates with Google Play
    fn login(&mut self, py: Python) -> PyResult<()> {
        // Use tokio runtime to run async code
        let runtime = tokio::runtime::Runtime::new()
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to create runtime: {}", e)))?;

        // Capture values before entering closure
        let device = self.device.clone();
        let email = self.email.clone();
        let locale = self.locale.clone();
        let timezone = self.timezone.clone();
        let aas_token = self.aas_token.clone();
        let oauth_token = self.oauth_token.clone();

        let (api, new_aas_token) = py.detach(|| {
            runtime.block_on(async {
                // Create Gpapi instance
                let mut api = gpapi::Gpapi::new(&device, &email);
                api.set_locale(&locale);
                api.set_timezone(&timezone);

                let mut new_aas_token = None;

                // Smart login: If AAS token exists, use it. Otherwise exchange OAuth token.
                if let Some(aas_token) = &aas_token {
                    // Direct AAS token flow
                    api.set_aas_token(aas_token);
                } else if let Some(oauth_token) = &oauth_token {
                    // OAuth → AAS exchange flow
                    api.request_aas_token(oauth_token)
                        .await
                        .map_err(|e| PyRuntimeError::new_err(format!("Failed to exchange OAuth token: {}", e)))?;

                    // Save the newly obtained AAS token
                    new_aas_token = api.get_aas_token().map(|s| s.to_string());
                } else {
                    return Err(PyValueError::new_err(
                        "Must provide either oauth_token or aas_token"
                    ));
                }

                // Perform login (checkin, upload device config, request auth token)
                api.login()
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Login failed: {}", e)))?;

                Ok::<(gpapi::Gpapi, Option<String>), PyErr>((api, new_aas_token))
            })
        })?;

        // Update instance state after async operation completes
        if let Some(token) = new_aas_token {
            self.aas_token = Some(token);
        }
        self.inner = Some(api);
        self.is_logged_in = true;

        Ok(())
    }

    /// Get current AAS token
    ///
    /// Returns:
    ///     str: AAS token string
    fn get_aas_token(&self) -> PyResult<String> {
        self.aas_token
            .clone()
            .ok_or_else(|| PyRuntimeError::new_err("No AAS token available. Call login() first."))
    }

    /// Save credentials to JSON file
    ///
    /// Args:
    ///     path (str): File path to save credentials
    fn save_credentials(&self, path: &str) -> PyResult<()> {
        use std::fs;
        use serde_json::json;

        let creds = json!({
            "email": self.email,
            "aas_token": self.aas_token,
            "device": self.device,
            "locale": self.locale,
            "timezone": self.timezone,
        });

        let path = PathBuf::from(path);

        // Create parent directories if needed
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to create directory: {}", e)))?;
        }

        // Write JSON file
        fs::write(&path, serde_json::to_string_pretty(&creds).unwrap())
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to write file: {}", e)))?;

        // Set file permissions to 0600 (owner read/write only) on Unix
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let mut perms = fs::metadata(&path)
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to get file metadata: {}", e)))?
                .permissions();
            perms.set_mode(0o600);
            fs::set_permissions(&path, perms)
                .map_err(|e| PyRuntimeError::new_err(format!("Failed to set file permissions: {}", e)))?;
        }

        Ok(())
    }

    /// Load client from saved credentials file
    ///
    /// Args:
    ///     path (str): Path to credentials JSON file
    ///
    /// Returns:
    ///     GpapiClient: Initialized and logged-in client
    #[staticmethod]
    fn from_credentials(py: Python, path: &str) -> PyResult<Self> {
        use std::fs;
        use serde_json::Value;

        let contents = fs::read_to_string(path)
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to read file: {}", e)))?;

        let creds: Value = serde_json::from_str(&contents)
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to parse JSON: {}", e)))?;

        let email = creds["email"]
            .as_str()
            .ok_or_else(|| PyValueError::new_err("Missing 'email' in credentials file"))?
            .to_string();

        let aas_token = creds["aas_token"]
            .as_str()
            .map(|s| s.to_string());

        let device = creds["device"]
            .as_str()
            .unwrap_or("px_9a")
            .to_string();

        let locale = creds["locale"]
            .as_str()
            .unwrap_or("en_US")
            .to_string();

        let timezone = creds["timezone"]
            .as_str()
            .unwrap_or("America/New_York")
            .to_string();

        let mut client = Self {
            inner: None,
            email,
            oauth_token: None,
            aas_token,
            device,
            locale,
            timezone,
            is_logged_in: false,
        };

        // Automatically login
        client.login(py)?;

        Ok(client)
    }

    /// Download APK file from Google Play Store
    ///
    /// Args:
    ///     package_id (str): Package ID (e.g., "com.instagram.android")
    ///     dest_path (str): Destination file path for the APK
    ///     version_code (int, optional): Specific version code to download (default: latest)
    ///     progress_callback (callable, optional): Callback function(current_bytes: int, total_bytes: int)
    ///         Called periodically with file size updates (every 0.5 seconds)
    ///
    /// Returns:
    ///     str: Path to the downloaded APK file
    ///
    /// Example:
    ///     >>> def progress(current, total):
    ///     ...     percent = (current / total * 100) if total > 0 else 0
    ///     ...     print(f"Progress: {percent:.1f}%")
    ///     >>> client.download_apk("com.app", "/tmp", None, progress)
    fn download_apk(
        &self,
        py: Python,
        package_id: &str,
        dest_path: &str,
        version_code: Option<i32>,
        progress_callback: Option<Py<PyAny>>,
    ) -> PyResult<String> {
        if !self.is_logged_in {
            return Err(PyRuntimeError::new_err(
                "Not logged in. Call login() first."
            ));
        }

        let api = self.inner.as_ref().ok_or_else(|| {
            PyRuntimeError::new_err("API not initialized. Call login() first.")
        })?;

        let runtime = tokio::runtime::Runtime::new()
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to create runtime: {}", e)))?;

        let package_id = package_id.to_string();
        let dest_path = PathBuf::from(dest_path);
        let apk_file_path = dest_path.join(format!("{}.apk", &package_id));

        // Python callback을 Arc로 감싸서 thread-safe하게 공유
        let progress_callback = progress_callback.map(Arc::new);

        // Clone api to move into closure (gpapi::Gpapi doesn't implement Clone)
        // We'll need to work with a reference instead
        let result = py.detach(|| {
            runtime.block_on(async {
                // Note: We don't fetch expected size from package details because
                // info_download_size represents the total app size (including all splits),
                // but we only download the base APK. The progress bar will show actual
                // downloaded bytes without a misleading total.
                let total_size = 0u64;

                // Spawn progress monitoring task if callback provided
                let monitor_handle = if let Some(ref callback) = progress_callback {
                    let apk_path = apk_file_path.clone();
                    let done = Arc::new(AtomicBool::new(false));
                    let done_clone = Arc::clone(&done);
                    let callback_clone = Arc::clone(callback);

                    let handle = std::thread::spawn(move || {
                        while !done_clone.load(Ordering::Relaxed) {
                            if apk_path.exists() {
                                if let Ok(metadata) = std::fs::metadata(&apk_path) {
                                    let current_size = metadata.len();

                                    // Call Python callback with current and total size
                                    Python::attach(|py| {
                                        let _ = callback_clone.call1(py, (current_size, total_size));
                                    });
                                }
                            }

                            std::thread::sleep(Duration::from_millis(500));
                        }
                    });

                    Some((handle, done))
                } else {
                    None
                };

                // Download the APK
                // Note: split_if_available=false, include_additional_files=false for simplicity
                let download_result = api.download(
                    &package_id,
                    version_code,
                    false, // split_if_available
                    false, // include_additional_files
                    &dest_path,
                    None,  // gpapi progress callback (not used)
                )
                .await
                .map_err(|e| PyRuntimeError::new_err(format!("Download failed: {}", e)));

                // Stop monitoring task
                if let Some((handle, done)) = monitor_handle {
                    done.store(true, Ordering::Relaxed);
                    let _ = handle.join();

                    // Final callback with complete size
                    if let Ok(metadata) = std::fs::metadata(&apk_file_path) {
                        Python::attach(|py| {
                            if let Some(callback) = &progress_callback {
                                let _ = callback.call1(py, (metadata.len(), metadata.len()));
                            }
                        });
                    }
                }

                download_result?;

                Ok::<String, PyErr>(apk_file_path.to_string_lossy().to_string())
            })
        });

        result
    }

    /// Get package details from Google Play Store
    ///
    /// Args:
    ///     package_id (str): Package ID (e.g., "com.instagram.android")
    ///
    /// Returns:
    ///     dict: Package details (title, version, etc.)
    fn get_package_details(&self, py: Python, package_id: &str) -> PyResult<String> {
        if !self.is_logged_in {
            return Err(PyRuntimeError::new_err(
                "Not logged in. Call login() first."
            ));
        }

        let api = self.inner.as_ref().ok_or_else(|| {
            PyRuntimeError::new_err("API not initialized. Call login() first.")
        })?;

        let runtime = tokio::runtime::Runtime::new()
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to create runtime: {}", e)))?;

        let package_id = package_id.to_string();

        py.detach(|| {
            runtime.block_on(async {
                let details = api
                    .details(&package_id)
                    .await
                    .map_err(|e| PyRuntimeError::new_err(format!("Failed to get details: {}", e)))?;

                // Return debug representation
                // TODO: In production, parse the protobuf and return a proper Python dict
                let details_str = format!("{:#?}", details);

                Ok::<String, PyErr>(details_str)
            })
        })
    }

    fn __repr__(&self) -> String {
        format!(
            "GpapiClient(email='{}', device='{}', logged_in={})",
            self.email, self.device, self.is_logged_in
        )
    }
}
