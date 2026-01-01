#!/bin/bash

# Bail if not running on macOS
if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "Error: This script only runs on macOS" >&2
    exit 1
fi

# Finder

# Show hidden files
defaults write com.apple.finder AppleShowAllFiles -bool true

# Always show file extensions
defaults write NSGlobalDomain AppleShowAllExtensions -bool true

# Show ~/Library folder
chflags nohidden ~/Library

# Disable .DS_Store on network and USB drives
defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true

# Default to searching current folder
defaults write com.apple.finder "FXDefaultSearchScope" -string "SCcf"

# Don't nag about changing a file's extension
defaults write com.apple.finder "FXEnableExtensionChangeWarning" -bool false

# Save dialog should open to disk, not iCloud
defaults write NSGlobalDomain "NSDocumentSaveNewDocumentsToCloud" -bool "false"

killall Finder

# Dock

# Bottom
defaults write com.apple.dock "orientation" -string "bottom"

# Auto-hide
defaults write com.apple.dock autohide -bool true

# Fast(ish) animations
defaults write com.apple.dock autohide-time-modifier -float 0.5
defaults write com.apple.dock autohide-delay -float 0

killall Dock

# Keyboard Shortcuts

# Disable screenshot shortcuts (I use CleanShot X)
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 28  '{ enabled = 0; }'  # ⌘⇧3 full screen
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 29  '{ enabled = 0; }'  # ⌘⇧4 selection
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 30  '{ enabled = 0; }'  # ⌘⇧3 → clipboard
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 31  '{ enabled = 0; }'  # ⌘⇧4 → clipboard
defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 184 '{ enabled = 0; }'  # ⌘⇧5 toolbar

killall SystemUIServer