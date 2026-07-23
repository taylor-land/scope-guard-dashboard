"""JSON-backed Google OAuth scope reference data.

This module keeps the runtime API stable while moving the actual source of
truth into `preprocessing_requirments.json`.
"""

from functools import lru_cache
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "preprocessing_requirments.json"


@lru_cache(maxsize=1)
def _load_data() -> dict:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


_DATA = _load_data()
SERVICE_SCOPES = _DATA["SERVICE_SCOPES"]
SERVICE_SENSITIVITY = _DATA["SERVICE_SENSITIVITY"]
ACCESS_LEVELS = _DATA["ACCESS_LEVELS"]
ONEHOT_COLUMNS = _DATA["ONEHOT_COLUMNS"]

READ_ONLY_HINTS = (
    "readonly",
    "read_only",
    "read-only",
    ".read",
    "admin.reports.audit.readonly",
    "calendar.events.public.readonly",
    "photoslibrary.readonly.appcreateddata",
    "userinfo.email",
    "userinfo.profile",
    "openid",
    "profile",
    "email",
)

WRITE_HINTS = (
    ".write",
    ".upload",
    ".insert",
    ".compose",
    ".delete",
    "messaging",
    "deployments",
    "script.projects",
    "script.deployments",
)


def _infer_access_type(scope: str, entry: dict) -> str:
    if scope in {"openid", "profile", "email"}:
        return "read"
    if any(hint in scope for hint in READ_ONLY_HINTS):
        return "read"
    if any(hint in scope for hint in WRITE_HINTS):
        return "write"
    if scope in {"https://www.googleapis.com/auth/admin.datatransfer"}:
        return "read_write"
    if scope.endswith(".appdata"):
        return "read_write"
    if scope.endswith(".file"):
        return "read_write"
    if scope.endswith(".readonly"):
        return "read"
    if scope.endswith(".readonly"):
        return "read"
    if entry.get("is_admin"):
        return "full_access"
    broad_services = {
        "AdSense",
        "Analytics",
        "Blogger",
        "Calendar",
        "Classroom",
        "Docs",
        "Drive",
        "Fitness",
        "Forms",
        "Firebase",
        "Gmail",
        "Groups",
        "Keep",
        "Photos",
        "Sheets",
        "Slides",
        "Tasks",
        "YouTube",
        "Cloud",
        "Cloud Storage",
        "BigQuery",
        "Compute",
        "Contacts",
    }
    if entry.get("service") in broad_services:
        return "full_access"
    return "read_write"


SCOPE_DB = {
    entry["scope"]: {
        "service": service_name,
        "access_type": _infer_access_type(entry["scope"], {**entry, "service": service_name}),
        "google_classification": entry["classification"],
        "description": entry["description"],
        "classification": entry["classification"],
        "is_admin": entry.get("is_admin", False),
        "is_transitive": entry.get("is_transitive", False),
    }
    for service_name, scopes in SERVICE_SCOPES.items()
    for entry in scopes
}

ADMIN_SCOPES = sorted(
    scope for scope, entry in SCOPE_DB.items() if entry["is_admin"]
)
TRANSITIVE_SCOPES = sorted(
    scope for scope, entry in SCOPE_DB.items() if entry["is_transitive"]
)
