"""Plugin-owned resource registration; server appearance selection is unchanged."""

from pathlib import Path

CATALOG_FILE = Path(__file__).resolve().parent / "assets" / "appearances" / "catalog.json"


def default_bundled_appearance_settings(raw: dict) -> dict:
    """Supply the embedded runtime's optional catalog without writing user config."""
    viewer = raw.get("viewer", {})
    if not isinstance(viewer, dict) or viewer.get("bundled_appearance_catalog_file", "") != "":
        return raw
    return {**raw, "viewer": {**viewer, "bundled_appearance_catalog_file": str(CATALOG_FILE)}}
