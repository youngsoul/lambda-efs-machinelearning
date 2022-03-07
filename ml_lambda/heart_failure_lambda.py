import json
import logging
import os
import pandas as pd
import joblib

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

mount_dir = "/mnt/model"
heart_model = None

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

def lambda_handler(event, context):
    global heart_model
    logger.debug(f"Heart Failure ML Inference Event: {event}")

    # print the directory contents so we can make sure
    # the lambda and ec2 see the same diretory contents
    logger.debug(f"ListDir: {os.listdir(mount_dir)}")

    # load the heart model from the filesystem
    if heart_model is None:
        heart_model = joblib.load(f"{mount_dir}/heart_model.pkl")

    # call test_predict which uses a fixed data record
    test_pred = test_predict(model=heart_model, new_rec=[54, 'M', 'NAP', 150, 195, 0, 'Normal', 122, 'N', 0.0, 'Up'])
    logger.debug(f"Test Prediction should be [0]: {test_pred}")

    # see if this is a POST request event and if so read the
    # new data payload to make a prediction on
    pred = "N/A"
    try:
        if 'requestContext' in event and 'http' in event['requestContext']:
            method = event['requestContext']['http']['method']
            if method == 'POST':
                logger.debug("POST")
                logger.debug(event['body'])
                data = json.loads(event['body'])
                pred = prediction(heart_model, data)
    except Exception as exc:
        logger.error("ERROR in handling POST request")
        logger.error(exc)

    logger.info(f"Heart Failure Prediction: {pred}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "heart failure prediction",
            "prediction": f"{pred}"
        }),
    }
