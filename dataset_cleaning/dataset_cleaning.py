import pandas as pd

UNCLEANED_DATASET_PATH = 'dataset_creation/outputs/scope_guard_dataset008.csv'
CLEANED_DATASET_PATH = 'dataset_cleaning/outputs/scope_guard_dataset_cleaned.csv'

"""
In this file we remove all unrealistic scope combinations. Justification can be found in dataset_cleaning/dataset_cleaning_report.md
"""

df = pd.read_csv(UNCLEANED_DATASET_PATH,index_col='combination_id')
REMOVED_COMBINATION_IDS = [
    "SC-0011", "SC-0017", "SC-0115", "SC-0121", "SC-0256",
    "SC-0257", "SC-0258", "SC-0259", "SC-0260", "SC-0261",
    "SC-0268", "SC-0270", "SC-0302", "SC-0304", "SC-0307",
    "SC-0315", "SC-0321", "SC-0331", "SC-0333", "SC-0343",
    "SC-0344", "SC-0351", "SC-0352", "SC-0353", "SC-0354",
    "SC-0361", "SC-0362", "SC-0363", "SC-0370", "SC-0371",
    "SC-0396", "SC-0398", "SC-0400", "SC-0405", "SC-0406",
    "SC-0411", "SC-0412", "SC-0426", "SC-0438", "SC-0439",
    "SC-0440", "SC-0442", "SC-0454", "SC-0499", "SC-0500",
    "SC-0502", "SC-0515", "SC-0516", "SC-0517", "SC-0639",
    "SC-0640", "SC-0641", "SC-0642", "SC-0862", "SC-0863",
    "SC-0865", "SC-0866", "SC-0868", "SC-0869", "SC-0871",
    "SC-0873", "SC-0876", "SC-0877", "SC-0880", "SC-0881",
    "SC-0882", "SC-0887", "SC-0892", "SC-0893", "SC-0894",
    "SC-0897", "SC-0898", "SC-0901", "SC-0902", "SC-0909",
    "SC-0911", "SC-0915", "SC-0920", "SC-0921", "SC-0923",
    "SC-0926", "SC-0927", "SC-0930", "SC-0934", "SC-0935",
    "SC-0939", "SC-0940", "SC-0941", "SC-0942", "SC-0943",
    "SC-0946", "SC-0948", "SC-0949", "SC-0950", "SC-0952",
    "SC-0954", "SC-0957", "SC-0961", "SC-0962", "SC-0963",
    "SC-0964", "SC-0965", "SC-0966", "SC-0967", "SC-0969",
    "SC-0970", "SC-0971", "SC-0972", "SC-0974", "SC-0975",
    "SC-0979", "SC-0982", "SC-0985", "SC-0990", "SC-0993",
    "SC-0994", "SC-0996", "SC-0998", "SC-0999", "SC-1177",
    "SC-1179", "SC-1185", "SC-1186", "SC-1187", "SC-1195",
    "SC-1200", "SC-1205", "SC-1218", "SC-1219", "SC-1223",
    "SC-1244", "SC-1250", "SC-1255", "SC-1261", "SC-1262",
    "SC-1268", "SC-1269",
]
print(len(df)) # should be 1,894 
df = df.drop(REMOVED_COMBINATION_IDS)
print(len(df)) # should be 1,757
df.to_csv(CLEANED_DATASET_PATH)