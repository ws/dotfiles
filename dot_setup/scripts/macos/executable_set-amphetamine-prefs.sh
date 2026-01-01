#!/bin/bash
set -euo pipefail

# Keep your Mac awake
# https://apps.apple.com/us/app/amphetamine/id937984704

APP_NAME="Amphetamine"
BUNDLE_ID="com.if.Amphetamine"

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

# Hide welcome window
defaults write "$BUNDLE_ID" "Show Welcome Window" -int 0

# Set icon style
defaults write "$BUNDLE_ID" "Icon Style" -int 6
defaults write "$BUNDLE_ID" "Lower Icon Opacity" -int 1

# No Dock icon
defaults write "$BUNDLE_ID" "Hide Dock Icon" -int 1

# Relaunch if it was running before
if $was_running; then
    echo "Relaunching ${APP_NAME}..."
    open -a "$APP_NAME"
fi