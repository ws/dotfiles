#!/bin/bash
set -euo pipefail

# Move and resize windows
# https://rectangleapp.com/

APP_NAME="Rectangle"
BUNDLE_ID="com.knollsoft.Rectangle"

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

# Hide menu bar icon (DOES NOT SEEM TO WORK)
# defaults write "$BUNDLE_ID" "showMenuBarIcon" -int 0

# Hyperkey + left arrow = Left half
defaults write "$BUNDLE_ID" "leftHalf" -dict "keyCode" -int 123 "modifierFlags" -int 1966080

# Hyperkey + right arrow = Right half
defaults write "$BUNDLE_ID" "rightHalf" -dict "keyCode" -int 124 "modifierFlags" -int 1966080

# Hyperkey + up arrow = Top half
defaults write "$BUNDLE_ID" "topHalf" -dict "keyCode" -int 125 "modifierFlags" -int 1966080

# Hyperkey + down arrow = Bottom half
defaults write "$BUNDLE_ID" "bottomHalf" -dict "keyCode" -int 126 "modifierFlags" -int 1966080

# Hyperkey + F = Maximize window
defaults write "$BUNDLE_ID" "maximize" -dict "keyCode" -int 3 "modifierFlags" -int 1966080

echo "Relaunching ${APP_NAME}..."
open -a "$APP_NAME"

echo "Follow ${APP_NAME} instructions to enable accessibility permissions"