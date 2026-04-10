import json
import logging
import boto3
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(json.dumps(event))

    return {
        "statusCode": 200,
        "body": json.dumps(">> Event logged successfully")
    }