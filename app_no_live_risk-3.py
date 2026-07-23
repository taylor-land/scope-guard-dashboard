"""
OAuth Scope Risk Dashboard — v2 (no live risk features while building)

  1. Scope-builder page: service/scope dropdowns, offline-refresh-token choice,
     and a collapsed "current combination" panel (with remove buttons). The
     live risk-feature boxes have been removed from this page — nothing about
     the model's view of the combination is shown until it's submitted.
  2. Result page (after "Submit Scope Combination"): model prediction (from
     model.joblib) mapped to low/medium/high/critical, styled like the
     ScopeGuard prototype, plus a SHAP feature-impact chart (seaborn/viridis).
     Anchor + "explain
     this to me" are left as empty placeholders for now, as instructed.
"""

from pathlib import Path

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

from scopes_data import SERVICE_SCOPES
from preprocessing import onehot_encoding

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.joblib"

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
    """Render a shap.Explanation as a horizontal seaborn bar chart (viridis
    palette) instead of shap's built-in waterfall plot.

    Ordering: most significant (largest |impact|) at the top, down to least
    significant — e.g. values 1.5, -0.9, 0.3 render top-to-bottom in that
    order, regardless of sign.

    Color: signed value on a viridis scale centered at zero, so the color
    encodes *direction* as well as magnitude — features pushing the
    prediction toward the predicted tier land on the bright green/yellow end,
    features pushing away from it land on the dark purple end. The scale is
    symmetric around zero (based on the largest |impact| shown) so a
    colorbar can display the full range, including negative impacts.

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

    max_abs = np.abs(plot_values).max()
    max_abs = max_abs if max_abs > 0 else 1.0
    norm = plt.Normalize(vmin=-max_abs, vmax=max_abs)
    cmap = plt.cm.viridis
    palette = [cmap(norm(v)) for v in plot_df["shap_value"]]

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

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", pad=0.22, fraction=0.05, aspect=30)
    cbar.set_label(
        "purple = pushes away from predicted tier   ·   green/yellow = pushes toward predicted tier",
        fontsize=8,
    )
    cbar.ax.tick_params(labelsize=7)

    fig.tight_layout()
    return fig


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
    if st.button("‹ Back to builder"):
        st.session_state.page = "build"
        st.rerun()

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
                st.info("Coming soon.")

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
    if st.button("🔄 Start Over"):
        reset_all()
        st.rerun()


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
if st.session_state.page == "build":
    render_build_page()
else:
    render_result_page()
