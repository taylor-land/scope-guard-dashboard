import pandas as pd

UNCLEANED_DATASET_PATH = 'dataset_creation/outputs/scope_guard_dataset008.csv'
CLEANED_DATASET_PATH = 'dataset_cleaning/outputs/scope_guard_dataset_cleaned.csv'

"""
In this file we remove all unrealistic scope combinations. Justification can be found in dataset_cleaning/dataset_cleaning_report.md
"""

df = pd.read_csv(UNCLEANED_DATASET_PATH,index_col='combination_id')
REMOVED_COMBINATION_IDS = [
    "SC-0011", "SC-0017", "SC-0114", "SC-0119", "SC-0252", "SC-0253", "SC-0254", "SC-0255", "SC-0256", "SC-0257",
    "SC-0264", "SC-0266", "SC-0298", "SC-0300", "SC-0302", "SC-0310", "SC-0316", "SC-0326", "SC-0328", "SC-0338",
    "SC-0339", "SC-0340", "SC-0346", "SC-0347", "SC-0348", "SC-0349", "SC-0356", "SC-0357", "SC-0358", "SC-0365",
    "SC-0366", "SC-0381", "SC-0390", "SC-0392", "SC-0394", "SC-0399", "SC-0400", "SC-0405", "SC-0406", "SC-0420",
    "SC-0432", "SC-0433", "SC-0434", "SC-0436", "SC-0448", "SC-0493", "SC-0494", "SC-0496", "SC-0509", "SC-0510",
    "SC-0511", "SC-0630", "SC-0631", "SC-0632", "SC-0633", "SC-0847", "SC-0848", "SC-0850", "SC-0851", "SC-0853",
    "SC-0854", "SC-0856", "SC-0858", "SC-0861", "SC-0862", "SC-0865", "SC-0866", "SC-0867", "SC-0872", "SC-0877",
    "SC-0878", "SC-0879", "SC-0882", "SC-0883", "SC-0886", "SC-0887", "SC-0894", "SC-0896", "SC-0900", "SC-0905",
    "SC-0906", "SC-0908", "SC-0911", "SC-0912", "SC-0915", "SC-0916", "SC-0919", "SC-0920", "SC-0924", "SC-0925",
    "SC-0927", "SC-0928", "SC-0931", "SC-0934", "SC-0935", "SC-0937", "SC-0938", "SC-0939", "SC-0942", "SC-0946",
    "SC-0947", "SC-0948", "SC-0949", "SC-0950", "SC-0951", "SC-0952", "SC-0954", "SC-0955", "SC-0956", "SC-0957",
    "SC-0959", "SC-0960", "SC-0964", "SC-0967", "SC-0968", "SC-0970", "SC-0975", "SC-0978", "SC-0979", "SC-0980",
    "SC-0981", "SC-0983", "SC-0984", "SC-0985", "SC-0988", "SC-0990", "SC-0991", "SC-0992", "SC-0995", "SC-0996",
    "SC-0997", "SC-0999", "SC-1022", "SC-1025", "SC-1036", "SC-1078", "SC-1079", "SC-1080", "SC-1081", "SC-1087",
    "SC-1089", "SC-1102", "SC-1113", "SC-1114", "SC-1115", "SC-1122", "SC-1126", "SC-1128", "SC-1129", "SC-1130",
    "SC-1133", "SC-1135", "SC-1137", "SC-1138", "SC-1139", "SC-1141", "SC-1144", "SC-1162", "SC-1166", "SC-1167",
    "SC-1169", "SC-1172", "SC-1177", "SC-1179", "SC-1185", "SC-1186", "SC-1187", "SC-1195", "SC-1200", "SC-1201",
    "SC-1205", "SC-1218", "SC-1219", "SC-1223", "SC-1244", "SC-1250", "SC-1255", "SC-1261", "SC-1262", "SC-1268",
    "SC-1269"
]
print(len(df)) #should be 1,845 if not something is very wrong
df = df.drop(REMOVED_COMBINATION_IDS)
print(len(df)) # should be 1,664
df.to_csv(CLEANED_DATASET_PATH)
print(df['risk_label'].value_counts())