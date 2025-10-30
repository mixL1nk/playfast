"""Tests for ApkAnalyzer high-level API.

Note: These tests use real APK files and can be slow.
Use pytest -m "not slow" to skip slow tests.
"""

from pathlib import Path

import pytest

from playfast import ApkAnalyzer


def test_apk_analyzer_initialization(sample_apk_path):
    """Test ApkAnalyzer initialization with valid APK."""
    analyzer = ApkAnalyzer(str(sample_apk_path))
    assert analyzer.apk_path == Path(sample_apk_path)


def test_apk_analyzer_file_not_found():
    """Test ApkAnalyzer raises error for non-existent file."""
    with pytest.raises(FileNotFoundError, match="APK file not found"):
        ApkAnalyzer("nonexistent.apk")


def test_apk_analyzer_manifest_property(sample_apk_path):
    """Test accessing manifest property."""
    analyzer = ApkAnalyzer(str(sample_apk_path))
    manifest = analyzer.manifest

    assert manifest is not None
    assert hasattr(manifest, "package_name")
    assert manifest.package_name  # Should have a package name


def test_apk_analyzer_has_manifest(sample_apk_path):
    """Test has_manifest property."""
    analyzer = ApkAnalyzer(str(sample_apk_path))
    assert analyzer.has_manifest is True


def test_apk_analyzer_get_statistics(sample_apk_path):
    """Test getting APK statistics."""
    analyzer = ApkAnalyzer(str(sample_apk_path))
    stats = analyzer.get_statistics()

    assert isinstance(stats, dict)
    assert "class_count" in stats or "classes" in stats


def test_apk_analyzer_dex_count(sample_apk_path):
    """Test getting DEX file count."""
    analyzer = ApkAnalyzer(str(sample_apk_path))
    assert analyzer.dex_count > 0


def test_apk_analyzer_find_classes(sample_apk_path):
    """Test finding classes in APK."""
    analyzer = ApkAnalyzer(str(sample_apk_path))

    # Find Activity classes (most apps have at least one)
    activities = analyzer.find_classes(name="Activity", limit=5)
    assert isinstance(activities, list)


def test_apk_analyzer_find_methods(sample_apk_path):
    """Test finding methods in APK."""
    analyzer = ApkAnalyzer(str(sample_apk_path))

    # Find onCreate methods (common in Android apps)
    methods = analyzer.find_methods(method_name="onCreate", limit=5)
    assert isinstance(methods, list)
    # Each result should be a tuple of (class, method)
    if methods:
        assert len(methods[0]) == 2


def test_apk_analyzer_get_all_packages(sample_apk_path):
    """Test getting all package names."""
    analyzer = ApkAnalyzer(str(sample_apk_path))
    packages = analyzer.get_all_packages()

    assert isinstance(packages, list)
    assert len(packages) > 0
    # Should include the main app package
    manifest = analyzer.manifest
    assert any(manifest.package_name in pkg for pkg in packages)


def test_apk_analyzer_get_package_groups(sample_apk_path):
    """Test getting package groups."""
    analyzer = ApkAnalyzer(str(sample_apk_path))
    groups = analyzer.get_package_groups()

    assert isinstance(groups, dict)
    assert len(groups) > 0


def test_apk_analyzer_get_third_party_libraries(sample_apk_path):
    """Test identifying third-party libraries."""
    analyzer = ApkAnalyzer(str(sample_apk_path))
    libs = analyzer.get_third_party_libraries()

    assert isinstance(libs, dict)


def test_apk_analyzer_find_webview_usage(sample_apk_path):
    """Test finding WebView usage."""
    analyzer = ApkAnalyzer(str(sample_apk_path))
    usage = analyzer.find_webview_usage()

    assert isinstance(usage, dict)
    # The structure varies, just check it's a dict with some content
    assert len(usage) > 0


def test_apk_analyzer_analyze_entry_points(sample_apk_path):
    """Test analyzing Android entry points."""
    analyzer = ApkAnalyzer(str(sample_apk_path))
    result = analyzer.analyze_entry_points()

    assert isinstance(result, dict)
    assert "entry_points" in result
    assert "deeplink_handlers" in result
    # Note: 'stats' might be a string, not a dict
    assert "stats" in result
    assert isinstance(result["entry_points"], list)
    assert isinstance(result["deeplink_handlers"], list)


@pytest.mark.slow
def test_apk_analyzer_find_webview_flows(sample_apk_path):
    """Test finding WebView data flows (slow)."""
    analyzer = ApkAnalyzer(str(sample_apk_path))

    # Use max_depth=2 for faster test
    flows = analyzer.find_webview_flows(max_depth=2)
    assert isinstance(flows, list)


@pytest.mark.slow
def test_apk_analyzer_find_file_flows(sample_apk_path):
    """Test finding file I/O flows (slow)."""
    analyzer = ApkAnalyzer(str(sample_apk_path))

    flows = analyzer.find_file_flows(max_depth=2)
    assert isinstance(flows, list)


@pytest.mark.slow
def test_apk_analyzer_find_network_flows(sample_apk_path):
    """Test finding network flows (slow)."""
    analyzer = ApkAnalyzer(str(sample_apk_path))

    flows = analyzer.find_network_flows(max_depth=2)
    assert isinstance(flows, list)


@pytest.mark.slow
def test_apk_analyzer_find_sql_flows(sample_apk_path):
    """Test finding SQL flows (slow)."""
    analyzer = ApkAnalyzer(str(sample_apk_path))

    flows = analyzer.find_sql_flows(max_depth=2)
    assert isinstance(flows, list)


@pytest.mark.slow
def test_apk_analyzer_find_custom_flows(sample_apk_path):
    """Test finding custom flows (slow)."""
    analyzer = ApkAnalyzer(str(sample_apk_path))

    # Look for common Android APIs
    flows = analyzer.find_custom_flows(["startActivity"], max_depth=2)
    assert isinstance(flows, list)


@pytest.mark.slow
def test_apk_analyzer_find_deeplink_flows(sample_apk_path):
    """Test finding deeplink flows (slow)."""
    analyzer = ApkAnalyzer(str(sample_apk_path))

    flows = analyzer.find_deeplink_flows("webview", max_depth=2)
    assert isinstance(flows, list)


def test_apk_analyzer_repr(sample_apk_path):
    """Test string representation."""
    analyzer = ApkAnalyzer(str(sample_apk_path))
    repr_str = repr(analyzer)

    assert "ApkAnalyzer" in repr_str
    assert str(sample_apk_path.name) in repr_str
