"""
OAuth Scope Risk Dashboard — v2 (no live risk features while building)

  1. Scope-builder page: service/scope dropdowns, offline-refresh-token choice,
     and a collapsed "current combination" panel (with remove buttons). The
     live risk-feature boxes have been removed from this page — nothing about
     the model's view of the combination is shown until it's submitted.
  2. Result page (after "Submit Scope Combination"): model prediction (from
     logreg_model.joblib) mapped to low/medium/high/critical, styled like the
     ScopeGuard prototype, plus a SHAP feature-impact chart (seaborn/viridis).
     Anchor + "explain
     this to me" are left as empty placeholders for now, as instructed.
"""

from pathlib import Path
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
import streamlit as st

import matplotlib.pyplot as plt
import seaborn as sns

try:
    import xgboost  # noqa: F401  (only needed if the loaded model is XGBoost-based)
except ImportError:  # pragma: no cover
    xgboost = None

try:
    import shap
except ImportError:  # pragma: no cover
    shap = None

try:
    import dill
except ImportError:  # pragma: no cover
    dill = None

from scopes_data import SERVICE_SCOPES
from preprocessing import onehot_encoding, describe_feature, OFFLINE_FEATURE

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "logreg_model.joblib"
ANCHOR_EXPLAINER_PATH = BASE_DIR / "anchor_explainer.dill"

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="OAuth Scope Risk Dashboard", page_icon="🔐", layout="wide")

st.markdown(
    """
    <style>
    div[data-baseweb="select"] { min-width: 100% !important; }
    div[data-baseweb="select"] * { font-size: 0.95rem; }
    ul[data-testid="stSelectboxVirtualDropdown"] { min-width: 650px !important; }
    .verdict-banner { border-radius: 16px; padding: 28px 32px; color: #fff; margin: 8px 0 20px; }
    .verdict-banner .vlabel { font-size: 13px; text-transform: uppercase; letter-spacing: 0.1em;
                               opacity: 0.85; font-weight: 600; }
    .verdict-banner .vtier { font-size: 44px; font-weight: 700; letter-spacing: -0.02em; margin: 4px 0 6px; }
    .verdict-banner .vsub { font-size: 13px; opacity: 0.9; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Reference / display data
# ---------------------------------------------------------------------------
GOOGLE_SCOPES = SERVICE_SCOPES

CLASSIFICATION_BADGES = {
    "non_sensitive": "🟢 non-sensitive",
    "sensitive": "🟠 sensitive",
    "restricted": "🔴 restricted",
}

RISK_LABELS = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}
RISK_COLORS = {"Low": "#1B9E5A", "Medium": "#C68A0E", "High": "#E8730C", "Critical": "#D42E2E"}

RISK_CLASS_DESCRIPTIONS = {
    "Low": "Read-only access to non-sensitive data. Minimal damage potential if the app is compromised.",
    "Medium": "Read access to moderately sensitive data or write access to non-sensitive data. Limited damage potential.",
    "High": "Write access to sensitive data, persistent access to email or files, or any admin-level scope. Significant damage potential.",
    "Critical": "Full access to email or admin with persistence, or broad multi-service access with high privileges. Maximum damage potential.",
}


def scope_meta_line(entry: dict) -> str:
    parts = [CLASSIFICATION_BADGES.get(entry.get("classification"), "")]
    if entry.get("sensitivity") is not None:
        parts.append(f"Risk score: {entry['sensitivity']}/5")
    if entry.get("is_admin"):
        parts.append("🛡️ Admin")
    if entry.get("is_transitive"):
        parts.append("🔁 Transitive")
    return " · ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------
@st.cache_resource
def load_model(path: str = str(MODEL_PATH)):
    return joblib.load(path)


def _bind_anchor_predictor(explainer, predictor_fn):
    """Rebind the explainer and its samplers to a predictor closure that uses
    the currently loaded model."""
    for attr in ("predictor", "_predictor", "_ohe_predictor"):
        if hasattr(explainer, attr):
            setattr(explainer, attr, predictor_fn)

    for sampler in getattr(explainer, "samplers", []) or []:
        for attr in ("predictor", "_predictor"):
            if hasattr(sampler, attr):
                setattr(sampler, attr, predictor_fn)

    return explainer


@st.cache_resource
def load_anchor_explainer(path: str = str(ANCHOR_EXPLAINER_PATH)):
    """Load the pre-fitted alibi AnchorTabular explainer and reattach a
    predictor closure that uses the currently loaded model."""
    with open(path, "rb") as f:
        explainer = dill.load(f)

    def _predict_with_loaded_model(x):
        model = load_model()
        x_array = np.asarray(x, dtype=float)
        if x_array.ndim == 1:
            x_array = x_array.reshape(1, -1)
        preds = model.predict(x_array)
        return preds[0] if preds.ndim > 1 and preds.shape[0] == 1 else preds

    return _bind_anchor_predictor(explainer, _predict_with_loaded_model)


@lru_cache(maxsize=32)
def _compute_anchor_explanation(feature_tuple: tuple):
    """The anchor beam search is slow (can take tens of seconds), and with
    no caching it was re-running on *every* script rerun — not just when the
    user submitted a new combination, but on any widget interaction on the
    result page (expanding a panel, etc.). That made the page look hung and
    delayed every navigation click behind another full anchor search.

    Caching by the exact feature vector means it's computed once per unique
    scope combination and instantly reused after that, for the lifetime of
    this server process."""
    anchor_explainer = load_anchor_explainer()
    return anchor_explainer.explain(np.array(feature_tuple, dtype=float), threshold=0.95)


def preprocess_scopes(scope_combination: list, persistence: bool) -> pd.DataFrame:
    """Build the model input: every known scope one-hot encoded plus the
    trailing 'offline' flag, in the exact column order the model expects."""
    return onehot_encoding(scope_combination, persistence).reset_index(drop=True)


@st.cache_resource
def _shap_background(_feature_columns: tuple):
    """All-zero baseline row (no scopes selected, no offline token) used as
    the SHAP reference point. Reasonable for one-hot/binary features when no
    training data is shipped alongside the model."""
    return pd.DataFrame([[0] * len(_feature_columns)], columns=list(_feature_columns))


def _build_explainer(model, features: pd.DataFrame):
    """Pick a SHAP explainer appropriate for whatever model is currently
    loaded, so the dashboard keeps working across model swaps (linear,
    tree-based, or anything else with predict_proba)."""
    background = _shap_background(tuple(features.columns))

    n_classes = len(getattr(model, "classes_", []))
    if hasattr(model, "coef_") and n_classes <= 2:
        # Binary linear models. shap's LinearExplainer doesn't reliably
        # support multi-class linear models, so multi-class logistic
        # regression (our current 4-class model) falls through to the
        # generic branch below instead.
        return shap.LinearExplainer(model, background)
    if hasattr(model, "get_booster") or hasattr(model, "feature_importances_"):
        # Tree-based models (XGBoost, RandomForest, etc.)
        return shap.TreeExplainer(model)
    # Generic fallback: explain predict_proba directly, works for any model.
    return shap.Explainer(model.predict_proba, background)


def class_shap_explanation(model, features: pd.DataFrame, class_index: int):
    """Return a shap.Explanation for a single class/row, handling both the
    list-of-arrays and stacked-ndarray return shapes across shap versions."""
    explainer = _build_explainer(model, features)
    raw = explainer(features)

    values = raw.values
    base_values = raw.base_values

    if isinstance(values, list):
        row_values = np.asarray(values[class_index])[0]
        row_base = base_values[class_index] if isinstance(base_values, (list, tuple, np.ndarray)) else base_values
    elif getattr(values, "ndim", 0) == 3:
        row_values = np.asarray(values)[0, :, class_index]
        bv = np.asarray(base_values)
        row_base = bv[0, class_index] if bv.ndim == 2 else bv[class_index]
    else:
        row_values = np.asarray(values)[0]
        row_base = base_values if np.isscalar(base_values) else np.asarray(base_values).ravel()[0]

    return shap.Explanation(
        values=row_values,
        base_values=row_base,
        data=features.iloc[0].values,
        feature_names=list(features.columns),
    )


def plot_shap_barh(exp, max_display: int = 12):
    """Render a shap.Explanation as a horizontal seaborn bar chart with
    sign-based colors instead of shap's built-in waterfall plot.

    Ordering: most significant (largest |impact|) at the top, down to least
    significant — e.g. values 1.5, -0.9, 0.3 render top-to-bottom in that
    order, regardless of sign.

    Color: positive values use seaborn's Paired[3] and negative values use
    Paired[2].

    Labels: every feature here is a binary 0/1 one-hot column, so each bar's
    label also states whether it was the *presence* (scope/service selected,
    offline included) or *absence* of that feature that produced the impact
    — e.g. "gmail.readonly — present" vs. "svc:Keep — absent".
    """
    values = np.asarray(exp.values, dtype=float)
    feature_names = list(exp.feature_names)
    feature_data = np.asarray(exp.data).ravel()

    # Most -> least significant, by |impact|. Seaborn renders dataframe row 0
    # at the top of a horizontal bar chart, so no further reordering needed.
    order = np.argsort(np.abs(values))[::-1][:max_display]
    plot_values = values[order]
    plot_names = [feature_names[i] for i in order]
    plot_present = [bool(round(feature_data[i])) for i in order]
    plot_labels = [
        f"{name}  —  {'present' if present else 'absent'}"
        for name, present in zip(plot_names, plot_present)
    ]
    plot_df = pd.DataFrame({"feature": plot_labels, "shap_value": plot_values})

    positive_color = sns.color_palette("Paired")[3]
    negative_color = sns.color_palette("Paired")[2]
    palette = [positive_color if v >= 0 else negative_color for v in plot_df["shap_value"]]

    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(8.2, 0.42 * len(plot_df) + 1.6))
    sns.barplot(data=plot_df, x="shap_value", y="feature", hue="feature",
                palette=palette, legend=False, ax=ax,
                order=plot_df["feature"])
    ax.axvline(0, color="#333333", linewidth=0.9)
    ax.set_xlabel("SHAP value (impact on predicted-class score)")
    ax.set_ylabel("")
    ax.set_title(f"Top {len(plot_df)} feature contributions, most → least significant",
                 fontsize=11, loc="left")
    sns.despine(left=True, bottom=True)

    ax.legend(handles=[
        plt.Line2D([0], [0], color=positive_color, lw=6, label="positive SHAP value"),
        plt.Line2D([0], [0], color=negative_color, lw=6, label="negative SHAP value"),
    ], frameon=False, loc="lower right", fontsize=8)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Anchor ("the rule") explanation
# ---------------------------------------------------------------------------
import re

_NUMBER_RE = re.compile(r"^-?\d+\.?\d*$")
_COMPARISON_TOKENS = {"<", "<=", ">", ">=", "=", "=="}


def _feature_name_from_predicate(predicate: str, known_columns: set) -> str | None:
    """Anchor rule conditions come back as strings like
    ``'gmail.readonly > 0.50'`` or two-sided ranges like
    ``'0.00 < offline <= 1.00'``. Rather than parse the threshold, just pull
    out whichever token is one of our known feature/column names — we already
    know the actual 0/1 value for this instance from ``features``."""
    for token in predicate.split():
        if token in _COMPARISON_TOKENS or _NUMBER_RE.match(token):
            continue
        if token in known_columns:
            return token
    return None


def render_anchor_explanation(anchor_exp, features: pd.DataFrame):
    """Render an alibi AnchorTabular explanation as a plain-language rule:
    'as long as these conditions hold, the model gives this same verdict
    X% of the time, and conditions like this come up Y% of the time.'

    Only "present" conditions are shown (e.g. "the Gmail scope is included"),
    since anchor conditions on scopes/services the user *didn't* select are
    mostly noise for a non-technical reader — a combination with a couple of
    scopes will trivially satisfy "no Fitness scope is included" and dozens
    of others like it. The offline flag is the one exception: whether an
    offline refresh token is or isn't requested is itself a meaningful,
    user-set choice either way, so both directions are kept for it."""
    predicates = list(anchor_exp.data["anchor"])
    precision = anchor_exp.data["precision"]
    coverage = anchor_exp.data["coverage"]

    if not predicates:
        st.info(
            "No short, stable rule was found for this exact combination — "
            "the model's decision here depends on a broader mix of factors."
        )
        return

    known_columns = set(features.columns)
    clauses = []
    for predicate in predicates:
        feature_name = _feature_name_from_predicate(predicate, known_columns)
        if feature_name is None:
            clauses.append(predicate)  # fallback: show the raw condition
            continue
        present = bool(round(features.iloc[0][feature_name]))
        if not present and feature_name != OFFLINE_FEATURE:
            continue  # drop "X is not included" clauses
        clauses.append(describe_feature(feature_name, present))

    if not clauses:
        st.markdown(
            "This rule relies only on scopes and services that are **absent** "
            "from your combination — nothing you actually selected was singled "
            "out as the deciding factor."
        )
    else:
        st.markdown("**As long as:**")
        for clause in clauses:
            st.markdown(f"- {clause}")

    st.markdown(
        f"…the model reaches **this same risk verdict about "
        f"{precision * 100:.0f}% of the time**, and a combination fitting "
        f"this rule shows up in roughly **{coverage * 100:.0f}% of the "
        f"combinations** the model sees overall."
    )


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
defaults = {
    "page": "build",       # "build" or "result"
    "scopes": [],           # list of scope entry dicts
    "persistence": False,   # offline refresh token bool
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_all():
    for key, value in defaults.items():
        st.session_state[key] = value


def _go_to_build():
    st.session_state.page = "build"


# ---------------------------------------------------------------------------
# BUILD PAGE
# ---------------------------------------------------------------------------
def render_build_page():
    st.title("🔐 OAuth Scope Risk Dashboard")
    st.write(
        "Build a combination of Google OAuth scopes, choose whether it includes an "
        "offline refresh token, then submit it to see the model's risk prediction."
    )
    st.divider()

    # --- Step 1: service + scope dropdowns -------------------------------
    st.subheader("Add a Scope")
    selected_service = st.selectbox("Service", options=sorted(GOOGLE_SCOPES.keys()), key="service_select")

    scope_options = GOOGLE_SCOPES[selected_service]
    description_to_entry = {entry["description"]: entry for entry in scope_options}
    selected_description = st.selectbox("Scope", options=list(description_to_entry.keys()), key="scope_select")
    selected_entry = description_to_entry[selected_description]

    st.markdown("Scope URL:")
    st.code(selected_entry["scope"], language=None)
    st.caption(scope_meta_line(selected_entry))

    if st.button("➕ Enter Scope"):
        new_scope = {
            "service": selected_service,
            "description": selected_entry["description"],
            "scope_url": selected_entry["scope"],
            "classification": selected_entry["classification"],
            "sensitivity": selected_entry["sensitivity"],
            "is_admin": selected_entry["is_admin"],
            "is_transitive": selected_entry["is_transitive"],
        }
        if new_scope not in st.session_state.scopes:
            st.session_state.scopes.append(new_scope)
            st.rerun()
        else:
            st.info("That scope has already been added.")

    st.divider()

    # --- Step 2: offline refresh token, two boxes side by side ------------
    st.subheader("Offline Refresh Token")
    st.write("Should this scope combination include an offline refresh token?")

    box1, box2 = st.columns(2)
    with box1:
        with st.container(border=True):
            selected = st.session_state.persistence is True
            st.markdown(f"### Include Offline Refresh Token {'✅' if selected else ''}")
            if st.button("Include", key="include_btn", type="primary" if selected else "secondary"):
                st.session_state.persistence = True
                st.rerun()
    with box2:
        with st.container(border=True):
            selected = st.session_state.persistence is False
            st.markdown(f"### Exclude Offline Refresh Token {'✅' if selected else ''}")
            if st.button("Exclude", key="exclude_btn", type="primary" if selected else "secondary"):
                st.session_state.persistence = False
                st.rerun()

    st.divider()

    # --- Step 3: hidden panel with current combo + remove buttons --------
    with st.expander("👁️ View current scope combination & offline access", expanded=False):
        if not st.session_state.scopes:
            st.caption("No scopes added yet.")
        else:
            index_to_remove = None
            for i, scope in enumerate(st.session_state.scopes):
                row_left, row_right = st.columns([9, 1])
                with row_left:
                    meta = scope_meta_line(scope)
                    st.markdown(
                        f"**{scope['service']}** — {scope['description']}  \n"
                        f"&nbsp;&nbsp;&nbsp;&nbsp;`{scope['scope_url']}`  \n"
                        f"{meta}",
                        unsafe_allow_html=True,
                    )
                with row_right:
                    if st.button("❌", key=f"remove_{i}"):
                        index_to_remove = i
                st.divider()
            if index_to_remove is not None:
                st.session_state.scopes.pop(index_to_remove)
                st.rerun()

        st.write(f"**Offline refresh token included:** {st.session_state.persistence}")

    st.divider()

    # --- Step 4: submit ----------------------------------------------------
    disabled = len(st.session_state.scopes) == 0
    if st.button("🚀 Submit Scope Combination", type="primary", disabled=disabled):
        st.session_state.page = "result"
        st.rerun()
    if disabled:
        st.caption("Add at least one scope before submitting.")


# ---------------------------------------------------------------------------
# RESULT PAGE
# ---------------------------------------------------------------------------
def render_result_page():
    st.button("‹ Back to builder", on_click=_go_to_build)

    st.title("Result")

    features = preprocess_scopes(st.session_state.scopes, st.session_state.persistence)

    try:
        model = load_model()
        prediction = int(model.predict(features)[0])
        tier = RISK_LABELS.get(prediction, f"Unknown ({prediction})")
        color = RISK_COLORS.get(tier, "#546E7A")

        st.markdown(
            f"""
            <div class="verdict-banner" style="background:{color};">
              <div class="vlabel">Predicted Risk</div>
              <div class="vtier">{tier}</div>
              <div class="vsub">Model output class {prediction} → {tier} risk</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_shap, col_anchor = st.columns(2)

        with col_shap:
            st.markdown("**Why — SHAP**")
            with st.expander("📊 SHAP feature impact", expanded=False):
                if shap is None:
                    st.warning("Unable to render SHAP waterfall (shap is not installed).")
                else:
                    try:
                        exp = class_shap_explanation(model, features, prediction)
                        fig = plot_shap_barh(exp, max_display=12)
                        st.pyplot(fig, clear_figure=True)
                    except Exception as shap_error:
                        st.warning(f"Unable to render SHAP chart ({shap_error}).")

        with col_anchor:
            st.markdown("**The Rule — Anchor**")
            with st.expander("🔗 Anchor rule", expanded=False):
                if dill is None:
                    st.warning("Unable to compute the anchor rule (dill is not installed).")
                else:
                    try:
                        feature_tuple = tuple(features.values[0].astype(float))
                        with st.spinner("Finding the simplest rule behind this result…"):
                            anchor_exp = _compute_anchor_explanation(feature_tuple)
                        render_anchor_explanation(anchor_exp, features)
                    except Exception:
                        st.info("Anchor rule is temporarily unavailable for this model.")

        with st.expander("Risk class descriptions", expanded=False):
            for label in ("Low", "Medium", "High", "Critical"):
                st.markdown(f"**{label}:** {RISK_CLASS_DESCRIPTIONS[label]}")

    except Exception as e:
        st.warning(f"Model/preprocessing pipeline error ({e}). Showing placeholder output instead.")

    st.divider()

    st.subheader("Explain This To Me")
    st.info("Coming soon.")

    st.divider()

    with st.expander("Combination submitted", expanded=False):
        for scope in st.session_state.scopes:
            meta = scope_meta_line(scope)
            st.markdown(
                f"- **{scope['service']}**: {scope['description']}  \n"
                f"&nbsp;&nbsp;&nbsp;&nbsp;`{scope['scope_url']}`  \n"
                f"&nbsp;&nbsp;&nbsp;&nbsp;{meta}",
                unsafe_allow_html=True,
            )
        st.write(f"**Persistence (offline refresh token):** {st.session_state.persistence}")

    with st.expander("Preprocessed features", expanded=False):
        st.dataframe(features, use_container_width=True)

    st.divider()
    st.button("🔄 Start Over", on_click=reset_all)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
if st.session_state.page == "build":
    render_build_page()
else:
    render_result_page()
