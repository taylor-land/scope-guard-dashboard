import pandas as pd

UNCLEANED_DATASET_PATH = 'dataset_creation/outputs/scope_guard_dataset008.csv'
CLEANED_DATASET_PATH = 'dataset_cleaning/outputs/scope_guard_dataset_cleaned.csv'

"""
In this file we remove all unrealistic scope combinations. Justification can be found in dataset_cleaning/dataset_cleaning_report.md
"""

df = pd.read_csv(UNCLEANED_DATASET_PATH,index_col='combination_id')
unrealistic_combination_ids = [
    "SC-0337", "SC-0364", "SC-0387", "SC-0424", "SC-0457", "SC-0885", "SC-0918",
    "SC-1201", "SC-1212", "SC-0362", "SC-0430", "SC-0888", "SC-0931", "SC-0948",
    "SC-0966", "SC-0990", "SC-0997", "SC-1235", "SC-0026", "SC-0130", "SC-0388",
    "SC-0389", "SC-0536", "SC-0537", "SC-0539", "SC-0251", "SC-0414", "SC-0753",
    "SC-0959", "SC-1066", "SC-0303", "SC-0332", "SC-0911", "SC-0934", "SC-0941",
    "SC-0305", "SC-0350", "SC-0428", "SC-0964", "SC-0731", "SC-0944", "SC-0972",
    "SC-1044", "SC-0314", "SC-0933", "SC-0447", "SC-0883", "SC-0906", "SC-0983",
    "SC-0884", "SC-0907", "SC-0692", "SC-0980", "SC-1005", "SC-0946", "SC-0950",
    "SC-1223", "SC-0982", "SC-0985", "SC-0893", "SC-0970", "SC-0943", "SC-0949",
    "SC-0427", "SC-0929", "SC-1204", "SC-1183", "SC-1189", "SC-0371",
]
print(len(df)) # should be 1,903 
df = df.drop(unrealistic_combination_ids)
print(len(df)) # should be 1,834
df.to_csv(CLEANED_DATASET_PATH)