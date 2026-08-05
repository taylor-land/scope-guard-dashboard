import dill
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
import os
from alibi.saving import save_explainer
cwd = os.getcwd()
print(cwd)

from alibi.explainers import AnchorTabular

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

X_TRAIN_PATH ="pipeline/outputs/X_train.csv"
MODEL_PATH = "pipeline/outputs/best_model.joblib"
SAVE_PATH = "outputs/anchor_explainer.dill"

X_train = pd.read_csv(X_TRAIN_PATH)
print(X_train)
model = joblib.load(MODEL_PATH)
prediction_function = lambda x: model.predict(x)

#getting our feature names out now as we are going to convert our data to np array for anchor
feature_names = list(X_train.columns)

#defining our two categories for each column as absent (0) and present(1) - so anchor doesn't just assume continous 
categorical_names = {i: ["absent", "present"] for i in range(X_train.shape[1])}

#anchor requires a prediction function:
def predict_fn(x: np.ndarray) -> np.ndarray:
    return model.predict(x)

#converting data:
np_X_train = X_train.to_numpy()

explainer = AnchorTabular(predict_fn, feature_names=list(X_train.columns), categorical_names=categorical_names)
explainer.fit(np_X_train, disc_perc=(25, 50, 75)) #disc perc is required, but not used as data is categorical not continous 

#exporting explainer:
#could use dill, had some issues though, decided to just use alibi's built in explainer saver
save_explainer(explainer, "anchor/outputs/anchor_explainer")