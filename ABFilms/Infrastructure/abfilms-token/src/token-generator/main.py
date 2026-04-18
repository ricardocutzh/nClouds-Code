import json
import time
import jwt
import uuid
import datetime
import codecs
from botocore.exceptions import ClientError
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    secret_name = os.environ.get('DRM_SECRET_NAME')
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')

    try:
        logger.info(json.dumps(event))
        secret_name = os.environ.get('DRM_SECRET_NAME')
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager')
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)

        secret_string = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret_string)

        asset_id = json.loads(event["body"])["AssetId"]

        org_id = secret_dict.get('org_id')
        kid = secret_dict.get('shared_secret_kid')
        shared_secret_value = secret_dict.get('shared_secret_value')

        shared_secret_bytes = codecs.decode(shared_secret_value, 'hex')

        custom_data = {"merchant": org_id, "userId": "testuser-id"}
        customer_rights_token = { 'assetId': str(asset_id)}
        header_params = {"kid": kid}
        now = datetime.datetime.now()
        payload_claims = {
            "jti": str(uuid.uuid4()), # unique identifier for the token
            "iat": int(now.timestamp()), # timestamp of the request in seconds since epoch
            "exp": int((now + datetime.timedelta(minutes=10)).timestamp()), # optional expiration time
            "optData": json.dumps(custom_data),
            "crt": json.dumps(customer_rights_token),
        }
        token = jwt.encode(payload_claims, shared_secret_bytes, algorithm='HS256', headers=header_params)
        logger.info(f'Generated JWT token:\n{token}')

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*", # Must match the API Gateway config
                "Access-Control-Allow-Methods": "POST,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key"
            },
            "body": json.dumps({"token": f"{token}"})
        }


    except Exception as e:
        logger.error(f"-- Error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"{e}"})
        }