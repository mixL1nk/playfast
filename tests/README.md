# Tests

This directory contains tests for both Python and Rust components.

## Structure

```
tests/
├── python/              # Python tests (pytest)
│   ├── conftest.py     # pytest fixtures and configuration
│   └── test_*.py       # Python test modules
└── rust/               # Rust tests (cargo test)
    └── integration_tests.rs
```

## Running Tests

### Python Tests

```bash
# Run all Python tests
pytest tests/python/

# Run with coverage
pytest tests/python/ --cov=python/playfast --cov-report=html

# Run specific test file
pytest tests/python/test_async_client.py -v
```

### Rust Tests

```bash
# Run all Rust tests
cargo test

# Run specific integration test
cargo test --test integration_tests

# Run with output
cargo test -- --nocapture
```

### Run All Tests

```bash
# Python + Rust
pytest tests/python/ && cargo test
```

## Test APK Files

Tests that analyze APK files require a sample APK. The test suite uses an **automatic download system**.

### How It Works

The `sample_apk_path` fixture in `conftest.py`:

1. Checks for existing APK at `/tmp/playfast_apks/com.sampleapp.apk`
1. Auto-downloads if missing (using your Google Play credentials)
1. Caches for future runs (downloads only once per machine)

### Environment Variables

```bash
# Use a custom APK file
export PLAYFAST_TEST_APK="/path/to/your/app.apk"

# Skip auto-download (tests will skip if APK is missing)
export PLAYFAST_SKIP_DOWNLOAD=1

# Clear cache to force re-download
rm /tmp/playfast_apks/com.sampleapp.apk
```

### CI/CD Setup

For CI environments, either:

- Pre-download and cache APK in `/tmp/playfast_apks/`
- Skip APK tests with `PLAYFAST_SKIP_DOWNLOAD=1`
- Store credentials as secrets and allow auto-download

## Test Types

### Python Tests (`tests/python/`)

- **Unit tests** (`unit/`): Fast tests, no APK needed
- **Integration tests** (`integration/`): Require APK files
- **Development tests** (`development/`): Debugging/exploration
- **Coverage target**: 85%+

### Rust Tests (`tests/rust/`)

- **Integration tests**: Test Rust core functionality
- **Pattern validation**: Test parsing logic
- **Data structure tests**: Test JSON/HTML parsing

## CI/CD

Both test suites are run in CI:

```yaml
- name: Test Python
  run: pytest tests/python/ --cov=python/playfast

- name: Test Rust
  run: cargo test
```
