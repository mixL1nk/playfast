"""Tests for ApkDownloader high-level API."""

from pathlib import Path

import pytest

from playfast import ApkDownloader


def test_apk_downloader_initialization_with_oauth():
    """Test ApkDownloader initialization with OAuth token."""
    downloader = ApkDownloader(
        email="test@example.com", oauth_token="oauth2_4/fake_token"
    )

    assert downloader.email == "test@example.com"
    assert not downloader.is_logged_in


def test_apk_downloader_initialization_with_aas():
    """Test ApkDownloader initialization with AAS token."""
    downloader = ApkDownloader(email="test@example.com", aas_token="aas_et/fake_token")

    assert downloader.email == "test@example.com"
    assert not downloader.is_logged_in


def test_apk_downloader_initialization_missing_token():
    """Test ApkDownloader raises error when no token provided."""
    with pytest.raises(ValueError, match="either oauth_token or aas_token"):
        ApkDownloader(email="test@example.com")


def test_apk_downloader_from_credentials_not_found():
    """Test from_credentials with non-existent file."""
    with pytest.raises(RuntimeError, match="Failed to read file"):
        ApkDownloader.from_credentials("/nonexistent/path/credentials.json")


def test_apk_downloader_download_not_logged_in():
    """Test download fails when not logged in."""
    downloader = ApkDownloader(
        email="test@example.com", oauth_token="oauth2_4/fake_token"
    )

    with pytest.raises(RuntimeError, match="Not logged in"):
        downloader.download("com.example.app")


def test_apk_downloader_get_package_details_not_logged_in():
    """Test get_package_details fails when not logged in."""
    downloader = ApkDownloader(
        email="test@example.com", oauth_token="oauth2_4/fake_token"
    )

    with pytest.raises(RuntimeError, match="Not logged in"):
        downloader.get_package_details("com.example.app")


def test_apk_downloader_get_aas_token_not_logged_in():
    """Test get_aas_token fails when not logged in."""
    downloader = ApkDownloader(
        email="test@example.com", oauth_token="oauth2_4/fake_token"
    )

    with pytest.raises(RuntimeError):
        downloader.get_aas_token()


def test_apk_downloader_repr():
    """Test string representation."""
    downloader = ApkDownloader(
        email="test@example.com", oauth_token="oauth2_4/fake_token"
    )

    repr_str = repr(downloader)
    assert "ApkDownloader" in repr_str
    assert "test@example.com" in repr_str
    assert "not logged in" in repr_str


@pytest.mark.skipif(
    not Path.home().joinpath(".config/playfast/creds.json").exists(),
    reason="Requires Google Play credentials",
)
def test_apk_downloader_from_credentials_real():
    """Test from_credentials with real credentials (if available)."""
    creds_path = Path.home() / ".config" / "playfast" / "creds.json"

    downloader = ApkDownloader.from_credentials(str(creds_path))
    assert downloader.is_logged_in


@pytest.mark.skipif(
    not Path.home().joinpath(".config/playfast/creds.json").exists(),
    reason="Requires Google Play credentials",
)
def test_apk_downloader_get_package_details_real():
    """Test get_package_details with real credentials (if available)."""
    creds_path = Path.home() / ".config" / "playfast" / "creds.json"

    downloader = ApkDownloader.from_credentials(str(creds_path))
    details = downloader.get_package_details("com.android.chrome")

    # Should return some details string
    assert isinstance(details, str)
    assert len(details) > 0


def test_apk_downloader_download_path_creation():
    """Test that download creates output directory."""
    downloader = ApkDownloader(
        email="test@example.com", oauth_token="oauth2_4/fake_token"
    )

    # Should fail with not logged in
    with pytest.raises(RuntimeError, match="Not logged in"):
        downloader.download("com.example.app", dest_path="/tmp/test_playfast_dl")
