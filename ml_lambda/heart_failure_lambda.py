import json
from util import test_predict, prediction
import logging
import os
import pandas as pd
import joblib

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

mount_dir = "/mnt/model"
heart_model = None

# def _test_predict():
#     global heart_model
#     heart_model = joblib.load(f"{mount_dir}/heart_model.pkl")
#     new_sample = [[54, 'M', 'NAP', 150, 195, 0, 'Normal', 122, 'N', 0.0, 'Up']]
#     new_sample_df = pd.DataFrame(data=new_sample,
#                                  columns=['Age', 'Sex', 'ChestPainType', 'RestingBP', 'Cholesterol', 'FastingBS',
#                                           'RestingECG', 'MaxHR', 'ExerciseAngina', 'Oldpeak', 'ST_Slope'])
#
#     print(new_sample_df)
#     y_pred = heart_model.predict(new_sample_df)
#     print(f"*******: {y_pred}")
#
# def _new_prediction(event):
#     try:
#         method = event['requestContext']['http']['method']
#         pred = None
#         if method == 'POST':
#             print("POST")
#             print(event['body'])
#             data = json.loads(event['body'])
#             df = pd.DataFrame.from_dict([data], orient="columns")
#             print(f"df: {df}")
#             pred = heart_model.predict(df)
#             print(f"POST prediction: {pred}")
#     except Exception as exc:
#         print("ERROR ERROR")
#         print(exc)
#         pred = [-1.0]
#
#     return pred

def lambda_handler(event, context):
    global heart_model

    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    logger.debug(f"Heart Failure ML Inference Event: {event}")

    # print the directory contents so we can make sure
    # the lambda and ec2 see the same diretory contents
    logger.debug(f"ListDir: {os.listdir(mount_dir)}")

    # load the heart model from the filesystem
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
