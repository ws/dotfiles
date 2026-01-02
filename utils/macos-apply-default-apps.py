#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
Apply default application handlers for file extensions and URL schemes on macOS.

Usage:
    macos-apply-default-apps.py [config] [-d] [-v]

Arguments:
    config            TOML config file (default: ../macos/default-apps.toml)

Options:
    -d, --dry-run     Show what would be done without making changes
    -v, --verbose     Increase verbosity (use -vv for more)

Examples:
    # Apply default apps from config
    ./macos-apply-default-apps.py

    # Preview changes
    ./macos-apply-default-apps.py --dry-run

    # Use a different config file
    ./macos-apply-default-apps.py ~/my-apps.toml -v

TOML format:
    [apps.vscode]
    name = "VS Code"
    bundle_id = "com.microsoft.VSCode"
    extensions = ["py", "js", "ts", "json", "md"]

    [apps.firefox]
    name = "Firefox"
    bundle_id = "org.mozilla.firefox"
    urls = ["http", "https"]

Requires: duti (brew install duti)
"""
import argparse
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import tomllib


def log(message: str, *, level: str = "info", dry_run: bool = False, verbosity: int = 0) -> None:
    """Log messages based on verbosity."""
    min_verbosity = {"info": 0, "debug": 1, "trace": 2}.get(level, 0)
    if verbosity < min_verbosity:
        return
    prefix = "DRY RUN: " if dry_run else ""
    print(f"{prefix}{message}")


def load_url_handlers_cache() -> dict[str, str]:
    """Load all URL handlers from Launch Services plist (called once, cached)."""
    plist_path = Path.home() / "Library/Preferences/com.apple.LaunchServices/com.apple.launchservices.secure.plist"
    if not plist_path.exists():
        return {}

    try:
        result = subprocess.run(
            ["plutil", "-convert", "json", "-o", "-", str(plist_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        return {
            handler.get("LSHandlerURLScheme", "").lower(): handler.get("LSHandlerRoleAll", "")
            for handler in data.get("LSHandlers", [])
            if handler.get("LSHandlerURLScheme")
        }
    except Exception:
        return {}


def get_current_url_handler(scheme: str, cache: dict[str, str]) -> str | None:
    """Get the current handler for a URL scheme from cached data."""
    return cache.get(scheme.lower())


def get_current_extension_handler(ext: str) -> str | None:
    """Get the current handler for a file extension using duti."""
    try:
        result = subprocess.run(
            ["duti", "-x", ext],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 3:
                return lines[2]  # Bundle ID is on line 3
    except Exception:
        pass
    return None


def set_extension_handler(
    ext: str,
    bundle_id: str,
    dry_run: bool = False,
    verbosity: int = 0,
) -> bool:
    """Set the handler for a file extension."""
    if dry_run:
        log(f"Would set .{ext} → {bundle_id}", dry_run=True, verbosity=verbosity)
        return True

    result = subprocess.run(
        ["duti", "-s", bundle_id, f".{ext}", "all"],
        capture_output=True,
    )
    return result.returncode == 0


def set_url_handler(
    scheme: str,
    bundle_id: str,
    dry_run: bool = False,
    verbosity: int = 0,
) -> bool:
    """Set the handler for a URL scheme."""
    if dry_run:
        log(f"Would set {scheme}:// → {bundle_id}", dry_run=True, verbosity=verbosity)
        return True

    result = subprocess.run(
        ["duti", "-s", bundle_id, scheme, "viewer"],
        capture_output=True,
    )
    return result.returncode == 0


def load_config(path: Path) -> dict[str, Any]:
    """Load and validate the TOML configuration."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def apply_config(
    config: dict[str, Any],
    dry_run: bool = False,
    verbosity: int = 0,
) -> bool:
    """Apply the configuration. Returns True if any changes were made."""
    apps_config = config.get("apps", {})

    # Build mappings from the new app-centric structure
    ext_to_app: dict[str, str] = {}
    url_to_app: dict[str, str] = {}
    names: dict[str, str] = {}

    for app_def in apps_config.values():
        bundle_id = app_def.get("bundle_id", "")
        if not bundle_id:
            continue

        names[bundle_id] = app_def.get("name", bundle_id)

        for ext in app_def.get("extensions", []):
            ext_to_app[ext] = bundle_id

        for scheme in app_def.get("urls", []):
            url_to_app[scheme] = bundle_id

    # Load URL handlers once (fast, single plist read)
    url_handlers_cache = load_url_handlers_cache()
    current_handlers: dict[str, str | None] = {
        f"url:{scheme}": get_current_url_handler(scheme, url_handlers_cache)
        for scheme in url_to_app
    }

    # Check extension handlers in parallel (each requires a subprocess call)
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {
            executor.submit(get_current_extension_handler, ext): ext
            for ext in ext_to_app
        }
        for future in futures:
            ext = futures[future]
            try:
                current_handlers[f"ext:{ext}"] = future.result()
            except Exception:
                current_handlers[f"ext:{ext}"] = None

    # Track changes by app
    changed_by_app: dict[str, list[str]] = {}
    failed: list[str] = []

    # Apply URL handlers
    for scheme, bundle_id in url_to_app.items():
        current = current_handlers.get(f"url:{scheme}", "")
        if current and current.lower() == bundle_id.lower():
            log(f"URL scheme {scheme}:// already handled by {bundle_id}", level="debug", verbosity=verbosity)
            continue

        if set_url_handler(scheme, bundle_id, dry_run, verbosity):
            changed_by_app.setdefault(bundle_id, []).append(f"{scheme}://")
        else:
            app_name = names.get(bundle_id, bundle_id)
            failed.append(f"Failed to set {app_name} as handler for {scheme}://")

    # Apply extension handlers
    for ext, bundle_id in ext_to_app.items():
        current = current_handlers.get(f"ext:{ext}", "")
        if current == bundle_id:
            log(f"Extension .{ext} already handled by {bundle_id}", level="debug", verbosity=verbosity)
            continue

        if set_extension_handler(ext, bundle_id, dry_run, verbosity):
            changed_by_app.setdefault(bundle_id, []).append(f".{ext}")
        else:
            app_name = names.get(bundle_id, bundle_id)
            failed.append(f"Failed to set {app_name} as handler for .{ext}")

    # Report failures
    for msg in failed:
        log(f"⚠️  {msg}", verbosity=verbosity)

    # Report successes
    for bundle_id, items in sorted(changed_by_app.items()):
        app_name = names.get(bundle_id, bundle_id)
        # Separate URLs and extensions
        urls = [i for i in items if i.endswith("://")]
        exts = [i for i in items if i.startswith(".")]

        if urls:
            log(f"✅ Set {app_name} as the default browser", verbosity=verbosity)

        if exts:
            log(f"✅ Set {app_name} as the default for:", verbosity=verbosity)
            for ext in sorted(exts):
                log(f"   • {ext}", verbosity=verbosity)

    return bool(changed_by_app)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply default application handlers from TOML configuration"
    )
    parser.add_argument(
        "config",
        type=Path,
        nargs="?",
        default=Path(__file__).parent.parent / "macos" / "default-apps.toml",
        help="TOML configuration file (default: macos/default-apps.toml)",
    )
    parser.add_argument(
        "-d", "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Verbose output (repeat for more: -v, -vv)",
    )

    args = parser.parse_args()

    if sys.platform != "darwin":
        print("Error: This script only works on macOS", file=sys.stderr)
        sys.exit(1)

    if not shutil.which("duti"):
        print("Skipping setting default apps because duti is not installed. If this is a fresh install, this is expected.")
        sys.exit(0)

    if not args.config.exists():
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    config = load_config(args.config)
    apply_config(config, args.dry_run, args.verbose)


if __name__ == "__main__":
    main()

