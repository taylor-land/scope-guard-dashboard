# ScopeGuard

Explainable AI dashboard for Google OAuth scope combinations.

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/taylor-land/scope-guard-dashboard.git
cd scope-guard-dashboard
pip install -r requirements.txt
```

## Usage

> **Note:** Insert an API key into `API_KEY` before running the dashboard.

Run the main `app.py` file to launch the dashboard:

```bash
streamlit run dashboard/app.py
```

This will open the dashboard in a new browser tab.

## Methodology

Overview of the file structure and what each file does.

### `data/`

| File | Description |
|---|---|
| `google_oauth_scope_catalog.json` | Scope catalog file containing all scopes, their service, and related information. Used in `dataset_creation/pipeline`. Source: downloaded from the Google API documentation. |

### `dataset_creation/`

| File | Description |
|---|---|
| `ScopeGuardDatasetCreation008.ipynb` | Generates the dataset and performs risk labeling. |

**Outputs:**

| File | Description |
|---|---|
| `scope_guard_dataset008.csv` | Initial dataset, later cleaned in `dataset_cleaning`. |
| `scope_information.json` | Contains a variety of scope information, formatted for use in `dashboard/describe_scopes.py`, which is in turn used in `dashboard/app.py`. |
| `scopes_by_service.json` | Dictionary mapping each service to its associated scopes. Used for one-hot encoding services in `dashboard/app.py` and `pipeline/model_pipeline.ipynb`. |
| `services_scopes_descriptive.json` | Used in `dashboard/app.py` for the dropdown scope selection. |

### `dataset_cleaning/`

| File | Description |
|---|---|
| `dataset_cleaning.py` | Cleans the dataset of unrealistic scope combinations. |
| `dataset_cleaning_report.md` | Justification and details regarding removals. |

**Outputs:**

| File | Description |
|---|---|
| `scope_guard_dataset_cleaned.csv` | Cleaned, finalized dataset. |

### `pipeline/`

| File | Description |
|---|---|
| `model_pipeline.ipynb` | Full model training pipeline: preprocessing, training, selection, and evaluation. |

**Outputs:**

| File | Description |
|---|---|
| `best_model.joblib` | Best-performing model (Logreg), exported. Used to generate the anchor explainer in `anchor/fit_anchor_explainer.py`, and in `dashboard/app.py`. |
| `best_shap_scope_explanation.png` | SHAP explanation generated using logreg. |
| `confusion_matrix.png` | Confusion matrix for logreg on the testing set. |
| `optionB_engineered_reference.csv` | Complete engineered feature CSV. *Not used* in the current training pipeline or any other file. |
| `scope_binarizer.joblib` | `MultiLabelBinarizer` object fit for encoding scopes. Used in `dashboard/app.py`. |
| `scope_guard_dataset_optionB.csv` | One-hot encoded full dataset — includes scope ID, method of creation, actual scope combination, description, full one-hot encoded data, and risk label. *Not used* in any other file. |
| `scope_vocabulary.json` | Maps each shortened scope name back to its full URL. *Not used* in any other file. |
| `service_binarizer.joblib` | Binarizer for services. Used in `dashboard/app.py`. |
| `X_train.csv` | Full one-hot encoded `X_train` the model is trained on. Used in `anchor/fit_anchor_explainer.py` to create the anchor explainer object. |

### `anchor/`

| File | Description |
|---|---|
| `fit_anchor_explainer.py` | Generates the anchor explainer. |

**Outputs:**

| File | Description |
|---|---|
| `anchor_explainer/` | Contains `explainer.dill` and `meta.dill`. Loaded directly by `dashboard/app.py` to load the anchor explainer. |

### `dashboard/`

| File | Description |
|---|---|
| `app.py` | Dashboard for the model — allows users to view risk predictions and explanations for predictions. **Requires an API key inserted into `API_KEY` to run.** |
| `describe_scopes.py` | Helper functions used in `app.py` to generate descriptions of scopes. |

## `unused_encodings_pipelines/`
Contains legacy encodings, not used in any other file
## License

MIT License © 2026 Taylor Land & Imtiaz Ahmad, PhD

## Contact:
Taylor Land: landt@mail.gvsu.edu


Imtiaz Ahmad, PhD: ahmadi@mail.gvsu.edu
