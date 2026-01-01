# Dotfiles

Personal dotfiles managed with [chezmoi](https://chezmoi.io). I am only using on MacOS machines currently, but I plan to migrate to Linux eventually, so _theoretically_ everything should be setup for both.

New Mac setup is documented in [MACOS_SETUP.md](MACOS_SETUP.md).

## Quick Reference

```bash
# Apply changes
chezmoi apply

# Edit a file (automatically re-applies)
chezmoi edit ~/.zshrc

# Add new file to tracking
chezmoi add ~/.config/foo/bar.conf

# cd into chezmoi config directory
chezmoi cd

# See what would change
chezmoi diff

# Update external dependencies (fzf-tab)
chezmoi update

# Install packages from Brewfile
brew bundle --global

# Remove Brew packages that are not in Brewfile
brew bundle cleanup --force --global

# One-line updates for everything
topgrade
```

## Architecture

### Directory Structure

```
~/.local/share/chezmoi/
├── .chezmoiexternal.toml      # External git repos (fzf-tab)
├── .chezmoiignore              # Platform-specific ignore patterns
├── dot_*                       # Files → ~/.*
├── Library/                    # macOS app configs
├── dot_config/                 # Linux app configs (.config/)
├── espanso/                    # Shared, symlinked per-platform
├── vscode/                     # Shared VSCode/Cursor settings
├── dot_setup/                  # Setup scripts & docs
└── run_*.sh.tmpl              # Scripts that run on `chezmoi apply`
```

### Configuration Data

Create `~/.config/chezmoi/chezmoi.yaml` with:

```yaml
data:
  user:
    name: "Your Name"
    email: "you@example.com"
  machine:
    role: "personal"  # or "work"
    type: "laptop"    # or "desktop"
```

Required for templates to render. The Brewfile and other `.tmpl` files use these values.

### Platform Handling

**The Problem**: VSCode/Cursor/Espanso live in different locations per platform:
- macOS: `~/Library/Application Support/`
- Linux: `~/.config/`

**The Solution**: Maintain both `Library/` and `dot_config/` directories with platform-conditional symlinks.

```
vscode/settings.json  ← Single source of truth
                      ↓
macOS:  Library/Application Support/Code/User/settings.json  → symlink
Linux:  .config/Code/User/settings.json                      → symlink
```

Each `symlink_*.tmpl` file contains platform-conditional logic:
- macOS version points to source on darwin
- Linux version points to source on linux
- Opposite platform gets ignored via `.chezmoiignore`

**To edit VSCode/Cursor/Espanso configs**: Edit files in `vscode/` or `espanso/`, not the symlinks.

## Package Management

### System Packages (Homebrew)

**File**: `dot_Brewfile.tmpl`

Organized by:
- Common (all platforms)
- macOS only (`{{- if eq .chezmoi.os "darwin" }}`)
- Personal role only (`{{ if eq $role "personal" }}`)
- Laptop only (`{{ if eq .machine.type "laptop" }}`)

```bash
# Install/update all packages
brew bundle --global
```

**To add a package**: Edit `dot_Brewfile.tmpl` in the appropriate section, then `chezmoi apply && brew bundle --global`.

### Dev Tools (mise)

**File**: `dot_config/mise/config.toml`

Manages runtime versions for Node, Python, Ruby, Rust, Go, etc.

```bash
# Install/update all tools
mise install

# Add new tool
mise use -g node@latest

# Check versions
mise current
```

**To add a tool**: Either `mise use -g <tool>` (auto-updates config) or edit `dot_config/mise/config.toml` directly.

### External Dependencies

**File**: `.chezmoiexternal.toml`

Currently manages:
- `fzf-tab` zsh plugin

```bash
# Update external repos
chezmoi update
```

**To add external deps**: Add to `.chezmoiexternal.toml`, see [chezmoi docs](https://www.chezmoi.io/reference/special-files-and-directories/chezmoiexternal-format/).

## Scripts & Automation

### Run Scripts

Scripts prefixed with `run_` execute on `chezmoi apply`:

- `run_set-default-open-apps.sh.tmpl` (macOS) - Sets default apps for file extensions via `duti`

**To add auto-run scripts**: Create `run_*.sh.tmpl` or `run_once_*.sh` (one-time) or `run_onchange_*.sh` (when hash changes).

### Setup Scripts

**Location**: `dot_setup/scripts/macos/`

Manual setup scripts for app preferences (not auto-run):

- `executable_set-macos-prefs.sh` - Finder, Dock, keyboard shortcuts
- `executable_set-rectangle-prefs.sh` - Window manager shortcuts
- `executable_set-maccy-prefs.sh` - Clipboard manager
- `executable_set-hyperkey-prefs.sh` - Caps Lock → Hyper key
- `executable_set-amphetamine-prefs.sh` - Keep-awake app
- `executable_set-cleanshot-prefs.sh` - Screenshot tool

**Why not auto-run?** Some prefs require the app to be closed, or need user review first.

**To run**: `~/.setup/scripts/macos/set-macos-prefs.sh` (chezmoi makes them executable).

### Setup Guide

**Location**: `MACOS_SETUP.md`

Complete fresh Mac setup walkthrough including manual app configuration (Ice, Chrome, VSCode extensions, etc).

## Common Tasks

### Update a System Preference

**Example**: Change a Finder setting

1. Edit `dot_setup/scripts/macos/executable_set-macos-prefs.sh`
2. `chezmoi apply` (makes it executable in `~/.setup/`)
3. Run: `~/.setup/scripts/macos/set-macos-prefs.sh`

### Add a New Homebrew Package

1. Edit `dot_Brewfile.tmpl`, add in appropriate section
2. `chezmoi apply && brew bundle --global`

Or just `brew install foo` then `chezmoi add ~/.Brewfile` to sync.

### Add a New Dotfile

```bash
chezmoi add ~/.config/some-app/config.yaml
# Creates: dot_config/some-app/config.yaml

# Or edit directly
chezmoi edit ~/.config/some-app/config.yaml
```

### Update VSCode/Cursor Settings

1. Edit `vscode/settings.json` or `vscode/keybindings.json`
2. `chezmoi apply` (re-creates symlinks if needed)

VSCode and Cursor share the same configs via symlinks.

### Update Espanso Snippets

**Shared snippets** (tracked in git):
1. Edit `espanso/match/base.yml` or `espanso/match/utils.yml`
2. `chezmoi apply`
3. Espanso auto-reloads

**Local/machine-specific snippets** (not tracked):
1. Create `~/espanso-local.yml` if it doesn't exist (see `espanso/espanso-local.yml.example`)
2. Add your work/personal specific snippets
3. Espanso auto-reloads

The local file is imported by `base.yml` but gitignored, so you can have different snippets on each machine (work vs personal).

### Change Shell Configuration

```bash
chezmoi edit ~/.zshrc
# Auto-applies, reload with: source ~/.zshrc
```

## Shell Features

### Aliases & Functions

- `j` → `z` (zoxide jump, muscle memory from autojump)
- `t` → `trash` (safe delete)
- `del` or `/bin/rm` → hard delete (use sparingly)
- `rm` → disabled (prevents accidents)

### Integrated Tools

- **fzf**: Fuzzy finder for history (Ctrl+R), completion
- **zoxide**: Smart directory jumping (`z <partial-name>`)
- **mise**: Dev tool version management
- **eza**: Modern `ls` replacement

### Environment

- Editor: `code -w` (VSCode, wait mode)
- Visual: `code`
- SSH sessions: `nano`

## Maintenance

### Keep Everything Updated

```bash
topgrade
```

This updates:
- Homebrew packages (formulae and casks)
- mise tools
- System software
- And more

Config: `dot_config/topgrade.toml` (disables chezmoi self-update since it's Brew-managed).

### Sync Changes Back

After editing files directly in `~`:

```bash
chezmoi re-add
# Reviews which tracked files changed, adds them back
```

Or manually:
```bash
chezmoi add ~/.zshrc
```