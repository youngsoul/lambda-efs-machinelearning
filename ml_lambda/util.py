import pandas as pd
import logging

"""
Utility file used primary to test the ability for a Lambda to pull in
other local scripts
"""


def test_predict(model, new_rec):
    new_sample = [new_rec]
    new_sample_df = pd.DataFrame(data=new_sample,
                                 columns=['Age', 'Sex', 'ChestPainType', 'RestingBP', 'Cholesterol', 'FastingBS',
                                          'RestingECG', 'MaxHR', 'ExerciseAngina', 'Oldpeak', 'ST_Slope'])

    logging.getLogger().debug(new_sample_df)
    y_pred = model.predict(new_sample_df)
    return y_pred


def prediction(model, json_data_rec):
    try:
        df = pd.DataFrame.from_dict([json_data_rec], orient="columns")
        pred = model.predict(df)

    except Exception as exc:
        logging.getLogger().error("ERROR ERROR")
        logging.getLogger().error(exc)
        pred = [-1.0]

    return pred
