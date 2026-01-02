# Fresh Mac Setup Guide

Most macOS and app preferences are now applied automatically via `chezmoi apply`. This guide covers the full setup process, including the manual steps that can't be automated.

Expect to accept accessibility and screen recording prompts along the way.

---

## Overview

| Phase | What happens |
|-------|--------------|
| 1. Xcode | Start the download (it's huge) |
| 2. Homebrew | Install package manager |
| 3. Chezmoi | Configure and initialize dotfiles |
| 4. Brew bundle | Install all apps |
| 5. Apply dotfiles | `chezmoi apply` (auto-configures most prefs) |
| 6. Manual setup | Permissions, login items, app-specific |
| 7. Dev runtimes | mise install |
| 8. xcode-select | Configure after Xcode finishes |
| 9. Final checks | Verify everything works |

---

## 1. Start Xcode Download

Xcode is ~12GB. Start this first so it downloads in the background.

```bash
open "https://apps.apple.com/us/app/xcode/id497799835"
```

You'll configure xcode-select at the end (step 9) after it finishes installing.

---

## 2. Install Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

This also downloads and installs Xcode Command Line Tools and accepts the license.

**Temporarily add Homebrew to PATH:**

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

**Verify:**

```bash
brew --version
```

---

## 3. Configure and Initialize Chezmoi

### Install Chezmoi

```bash
brew install chezmoi
```

### Create Machine Config

Templates require this before the first apply.

```bash
mkdir -p ~/.config/chezmoi
cat > ~/.config/chezmoi/chezmoi.yaml << 'EOF'
data:
  user:
    name: "Your Name"
    email: "you@example.com"
  machine:
    role: "personal"  # or "work"
    type: "laptop"    # or "desktop"
EOF
```

### Initialize

```bash
chezmoi init <your-dotfiles-repo-url>
# e.g.: chezmoi init git@github.com:username/dotfiles.git
```

---

## 4. Install All Packages

```bash
brew bundle --global --verbose
```

This takes a while.

You will have to babysit to type in your password several times, which is apparently [intended functionality](https://github.com/Homebrew/brew/issues/1293).

If you have to exit midway through, Brew's cache will get messed up and indefinitely hang on future runs (hangs on "verifying" for random packages forever). You can clear with

```bash
brew cleanup --prune=all
```

and try again. It's not a bad idea to run that command once you're finished installing everything, you can reclaim several gigs in log files about just installs.

---

## 5. Apply Dotfiles

```bash
chezmoi apply
```

This does a lot of work automatically:

- Installs shell plugins (fzf-tab via `.chezmoiexternal`)
- **Applies macOS system preferences** (Finder, Dock, keyboard shortcuts)
- **Applies app preferences** (Hyperkey, Rectangle, Maccy, CleanShot, Amphetamine)
- **Sets default apps** for file types and URLs (via duti)
- **Sets filesystem flags** (e.g., unhides ~/Library)

You may see a warning about `duti` not being installed if you run this before step 4. That's fine - just run `chezmoi apply` again after brew bundle.

### How It Works

Preferences are defined declaratively in TOML files under `macos/defaults/`. Python scripts in `utils/` read these configs and apply them via `defaults write`. Chezmoi orchestrates everything via scripts in `.chezmoiscripts/macos/`.

To customize settings, edit the TOML files in `macos/`:

```
macos/
├── defaults/
│   ├── finder.toml      # Finder behavior
│   ├── dock.toml        # Dock settings
│   ├── hotkeys.toml     # Keyboard shortcuts
│   ├── hyperkey.toml    # Hyperkey config
│   ├── rectangle.toml   # Window management
│   ├── maccy.toml       # Clipboard manager
│   ├── cleanshot.toml   # Screenshot tool
│   ├── amphetamine.toml # Keep-awake utility
│   └── general.toml     # System-wide settings
├── default-apps.toml    # File associations
└── fs-flags.toml        # Filesystem attributes
```

---

## 6. Manual App Setup

These steps can't be automated due to macOS restrictions or app limitations.

### Accessibility Permissions

Grant accessibility access when prompted for:
- **Hyperkey** - needed for Caps Lock remapping
- **Rectangle** - needed for window management
- **Espanso** - needed for text expansion

### Screen Recording Permission

Grant screen recording access when prompted for:
- **CleanShot** - needed for screenshots

### Rectangle First Launch

When Rectangle first launches:
1. Select **"Default keyboard shortcuts"** when prompted
2. Select **"Disable macOS tiling"** when prompted

### Login Items

Verify these are set to launch on login (System Settings → General → Login Items):

| App | How to Enable |
|-----|---------------|
| Hyperkey | Settings → "Open on login" |
| Rectangle | Settings → "Open on login" |
| Maccy | Preferences → General → "Launch at login" |
| CleanShot | Prompts on first run |
| Ice | Settings → General → "Launch at login" |
| Espanso | Add manually to Login Items |
| Amphetamine | Add manually (laptop only) |

### Menu Bar Icons

Some apps don't respect `defaults write` for hiding menu bar icons. Set manually:
- Hyperkey → Settings → "Hide menu bar icon"
- Rectangle → Settings → "Hide menu bar icon"

### Ice (Menu Bar Organizer)

1. Open Ice.app and follow setup prompts
2. General → Set **"Ice icon"** to **Ellipsis**
3. General → Enable **"Use the Ice Bar"**

### Maccy

1. Preferences → Appearance → Set **"Popup at"** preference
2. System Settings → Notifications → Enable for Maccy

### Chrome

**Personal devices:** Sign in to Google account (syncs everything)

**Work devices:** Install extensions manually:
- [1Password](https://chromewebstore.google.com/detail/1password-%E2%80%93-password-mana/aeblfdkhhhdcdjpifhhbdiojplfjncoa)
- [Picture-in-picture](https://chromewebstore.google.com/detail/picture-in-picture-extens/hkgfoiooedgoejojocmhlaklaeopbecg)
- [uBlock Origin Lite](https://chromewebstore.google.com/detail/ublock-origin-lite/ddkjiahejlhfcafbddmgiahcphecmpfh)

### VSCode / Cursor Extensions

Settings and keybindings are managed by chezmoi. Extensions need manual install.

```bash
# List extensions from another machine
code --list-extensions
cursor --list-extensions

# Install
code --install-extension <extension-id>
cursor --install-extension <extension-id>
```

### Espanso

Should work automatically via chezmoi symlinks.

> **Note:** Local machine-specific snippets (`~/espanso-local.yml`) are currently broken due to espanso not expanding `~` or `$HOME` in imports when reading from a symlinked config.

---

## 7. Install Dev Runtimes

```bash
mise install
```

**Verify:**

```bash
mise current
node --version
python --version
```

---

## 8. Configure xcode-select

By now Xcode.app should have finished downloading and installing.

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

**Verify:**

```bash
xcode-select -p
# Should show: /Applications/Xcode.app/Contents/Developer
```

If Xcode isn't installed yet, skip this and come back later.

---

## 9. Final Checks

### Restart Terminal

```bash
exec zsh
```

### Verify Tools

```bash
# Shell tools
which fzf zoxide eza

# Dev tools
node --version && python --version && bun --version

# Chezmoi
chezmoi doctor
```

---

## Troubleshooting

### Preferences Not Applied

Run with verbose output to see what's happening:

```bash
python3 ~/.local/share/chezmoi/utils/macos-apply-defaults.py ~/.local/share/chezmoi/macos/defaults/ -vv
```

Dry-run mode shows what would change without applying:

```bash
python3 ~/.local/share/chezmoi/utils/macos-apply-defaults.py ~/.local/share/chezmoi/macos/defaults/ --dry-run -v
```

### Default Apps Not Set

Ensure `duti` is installed:

```bash
brew install duti
chezmoi apply
```

### App Settings Reset

Some apps (especially sandboxed ones) may reset preferences on update. Re-run:

```bash
chezmoi apply
```

### Adding New App Preferences

Create a new TOML file in `macos/defaults/`:

```toml
description = "My App"
kill = ["MyApp"]  # Process to restart after changes

[data."com.example.myapp"]
SomeSetting = true
AnotherSetting = "value"
```

Find the domain name with:

```bash
defaults domains | tr ',' '\n' | grep -i myapp
```

Read current settings with:

```bash
defaults read com.example.myapp
```
