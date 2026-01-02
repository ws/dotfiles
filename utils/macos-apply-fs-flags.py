#!/usr/bin/env -S uv run --no-cache
# /// script
# requires-python = ">=3"
# ///
"""
Apply filesystem flags from TOML configuration.

Usage:
    macos-apply-fs-flags.py [path] [-d] [-v]

TOML format:
    description = "Filesystem flags"

    [paths."~/Library"]
    hidden = false

    [paths."~/Private"]
    hidden = true
    uchg = true
"""
import argparse
import os
import stat
import sys
import tomllib
from pathlib import Path

# macOS file flags (from sys/stat.h)
FLAG_BITS = {
    "hidden": stat.UF_HIDDEN,    # 0x8000
    "uchg": stat.UF_IMMUTABLE,   # 0x00000002
    "uappnd": stat.UF_APPEND,    # 0x00000004
    "schg": stat.SF_IMMUTABLE,   # 0x00020000
    "sappnd": stat.SF_APPEND,    # 0x00040000
}


def apply_flags(
    path: Path,
    flags: dict[str, bool],
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """Apply flags to a path. Returns True if changes were made."""
    path = path.expanduser()
    if not path.exists():
        print(f"Warning: {path} does not exist, skipping")
        return False

    current = os.stat(path).st_flags
    new_flags = current

    for flag_name, enabled in flags.items():
        if flag_name not in FLAG_BITS:
            print(f"Warning: Unknown flag '{flag_name}', skipping")
            continue

        bit = FLAG_BITS[flag_name]
        if enabled:
            new_flags |= bit
        else:
            new_flags &= ~bit

    if new_flags == current:
        if verbose:
            print(f"No changes needed for {path}")
        return False

    if dry_run:
        print(f"Would set flags on {path}: {current:#x} -> {new_flags:#x}")
    else:
        if verbose:
            print(f"Setting flags on {path}")
        os.chflags(path, new_flags)

    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply filesystem flags from TOML")
    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=Path(__file__).parent.parent / "macos" / "fs-flags.toml",
        help="TOML config file",
    )
    parser.add_argument("-d", "--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if sys.platform != "darwin":
        print("Error: macOS only", file=sys.stderr)
        sys.exit(1)

    with open(args.path, "rb") as f:
        config = tomllib.load(f)

    paths = config.get("paths", {})
    changes_made = False

    for path_str, flags in paths.items():
        if apply_flags(Path(path_str), flags, args.dry_run, args.verbose):
            changes_made = True

    if args.verbose and not changes_made:
        print("No changes needed")


if __name__ == "__main__":
    main()
