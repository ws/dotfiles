# Dotfiles

Personal dotfiles managed with [chezmoi](https://chezmoi.io). Currently macOS only, but structured for eventual Linux support.

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
├── .chezmoiroot               # Points chezmoi to home/
├── home/                      # Source files → ~/
│   ├── .chezmoiexternal.toml  # External git repos (fzf-tab)
│   ├── .chezmoiignore         # Platform-specific ignores
│   ├── .chezmoiscripts/       # Scripts run on `chezmoi apply`
│   ├── dot_*                  # Files → ~/.*
│   ├── dot_config/            # → ~/.config/
│   └── Library/               # → ~/Library/ (macOS)
├── espanso/                   # Symlink target (shared config)
├── vscode/                    # Symlink target (shared config)
├── macos/                     # Declarative macOS preferences
│   ├── defaults/              # App preferences (TOML)
│   ├── default-apps.toml      # File associations
│   └── fs-flags.toml          # Filesystem flags
└── utils/                     # Python scripts for applying configs
```

### Configuration Data

Create `~/.config/chezmoi/chezmoi.yaml`:

```yaml
data:
  user:
    name: "Your Name"
    email: "you@example.com"
  machine:
    role: "personal"  # or "work"
    type: "laptop"    # or "desktop"
```

Required for templates. The Brewfile and other `.tmpl` files use these values.

### Platform Handling

**The Problem**: VSCode/Cursor/Espanso live in different locations per platform:
- macOS: `~/Library/Application Support/`
- Linux: `~/.config/`

**The Solution**: Source files live at repo root (`vscode/`, `espanso/`), with platform-conditional symlinks in `home/`.

```
vscode/settings.json  ← Single source of truth
                      ↓
macOS:  ~/Library/Application Support/Code/User/settings.json  → symlink
Linux:  ~/.config/Code/User/settings.json                      → symlink
```

**To edit VSCode/Cursor/Espanso configs**: Edit files in `vscode/` or `espanso/`, not the symlinks.

## macOS Preferences

Preferences are defined declaratively in TOML and applied automatically on `chezmoi apply`.

### How It Works

```
macos/defaults/*.toml  →  utils/macos-apply-defaults.py  →  defaults write
```

Each TOML file defines preferences for one app:

```toml
description = "Finder"
kill = ["Finder"]  # Restart after applying

[data."com.apple.finder"]
AppleShowAllFiles = true
FXDefaultSearchScope = "SCcf"
```

### Adding New Preferences

1. Create `macos/defaults/myapp.toml`
2. Find the domain: `defaults domains | tr ',' '\n' | grep -i myapp`
3. Read current settings: `defaults read com.example.myapp`
4. Run `chezmoi apply`

### Debugging

```bash
# Dry-run (see what would change)
python3 utils/macos-apply-defaults.py macos/defaults/ --dry-run -v

# Verbose apply
python3 utils/macos-apply-defaults.py macos/defaults/ -vv
```

## Package Management

### System Packages (Homebrew)

**File**: `home/dot_Brewfile.tmpl`

Organized by platform/role/machine type with chezmoi conditionals.

```bash
brew bundle --global          # Install all
brew bundle cleanup --global  # Remove unlisted
```

### Dev Tools (mise)

**File**: `home/dot_config/mise/config.toml`

```bash
mise install      # Install all tools
mise use -g node  # Add new tool
mise current      # Check versions
```

### External Dependencies

**File**: `home/.chezmoiexternal.toml`

Currently manages fzf-tab. Update with `chezmoi update`.

## Common Tasks

### Add a New macOS Preference

1. Edit or create `macos/defaults/<app>.toml`
2. `chezmoi apply`

### Add a New Dotfile

```bash
chezmoi add ~/.config/some-app/config.yaml
```

### Update VSCode/Cursor Settings

1. Edit `vscode/settings.json` or `vscode/keybindings.json`
2. `chezmoi apply`

### Update Espanso Snippets

Edit `espanso/match/base.yml` or `espanso/match/utils.yml`, then `chezmoi apply`.

> **Note:** Local machine-specific snippets are currently broken.

## Shell Features

### Aliases

- `j` → `z` (zoxide jump)
- `t` → `trash` (safe delete)
- `rm` → disabled (use `del` or `/bin/rm` for hard delete)

### Integrated Tools

- **fzf**: Fuzzy finder (Ctrl+R for history)
- **zoxide**: Smart directory jumping (`z <partial>`)
- **mise**: Dev tool version management
- **eza**: Modern `ls` replacement

## Maintenance

```bash
topgrade  # Updates everything (Homebrew, mise, system, etc.)
```
