#!/usr/bin/env python3
"""
Google Play Authentication Setup

This example shows how to set up authentication with Google Play Store API.

Two authentication flows are supported:
1. First-time setup: OAuth token → AAS token exchange
2. Returning users: Direct AAS token usage

Prerequisites:
- Obtain OAuth token from Google's embedded setup page:
  https://accounts.google.com/EmbeddedSetup
- Open browser dev console, login, and copy the oauth_token cookie (starts with "oauth2_4/")
- The OAuth token can only be used once to obtain an AAS token
- The AAS token can be reused for subsequent API calls
"""

import sys
import os
from pathlib import Path
from playfast import ApkDownloader


def setup_first_time(email: str, oauth_token: str, credentials_path: str):
    """
    First-time authentication setup.

    Exchanges OAuth token for persistent AAS token and saves credentials.

    Args:
        email: Google account email
        oauth_token: OAuth token from embedded setup (starts with "oauth2_4/")
        credentials_path: Path to save credentials JSON file
    """
    print(f"🔐 Setting up authentication for {email}...")
    print(f"📝 Using OAuth token: {oauth_token[:20]}...")

    # Create downloader with OAuth token
    downloader = ApkDownloader(
        email=email,
        oauth_token=oauth_token,
        device="px_9a",  # Pixel 9a (default)
        locale="en_US",
        timezone="America/New_York"
    )

    print("🔄 Logging in (this will exchange OAuth for AAS token)...")
    try:
        downloader.login()
        print("✅ Login successful!")

        # Get and display AAS token
        aas_token = downloader.get_aas_token()
        print(f"🎫 AAS token obtained: {aas_token[:20]}...")

        # Save credentials for future use
        downloader.save_credentials(credentials_path)
        print(f"💾 Credentials saved to: {credentials_path}")
        print(f"   (File permissions set to 0600 on Unix)")

        print("\n✨ Setup complete! You can now use the AAS token for future API calls.")
        print(f"   Next time, use: ApkDownloader.from_credentials('{credentials_path}')")

    except Exception as e:
        print(f"❌ Login failed: {e}")
        sys.exit(1)


def setup_with_aas_token(email: str, aas_token: str, credentials_path: str):
    """
    Authentication setup with existing AAS token.

    Skips OAuth exchange and directly uses AAS token.

    Args:
        email: Google account email
        aas_token: Existing AAS token (starts with "aas_et/")
        credentials_path: Path to save credentials JSON file
    """
    print(f"🔐 Setting up authentication for {email}...")
    print(f"🎫 Using AAS token: {aas_token[:20]}...")

    # Create downloader with AAS token (skips OAuth exchange)
    downloader = ApkDownloader(
        email=email,
        aas_token=aas_token,
        device="px_9a",
        locale="en_US",
        timezone="America/New_York"
    )

    print("🔄 Logging in with AAS token...")
    try:
        downloader.login()
        print("✅ Login successful!")

        # Save credentials for future use
        downloader.save_credentials(credentials_path)
        print(f"💾 Credentials saved to: {credentials_path}")

        print("\n✨ Setup complete!")

    except Exception as e:
        print(f"❌ Login failed: {e}")
        sys.exit(1)


def load_from_credentials(credentials_path: str):
    """
    Load client from saved credentials.

    This is the recommended way for returning users - just load and go!

    Args:
        credentials_path: Path to credentials JSON file
    """
    print(f"📂 Loading credentials from: {credentials_path}...")

    try:
        downloader = ApkDownloader.from_credentials(credentials_path)
        print("✅ Loaded successfully!")
        print(f"📧 Email: {downloader.email}")
        print(f"🎫 AAS token: {downloader.get_aas_token()[:20]}...")

        print("\n✨ Ready to use! Downloader is already logged in.")
        return downloader

    except Exception as e:
        print(f"❌ Failed to load credentials: {e}")
        sys.exit(1)


def main():
    print("=" * 60)
    print("Google Play Authentication Setup")
    print("=" * 60)
    print()

    # Default credentials path
    default_creds_path = os.path.expanduser("~/.playfast/credentials.json")

    print("Choose authentication method:")
    print("  1. First-time setup (OAuth token)")
    print("  2. Setup with existing AAS token")
    print("  3. Load from saved credentials")
    print()

    choice = input("Enter choice (1-3): ").strip()

    if choice == "1":
        print("\n--- First-time OAuth Setup ---")
        print("Get OAuth token from:")
        print("https://accounts.google.com/EmbeddedSetup")
        print()

        email = input("Google email: ").strip()
        oauth_token = input("OAuth token (starts with 'oauth2_4/'): ").strip()
        creds_path = input(f"Save credentials to [{default_creds_path}]: ").strip() or default_creds_path

        setup_first_time(email, oauth_token, creds_path)

    elif choice == "2":
        print("\n--- AAS Token Setup ---")
        email = input("Google email: ").strip()
        aas_token = input("AAS token (starts with 'aas_et/'): ").strip()
        creds_path = input(f"Save credentials to [{default_creds_path}]: ").strip() or default_creds_path

        setup_with_aas_token(email, aas_token, creds_path)

    elif choice == "3":
        print("\n--- Load Existing Credentials ---")
        creds_path = input(f"Credentials path [{default_creds_path}]: ").strip() or default_creds_path

        downloader = load_from_credentials(creds_path)
        print("\nℹ️  Downloader is ready - you can now use it for API calls!")

    else:
        print("❌ Invalid choice")
        sys.exit(1)


if __name__ == "__main__":
    main()
