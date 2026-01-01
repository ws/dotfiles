#!/bin/bash
set -euo pipefail

# Maccy clipboard manager
# https://maccy.app/

APP_NAME="Maccy"
BUNDLE_ID="org.p0deje.Maccy"

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

# Search mode fuzzy
defaults write "$BUNDLE_ID" "searchMode" -string "fuzzy"

# Set history size of 50
defaults write "$BUNDLE_ID" "historySize" -int 50

open -a "$APP_NAME"

echo '👋 Set General > "Launch at login" preference manually in Maccy preferences'
echo '👋 Set Appearance > "Popup at" preference manually in Maccy preferences'