#!/bin/bash
set -euo pipefail

# Screenshots how Apple should have built them
# https://cleanshot.com/

APP_NAME="CleanShot X"
BUNDLE_ID="com.getcleanshot.app"
1P_LICENSE_KEY_PATH="op://Personal/CleanShot X/license key"

# Check if 1Password CLI is installed
if ! command -v op &>/dev/null; then
    echo "Error: 1Password CLI (op) is not installed" >&2
    exit 1
fi

# Check if 1Password CLI is configured/enabled
# Use </dev/null to prevent interactive prompt from hanging
if ! op account get &>/dev/null </dev/null; then
    echo "Error: 1Password CLI is not configured. Enable app integration or sign in." >&2
    echo "https://developer.1password.com/docs/cli/get-started/#step-2-turn-on-the-1password-desktop-app-integration" >&2
    exit 1
fi

# Bail if not running on macOS
if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "Error: This script only runs on macOS" >&2
    exit 1
fi

# Check if app is installed
if [[ ! -d "/Applications/${APP_NAME}.app" ]]; then
    echo "Error: ${APP_NAME} is not installed in /Applications" >&2
    exit 1
fi

# Track if app was running before we started
was_running=false
if pgrep -xq "$APP_NAME"; then
    was_running=true
fi

# Launch app if it hasn't been run yet (no preferences exist)
if ! defaults read "$BUNDLE_ID" &>/dev/null; then
    echo "${APP_NAME} has never been run. Launching it to initialize preferences..."
    open -a "$APP_NAME"
    sleep 2
fi

# Quit app before modifying preferences
if pgrep -xq "$APP_NAME"; then
    echo "Quitting ${APP_NAME} to safely modify preferences..."
    osascript -e "quit app \"${APP_NAME}\""
    sleep 1
fi

# Set license key from 1Password
license_key=$(op read "$1P_LICENSE_KEY_PATH")
if [[ -z "$license_key" ]]; then
    echo "Error: Failed to read license key from 1Password" >&2
    exit 1
fi
defaults write "$BUNDLE_ID" "activationKey" -string "$license_key"

# Hide desktop icons in screenshots
defaults write "$BUNDLE_ID" "captureWithoutDesktopIcons" -int 1

# No thank you
defaults write "$BUNDLE_ID" "analyticsAllowed" -int 0

# Disable automatic checks (managed via Homebrew)
defaults write "$BUNDLE_ID" "SUEnableAutomaticChecks" -int 0

# Accept EULA
defaults write "$BUNDLE_ID" "lastAcceptedEulaVersion" -int 1

# Don't show onboarding
# defaults write "$BUNDLE_ID" "onboardingDisplayed" -int 1 # TODO: Test if this works on a fresh install, it may be doing permissions requests

# Relaunch if it was running before
if $was_running; then
    echo "Relaunching ${APP_NAME}..."
    open -a "$APP_NAME"
fi