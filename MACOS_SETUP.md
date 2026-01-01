# Fresh Mac Setup Guide

Some setup steps cannot be reliably run unattended - usually due to macOS restrictions/quirks or apps' reliance on inbuilt sync/cloud mechanisms. This guide walks through everything manually.

Expect to accept a lot of accessibility and screen recording prompts.

---

## Overview

| Phase | What happens |
|-------|--------------|
| 1. Xcode | Start the download (it's huge) |
| 2. Homebrew | Install package manager |
| 3. Chezmoi | Configure and initialize dotfiles |
| 4. Brew bundle | Install all apps |
| 5. 1Password | Sign in, enable CLI |
| 6. macOS prefs | System preferences via script |
| 7. App prefs | Per-app preference scripts |
| 8. Dev runtimes | mise install |
| 9. Manual setup | Ice, Chrome, VSCode extensions |
| 10. xcode-select | Configure after Xcode finishes |
| 11. Final checks | Verify everything works |

---

## 1. Start Xcode Download

Xcode is ~12GB. Start this first so it downloads in the background.

```bash
open "https://apps.apple.com/us/app/xcode/id497799835"
```

You'll configure xcode-select at the end (step 10) after it finishes installing.

---

## 2. Install Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

This also downloads and installs Xcode Command Line Tools and accepts the license.

**Temporarily Add Homebrew to PATH:**

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

First apply chezmoi to get the Brewfile:

```bash
chezmoi apply
```

This will also install [fzf-tab](https://github.com/Aloxaf/fzf-tab) (via .chezmoiexternal)

You may get a warning about `duti` not being installed yet, don't worry about it.

Then install everything:

```bash
brew bundle --global --verbose
```

This takes a while. ☕

You will have to babysit to type in your password several times, which is apparently [intended functionality](https://github.com/Homebrew/brew/issues/1293).

If you have to exit midway through, Brew's cache will get messed up and indefinitely hang on future runs (hangs on "verifying" for random packages forever). You can clear with

```bash
brew cleanup --prune=all
```

and try again. It's not a bad idea to run that command once you're finished installing everything, you can reclaim several gigs in log files about just installs.

---

## 5. Configure 1Password

This is needed before the CleanShot script (which reads the license key from 1Password).

### Sign In

1. Open **1Password.app**
2. Sign in to your account

### Enable CLI Integration

1. 1Password → Settings → Developer
2. Enable **"Integrate with 1Password CLI"**

See: https://developer.1password.com/docs/cli/get-started/#step-2-turn-on-the-1password-desktop-app-integration

**Verify CLI works:**

```bash
op account get
# Should show your account info
```

---

## 6. macOS System Preferences

```bash
~/.setup/scripts/macos/set-macos-prefs.sh
```

**Sets:**
- **Finder:** Show hidden files, show extensions, show ~/Library, search current folder, no .DS_Store on network/USB
- **Dock:** Bottom, auto-hide, fast animations
- **Keyboard:** Disables default screenshot shortcuts (CleanShot replaces them)

---

## 7. App Preference Scripts

Run these in order (some depend on others).

### 7a. Hyperkey

```bash
~/.setup/scripts/macos/set-hyperkey-prefs.sh
```

**Run this before Rectangle** (Rectangle shortcuts use Hyper key).

**Sets:**
- Caps Lock → Hyper (⌃⌥⌘⇧)
- Hold Caps = actual Caps Lock
- Launch on login
- Hides menu bar icon

Grant accessibility permissions when prompted.

**⚠️ Manual steps required:**
1. Ensure "Open on login" is checked.
2. Check "Hide menu bar icon" (TODO: see why this isn't respecting `defaults write`)

### 7b. Rectangle

```bash
~/.setup/scripts/macos/set-rectangle-prefs.sh
```

**Shortcuts:**
| Shortcut | Action |
|----------|--------|
| `Hyper + ←` | Left half |
| `Hyper + →` | Right half |
| `Hyper + ↑` | Top half |
| `Hyper + ↓` | Bottom half |
| `Hyper + F` | Maximize |

Grant accessibility permissions when prompted.

Select default keyboard shortcuts when prompted (TODO: script this)

Disable MacOS tiling when prompted (TODO: see if I can script this)

**⚠️ Manual steps required:**
1. Ensure General > "Open on login" is checked.
2. Check General > "Hide menu bar icon" (TODO: see why this isn't respecting `defaults write`)

### 7c. Maccy

```bash
~/.setup/scripts/macos/set-maccy-prefs.sh
```

**Sets:**
- Fuzzy search
- 50 item history

**⚠️ Manual steps required:**
1. Open Maccy preferences
2. General → Enable **"Launch at login"**
3. Appearance → Set **"Popup at"** preference
3. Enable notifications in System Preferences

### 7d. CleanShot

```bash
~/.setup/scripts/macos/set-cleanshot-prefs.sh
```

**Requires:** 1Password CLI configured (step 5)

**Sets:**
- License key from 1Password
- Hide desktop icons in screenshots
- Disables analytics
- Accepts EULA

Grant screen recording permissions when prompted.

### 7e. Amphetamine (Laptop Only)

```bash
~/.setup/scripts/macos/set-amphetamine-prefs.sh
```

**Sets:**
- Hides welcome window
- Custom icon style
- No Dock icon

---

## 8. Install Dev Runtimes

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

## 9. Manual App Setup

### Ice (Menu Bar Organizer)

Open Ice.app and follow setup prompts.

**Configure:**
- General → Enable **"Launch at login"**
- General → Set **"Ice icon"** to **Ellipsis**
- General → Enable **"Use the Ice Bar"**

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

**For machine-specific snippets** (not tracked in git):

```bash
cat > ~/espanso-local.yml << 'EOF'
matches:
  - trigger: ":email"
    replace: "you@example.com"
EOF
```

Grant accessibility permissions when prompted.

---

## 10. Configure xcode-select

By now Xcode.app should have finished downloading and installing. You should run

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

for reasons that are not totally clear to me.

**Verify:**

```bash
xcode-select -p
# Should show: /Applications/Xcode.app/Contents/Developer
```

If Xcode isn't installed yet, skip this and come back later.

---

## 11. Final Checks

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

# 1Password CLI
op account get
```

### Launch on Login

Verify these are set to launch on login (search "Login Items & Extensions" in System Preferences):
- ✅ Ice (in app settings)
- ✅ Maccy (in app settings)
- ✅ Hyperkey (script sets this)
- ✅ Rectangle (prompts on first run)
- ✅ CleanShot (prompts on first run)
- ✅ Espanso (manually add)
- ✅ Amphetamine (if laptop)