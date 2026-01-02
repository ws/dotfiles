#!/usr/bin/python3
# /// script
# requires-python = ">=3.11"
# ///
"""
Apply macOS defaults from TOML configuration files.

Usage:
    macos-apply-defaults.py [path] [-d] [-v] [-e N]

Arguments:
    path              TOML file or directory containing TOML files (default: script directory)

Options:
    -d, --dry-run     Show what would be done without making changes
    -v, --verbose     Increase verbosity (use -vv or -vvv for more)
    -e N, --exit-code N   Exit with code N if changes were made

Examples:
    # Apply all defaults from TOML files in a directory
    ./macos-apply-defaults.py ~/defaults/

    # Preview changes without applying
    ./macos-apply-defaults.py ~/defaults/ --dry-run

    # Apply a single config file with verbose output
    ./macos-apply-defaults.py ~/defaults/finder.toml -vv

    # Use in scripts: exit 1 if changes were made (useful for chezmoi run_onchange)
    ./macos-apply-defaults.py ~/defaults/ -e 1

TOML format:
    description = "What this config does"
    current_host = false  # true for ByHost preferences
    sudo = false          # true if root access needed
    kill = ["Finder"]     # processes to restart after changes

    [data.com.apple.finder]
    ShowPathbar = true
    ShowStatusBar = true

    # Use "!" to clear existing dict values
    [data.com.apple.dock]
    "!" = true
    orientation = "left"

    # Use "..." in arrays to preserve existing items
    [data.com.apple.dock]
    persistent-apps = ["...", { tile-data = { file-label = "Terminal" } }]

Based on https://github.com/jbarnette/macos-defaults (itself based on https://github.com/gibfahn/up-rs).
Creates backups before changes and removes them after successful apply.
"""
import argparse
import plistlib
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any


def log(message: str, *, level: str = "info", dry_run: bool = False, verbosity: int = 0) -> None:
    """Log messages based on verbosity. Levels: info (0), debug (1), trace (2+)."""
    min_verbosity = {"info": 0, "debug": 1, "trace": 2}.get(level, 0)
    if verbosity < min_verbosity:
        return
    prefix = "DRY RUN: " if dry_run else ""
    print(f"{prefix}{message}")


def _get_hardware_uuid() -> str:
    """Get the hardware UUID for ByHost preferences."""
    try:
        result = subprocess.run(
            ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in result.stdout.split("\n"):
            if "IOPlatformUUID" in line:
                return line.split('"')[3]
    except Exception:
        pass
    return "UNKNOWN"

# Globals are bad but if your hardware UUID is mutable you've got bigger problems
HARDWARE_UUID = _get_hardware_uuid()

# Cache for sandboxed path existence checks (domain -> exists)
_sandboxed_cache: dict[str, bool] = {}

def sudo_read_bytes(path: Path, count: int) -> bytes:
    """Read bytes from a file using sudo."""
    result = subprocess.run(
        ["sudo", "head", "-c", str(count), str(path)],
        capture_output=True,
        check=True,
    )
    return result.stdout


def sudo_read_plist(path: Path) -> dict[str, Any]:
    """Read and parse a plist file using sudo."""
    result = subprocess.run(
        ["sudo", "plutil", "-convert", "xml1", "-o", "-", str(path)],
        capture_output=True,
        check=True,
    )
    return plistlib.loads(result.stdout)


def sudo_copy(src: Path, dst: Path) -> None:
    """Copy a file using sudo, preserving attributes."""
    subprocess.run(["sudo", "cp", "-p", str(src), str(dst)], check=True)


def sudo_move(src: Path, dst: Path) -> None:
    """Move a file using sudo."""
    subprocess.run(["sudo", "mv", str(src), str(dst)], check=True)


def sudo_remove(path: Path) -> None:
    """Remove a file using sudo."""
    subprocess.run(["sudo", "rm", str(path)], check=True)

def get_plist_path(domain: str, current_host: bool = False) -> Path:
    """Get the path to a plist file for a given domain."""
    home = Path.home()

    # Handle full paths (absolute paths or ending in .plist)
    if domain.startswith("/"):
        path = Path(domain)
        return path if path.suffix == ".plist" else path.with_suffix(".plist")
    if domain.endswith(".plist"):
        return Path(domain).expanduser()

    # Handle current_host (ByHost preferences)
    if current_host:
        if domain in ("NSGlobalDomain", "-g"):
            return home / f"Library/Preferences/ByHost/.GlobalPreferences.{HARDWARE_UUID}.plist"
        return home / f"Library/Preferences/ByHost/{domain}.{HARDWARE_UUID}.plist"

    # Handle global domain
    if domain in ("NSGlobalDomain", "-g"):
        return home / "Library/Preferences/.GlobalPreferences.plist"

    # Check for sandboxed app first (cached to avoid repeated exists() syscalls)
    if domain not in _sandboxed_cache:
        sandboxed_path = home / f"Library/Containers/{domain}/Data/Library/Preferences/{domain}.plist"
        _sandboxed_cache[domain] = sandboxed_path.exists()

    if _sandboxed_cache[domain]:
        return home / f"Library/Containers/{domain}/Data/Library/Preferences/{domain}.plist"

    # Standard preferences location
    return home / f"Library/Preferences/{domain}.plist"


def is_binary_plist(path: Path, use_sudo: bool = False) -> bool:
    """Check if a plist file is in binary format."""
    if not path.exists():
        return True  # Default to binary for new files

    try:
        if use_sudo:
            return sudo_read_bytes(path, 8) == b"bplist00"
        with open(path, "rb") as f:
            return f.read(8) == b"bplist00"
    except Exception:
        return True


def read_plist(path: Path, use_sudo: bool = False, verbosity: int = 0) -> dict[str, Any]:
    """Read a plist file (auto-detects binary/XML format)."""
    if not path.exists():
        return {}

    try:
        if use_sudo:
            return sudo_read_plist(path)
        with open(path, "rb") as f:
            return plistlib.load(f)
    except Exception as e:
        log(f"Warning: Failed to read {path}: {e}", level="debug", verbosity=verbosity)
        return {}


def write_plist(
    path: Path,
    data: dict[str, Any],
    use_sudo: bool = False,
    dry_run: bool = False,
    verbosity: int = 0,
) -> Path | None:
    """Write a plist file, preserving original format. Returns backup path if created."""
    if dry_run:
        log(f"Would write to {path}", dry_run=True, verbosity=verbosity)
        return None

    # Create parent directory if needed
    if not use_sudo:
        path.parent.mkdir(parents=True, exist_ok=True)

    # Determine format
    fmt = plistlib.FMT_BINARY if is_binary_plist(path, use_sudo) else plistlib.FMT_XML

    # Create backup before writing
    backup_path = path.with_suffix(path.suffix + ".prev")
    if path.exists():
        if use_sudo:
            sudo_copy(path, backup_path)
        else:
            shutil.copy2(path, backup_path)
        log(f"Backed up {path}", level="debug", verbosity=verbosity)

    def write_with_sudo():
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tf:
            plistlib.dump(data, tf, fmt=fmt)
            temp_path = Path(tf.name)
        try:
            sudo_move(temp_path, path)
            log(f"Wrote {path} with sudo", level="debug", verbosity=verbosity)
        except subprocess.CalledProcessError as e:
            log(f"Error: Failed to write {path} with sudo: {e}", verbosity=verbosity)
            temp_path.unlink()
            raise

    if use_sudo:
        write_with_sudo()
        return backup_path if path.exists() else None

    try:
        with open(path, "wb") as f:
            plistlib.dump(data, f, fmt=fmt)
        log(f"Wrote {path}", level="debug", verbosity=verbosity)
    except PermissionError:
        log(f"Permission denied writing {path}, trying with sudo...", verbosity=verbosity)
        write_with_sudo()

    return backup_path if backup_path.exists() else None


def merge_values(old_value: Any, new_value: Any) -> Any:
    """
    Smart merge of values supporting special operators:
    - "!" in dict: clear old dict and use only new values
    - "..." in list: replace with old list values (no duplicates)

    Returns the original old_value object (by identity) when no changes are needed,
    enabling O(1) identity checks instead of O(n) equality checks.
    """
    # Handle dictionaries
    if isinstance(new_value, dict) and isinstance(old_value, dict):
        # Check for "!" operator (clear existing)
        if "!" in new_value:
            return {k: v for k, v in new_value.items() if k != "!"}

        # Otherwise merge recursively, tracking if anything changed
        changed = False
        result = old_value.copy()
        for key, val in new_value.items():
            if key in result:
                merged = merge_values(result[key], val)
                if merged is not result[key]:
                    result[key] = merged
                    changed = True
            else:
                result[key] = val
                changed = True
        return result if changed else old_value

    # Handle arrays with "..." operator
    if isinstance(new_value, list):
        result: list[Any] = []
        seen: set[str] = set()

        def item_key(item: Any) -> str:
            if isinstance(item, dict):
                return str(sorted(item.items()))
            return str(item)

        # Track what's already in old_value
        old_keys: set[str] = set()
        if isinstance(old_value, list):
            for item in old_value:
                key = item_key(item)
                seen.add(key)
                old_keys.add(key)

        # Process new values
        changed = False
        for item in new_value:
            if item == "...":
                # Replace "..." with old values
                if isinstance(old_value, list):
                    for old_item in old_value:
                        if old_item not in result:
                            result.append(old_item)
            else:
                key = item_key(item)
                if key not in seen:
                    result.append(item)
                    seen.add(key)
                    changed = True

        # Check if result matches old_value exactly
        if not changed and isinstance(old_value, list) and len(result) == len(old_value):
            return old_value
        return result

    # Scalar: return original if equal
    if old_value == new_value:
        return old_value
    return new_value


def apply_defaults(
    domain: str,
    values: dict[str, Any],
    current_host: bool = False,
    use_sudo: bool = False,
    dry_run: bool = False,
    verbosity: int = 0,
) -> tuple[bool, Path | None]:
    """Apply defaults for a single domain. Returns (changed, backup_path)."""
    plist_path = get_plist_path(domain, current_host)

    old_data = read_plist(plist_path, use_sudo, verbosity)
    new_data = merge_values(old_data, values)

    # O(1) identity check: merge_values returns original object when unchanged
    if new_data is old_data:
        log(f"No changes needed for {domain}", level="debug", dry_run=dry_run, verbosity=verbosity)
        return False, None

    log(f"Applying changes to {domain}", dry_run=dry_run, verbosity=verbosity)
    backup = write_plist(plist_path, new_data, use_sudo, dry_run, verbosity)
    return True, backup


def kill_processes(processes: set[str], dry_run: bool = False, verbosity: int = 0) -> None:
    """Kill all specified processes."""
    for process in sorted(processes):
        if dry_run:
            log(f"Would kill process: {process}", dry_run=True, verbosity=verbosity)
        else:
            try:
                subprocess.run(["killall", process], stderr=subprocess.DEVNULL, check=False)
                log(f"Restarted {process}", level="debug", verbosity=verbosity)
            except Exception as e:
                log(f"Warning: Failed to kill {process}: {e}", level="debug", verbosity=verbosity)


def cleanup_backups(backups: list[Path], verbosity: int = 0) -> None:
    """Remove backup files after successful apply."""
    for backup_path in backups:
        try:
            backup_path.unlink()
            log(f"Removed backup {backup_path}", level="debug", verbosity=verbosity)
        except PermissionError:
            try:
                sudo_remove(backup_path)
                log(f"Removed backup {backup_path} with sudo", level="debug", verbosity=verbosity)
            except Exception as e:
                log(f"Warning: Failed to remove backup {backup_path}: {e}", level="debug", verbosity=verbosity)
        except Exception as e:
            log(f"Warning: Failed to remove backup {backup_path}: {e}", level="debug", verbosity=verbosity)


def process_toml_file(
    toml_path: Path,
    dry_run: bool = False,
    verbosity: int = 0,
) -> tuple[bool, set[str], list[Path]]:
    """Process a single TOML file. Returns (changes_made, processes_to_kill, backups)."""
    log(f"Processing {toml_path.name}...", level="debug", dry_run=dry_run, verbosity=verbosity)

    try:
        with open(toml_path, "rb") as f:
            doc = tomllib.load(f)
    except Exception as e:
        log(f"Error reading {toml_path}: {e}", dry_run=dry_run, verbosity=verbosity)
        return False, set(), []

    # Early exit if no data to process
    data = doc.get("data", {})
    if not doc or not data:
        return False, set(), []

    description = doc.get("description", "")
    if description:
        log(f"  {description}", level="debug", dry_run=dry_run, verbosity=verbosity)

    current_host = doc.get("current_host", False)
    use_sudo = doc.get("sudo", False)
    kill_list = doc.get("kill", [])

    changes_in_file = False
    backups: list[Path] = []

    for domain, values in data.items():
        changed, backup = apply_defaults(domain, values, current_host, use_sudo, dry_run, verbosity)
        if changed:
            changes_in_file = True
        if backup:
            backups.append(backup)

    # Only return kills if this file made changes
    processes = set(kill_list) if changes_in_file else set()
    return changes_in_file, processes, backups


def process_path(
    path: Path,
    dry_run: bool = False,
    verbosity: int = 0,
) -> tuple[bool, set[str], list[Path]]:
    """Process a file or directory. Returns (changes_made, processes_to_kill, backups)."""
    all_changes = False
    all_processes: set[str] = set()
    all_backups: list[Path] = []

    if path.is_file():
        if path.suffix == ".toml":
            changes, processes, backups = process_toml_file(path, dry_run, verbosity)
            all_changes = changes
            all_processes = processes
            all_backups = backups
    elif path.is_dir():
        for toml_file in sorted(path.glob("*.toml")):
            changes, processes, backups = process_toml_file(toml_file, dry_run, verbosity)
            if changes:
                all_changes = True
            all_processes.update(processes)
            all_backups.extend(backups)
    else:
        log(f"Error: {path} not found", dry_run=dry_run, verbosity=verbosity)
        sys.exit(1)

    return all_changes, all_processes, all_backups


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply macOS defaults from TOML configuration files"
    )
    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=Path(__file__).parent,
        help="TOML file or directory (default: script directory)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Verbose output (repeat for more: -v, -vv, -vvv)",
    )
    parser.add_argument(
        "-e",
        "--exit-code",
        type=int,
        metavar="N",
        help="Exit with N if changes were made",
    )

    args = parser.parse_args()

    if sys.platform != "darwin":
        print("Error: This script only works on macOS", file=sys.stderr)
        sys.exit(1)

    changes_made, processes_to_kill, backups = process_path(args.path, args.dry_run, args.verbose)

    if changes_made:
        kill_processes(processes_to_kill, args.dry_run, args.verbose)
        # Restart cfprefsd to ensure changes take effect
        if args.dry_run:
            log("Would restart cfprefsd", dry_run=True, verbosity=args.verbose)
        else:
            subprocess.run(["killall", "cfprefsd"], stderr=subprocess.DEVNULL, check=False)
            log("Restarted cfprefsd", level="debug", verbosity=args.verbose)

    cleanup_backups(backups, args.verbose)

    if changes_made and args.exit_code is not None:
        sys.exit(args.exit_code)

    sys.exit(0)


if __name__ == "__main__":
    main()