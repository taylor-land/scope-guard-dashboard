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
import pandas as pd

from scopes_data import (
    ACCESS_LEVELS,
    ADMIN_SCOPES as _ADMIN_SCOPES,
    SCOPE_DB,
    SERVICE_SENSITIVITY,
    TRANSITIVE_SCOPES as _TRANSITIVE_SCOPES,
)


BASE_DIR = Path(__file__).resolve().parent
FEATURE_NAMES_PATH = BASE_DIR / "scope_binarizer_feature_names.pkl"

ADMIN_SCOPES = set(_ADMIN_SCOPES)
TRANSITIVE_SCOPES = set(_TRANSITIVE_SCOPES)

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


def _scope_url(scope_entry):
    if isinstance(scope_entry, dict):
        return scope_entry.get("scope_url") or scope_entry.get("scope")
    return scope_entry


def _service_name(scope_entry):
    """Resolve the service name (e.g. 'Gmail') for a scope entry.

    Scope dicts built by the app already carry a 'service' key. For bare
    scope-URL strings (or dicts missing that key), fall back to looking the
    scope up in SCOPE_DB.
    """
    if isinstance(scope_entry, dict) and scope_entry.get("service"):
        return scope_entry["service"]
    scope_url = _scope_url(scope_entry)
    db_entry = SCOPE_DB.get(scope_url)
    return db_entry["service"] if db_entry else None


def _short_name(scope_url: str) -> str:
    """Map a full scope URL to the short feature name the model expects."""
    if scope_url in SPECIAL_SHORT_NAMES:
        return SPECIAL_SHORT_NAMES[scope_url]
    if scope_url.startswith(GOOGLEAPIS_PREFIX):
        return scope_url[len(GOOGLEAPIS_PREFIX):]
    return scope_url  # bare scopes: openid, email, profile


def onehot_encoding(scope_list, include_offline=False):
    """
    Build the full model input: every known scope one-hot encoded, every
    known service one-hot encoded (``svc:<Service>``), plus a trailing
    ``offline`` flag — in the order given by the feature-names file.

    Returns a single-row DataFrame whose columns exactly match, and are in the
    same order as, the model's training features.
    """
    feature_names = _load_feature_names()

    present_short_names = {_short_name(_scope_url(scope)) for scope in scope_list}
    present_services = {_service_name(scope) for scope in scope_list}
    present_services.discard(None)

    row = []
    for name in feature_names:
        if name == OFFLINE_FEATURE:
            row.append(int(bool(include_offline)))
        elif name.startswith(SERVICE_FEATURE_PREFIX):
            service = name[len(SERVICE_FEATURE_PREFIX):]
            row.append(1 if service in present_services else 0)
        else:
            row.append(1 if name in present_short_names else 0)

    return pd.DataFrame([row], columns=feature_names)


def build_model_input(scope_list, include_offline=False):
    """Explicit alias for the model's full input vector."""
    return onehot_encoding(scope_list, include_offline)


def engineer_features(scope_list, include_offline):
    """
    Interpretable engineered risk features. No longer part of the model input;
    kept for display / analysis purposes only.
    """

    scope_urls = [_scope_url(scope) for scope in scope_list]

    data_sensitivity = 0
    access_level = 0
    transitive_exposure = 0
    has_restricted_scope = 0
    services = set()

    persistence = int(bool(include_offline))

    for scope in scope_urls:
        db_data = SCOPE_DB[scope]
        service = db_data["service"]
        itt_sens = SERVICE_SENSITIVITY[service]
        itt_access = ACCESS_LEVELS[db_data["access_type"]]

        if scope in ADMIN_SCOPES:
            access_level = 3

        if scope in TRANSITIVE_SCOPES:
            transitive_exposure = 1

        if db_data["google_classification"] == "restricted":
            has_restricted_scope = 1

        services.add(service)
        data_sensitivity = max(data_sensitivity, itt_sens)
        access_level = max(access_level, itt_access)

    score_df = pd.DataFrame(
        [
            {
                "data_sensitivity": data_sensitivity,
                "persistence": persistence,
                "transitive_exposure": transitive_exposure,
                "scope_count": len(scope_urls),
                "cross_service_breadth": len(services),
                "has_restricted_scope": has_restricted_scope,
                "access_level": access_level,
            }
        ],
        columns=[
            "data_sensitivity",
            "persistence",
            "transitive_exposure",
            "scope_count",
            "cross_service_breadth",
            "has_restricted_scope",
            "access_level",
        ],
    )
    return score_df
