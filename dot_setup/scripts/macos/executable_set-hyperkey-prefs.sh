#!/bin/bash
set -euo pipefail

# Convert caps lock to hyper key
# https://hyperkey.app/

APP_NAME="Hyperkey"
BUNDLE_ID="com.knollsoft.Hyperkey"

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

# Disable automatic checks (managed via Homebrew)
defaults write "$BUNDLE_ID" "SUEnableAutomaticChecks" -int 0

# Remap caps lock to hyper key
defaults write "$BUNDLE_ID" "capsLockRemapped" -int 2
defaults write "$BUNDLE_ID" "keyRemap" -int 1

# Allow holding caps to use caps
defaults write "$BUNDLE_ID" "executeQuickHyperKey" -int 1

# Hide menu bar icon (DOES NOT SEEM TO WORK)
# defaults write "$BUNDLE_ID" "showMenuBarIcon" -int 0

# Launch on login
defaults write "$BUNDLE_ID" "launchOnLogin" -int 1

echo "Relaunching ${APP_NAME}..."
open -a "$APP_NAME"

echo "Follow ${APP_NAME} instructions to enable accessibility permissions"