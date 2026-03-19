import json
import logging

# Best practice: Set up a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # 1. Print the event as a formatted JSON string
    # 'indent=4' makes it readable in CloudWatch
    print("Received event:")
    print(json.dumps(event, indent=4))
    
    # 2. Extract specific data (Optional but helpful)
    try:
        bucket_name = event['detail']['bucket']['name']
        object_key = event['detail']['object']['key']
        
        logger.info(f"File uploaded: s3://{bucket_name}/{object_key}")
        
        # Your processing logic for .csv files goes here
        
    except KeyError as e:
        logger.error(f"Error parsing event: Missing key {str(e)}")
        return {
            "statusCode": 400,
            "body": "Invalid event format"
        }

    return {
        "statusCode": 200,
        "body": json.dumps("Event logged successfully")
    }