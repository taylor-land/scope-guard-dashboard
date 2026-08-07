# ScopeGuard

Explainable AI dashboard for Google OAuth scope combinations

## Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/taylor-land/scope-guard-dashboard.git
cd scope-guard-dashboard
pip install -r requirements.txt
```
## Usage

Run the main app.py file to view the dashboard:
```bash
streamlit run app.py
```

This should take you to the dashboard in a new browser tab.

## Methodology
An overview of the file structure and what file does what

### scope-guard/data:

Contains:
- google_oauth_scope_catalog.json
  - scope catalog file, contains all scopes, their service, and realted information

Source: This file was downloaded from the Google API documentation

--------------------
### scope-guard/dataset_creation

Contains:
- ScopeGuardDatasetCreation008ipynb.ipynb
  - where our dataset is generated and risk labeling occurs
- outputs:
  - scope_guard_dataset008.csv
    - initial dataset, cleaned in dataset_cleaning
  - scope_information.json
    - contains a variety of scope information formatted for usage in dashboard/describe_scopes.py which is in turn used in dashboard/app.py
  - scopes_by_service.json:
    - dictionairy containing all services and then a list of their associated scopes used for one hot encoding services in dashboard/app.py and in pipeline/model_pieline.ipynb
  - services_scopes_descriptive.json
    - used in dashboard/app.py for displaying drop down scope selection


    

License

MIT License © 2025 Your Name