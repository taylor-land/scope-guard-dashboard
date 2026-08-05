"""
Preprocessing for the OAuth Scope Risk model.

The current model (``model.joblib``) takes a single flat feature vector:

  1. every known scope, one-hot encoded (short-name columns, e.g. ``gmail.readonly``)
  2. every known service, one-hot encoded (``svc:<Service>`` columns, e.g. ``svc:Gmail``)
  3. a trailing ``offline`` column for the offline-refresh-token flag

The engineered risk features (data_sensitivity, access_level, ...) are not
part of the model input.

The column order/full feature list is defined by
``scope_binarizer_feature_names.pkl`` — a plain list of feature names, scopes
first, then ``svc:`` service columns, then ``offline`` last. Because that file
holds only the names (not a fitted MultiLabelBinarizer), the one-hot vector is
built directly against that name list, which also guarantees the output
columns line up with what the model was trained on regardless of which model
(linear, tree-based, etc.) is currently loaded.

``engineer_features`` is kept for anything that still wants the interpretable
risk features (e.g. display), but it is no longer on the model path.
"""

from functools import lru_cache
from pathlib import Path
import joblib
import json

with open('dataset_creation/outputs/scope_information.json', 'r') as f:
    SCOPE_INFORMATION = json.load(f)
for i in SCOPE_INFORMATION:
    print(i)

ADMIN_SCOPES = SCOPE_INFORMATION['ADMIN_SCOPES']
SCOPE_DB = SCOPE_INFORMATION["SCOPE_DB"]
TRANSITIVE_SCOPES = SCOPE_INFORMATION["TRANSITIVE_SCOPES"]

FEATURE_NAMES_PATH = "scope_binarizer_feature_names.pkl"

# Full scope URLs are stored in the app, but the model's feature names use the
# short form (the segment after the googleapis /auth/ prefix). One scope uses a
# different host and is special-cased.
GOOGLEAPIS_PREFIX = "https://www.googleapis.com/auth/"
SPECIAL_SHORT_NAMES = {"https://mail.google.com/": "mail.google.com"}

OFFLINE_FEATURE = "offline"
SERVICE_FEATURE_PREFIX = "svc:"


@lru_cache(maxsize=1)
def _load_feature_names():
    """Ordered list of model feature names (one-hot scopes + 'svc:' service
    flags + 'offline')."""
    return list(joblib.load(FEATURE_NAMES_PATH))

def _short_name(scope_url: str) -> str:
    """Map a full scope URL to the short feature name the model expects."""
    if scope_url in SPECIAL_SHORT_NAMES:
        return SPECIAL_SHORT_NAMES[scope_url]
    if scope_url.startswith(GOOGLEAPIS_PREFIX):
        return scope_url[len(GOOGLEAPIS_PREFIX):]
    return scope_url  # bare scopes: openid, email, profile

@lru_cache(maxsize=1)
def _short_name_lookup():
    """Reverse of ``_short_name``: map every known short feature name back to
    its scope URL, description, and service, so the UI can turn a raw model
    column name into something a non-technical user can read."""
    lookup = {}
    for scope_url, entry in SCOPE_DB.items():
        lookup[_short_name(scope_url)] = {
            "scope_url": scope_url,
            "description": entry["description"],
            "service": entry["service"],
        }
    return lookup


def describe_feature(feature_name: str, present: bool) -> str:
    """Turn one model feature name (a scope short name, a ``svc:<Service>``
    flag, or ``offline``) plus whether it's present/absent for this instance
    into a plain-language clause a non-technical user can read.

    Used to translate raw column names — from things like the anchor
    explainer's rule conditions — into readable sentences.
    """
    if feature_name == OFFLINE_FEATURE:
        return (
            "an offline refresh token is requested"
            if present
            else "no offline refresh token is requested"
        )
    if feature_name.startswith(SERVICE_FEATURE_PREFIX):
        service = feature_name[len(SERVICE_FEATURE_PREFIX):]
        return (
            f"at least one {service} scope is included"
            if present
            else f"no {service} scope is included"
        )
    entry = _short_name_lookup().get(feature_name)
    if entry:
        label = f"the \u201c{entry['description']}\u201d scope ({entry['service']})"
    else:
        label = f"`{feature_name}`"
    return f"{label} is included" if present else f"{label} is not included"
