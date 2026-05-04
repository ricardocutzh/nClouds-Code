import boto3
import json
import os
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns_client = boto3.client('sns')
DISTRIBUTION_TOPIC_ARN = os.environ['DISTRIBUTION_TOPIC_ARN']

def alarm_ok_state_message(alarm_name, region, reason):
    return (
        f"✅ ALARM OK: {alarm_name}\n"
        f"-------------------------------------\n"
        f"Status: OK\n"
        f"Region: {region}\n"
        f"Detail: {reason}\n"
        f"-------------------------------------\n"
        f"Action: No action needed, but please check the CloudWatch console for more details."
    )

def alarm_alarm_state_message(alarm_name, region, reason):
    return (
        f"🚨 ALARM TRIGGERED: {alarm_name}\n"
        f"-------------------------------------\n"
        f"Status: ALARM\n"
        f"Region: {region}\n"
        f"Detail: {reason}\n"
        f"-------------------------------------\n"
        f"Action: Please check the CloudWatch console for more details."
    )

def lambda_handler(event, context):
    # When triggered directly by CloudWatch Alarms, the event is the alarm JSON itself
    # We no longer loop through 'Records'
    logger.info(json.dumps(event))  # Log the raw event for debugging
    try:
        alarm_data = event["alarmData"]
        
        alarm_name = alarm_data["alarmName"]
        new_state = alarm_data["state"]["value"]
        reason = alarm_data["state"]["reason"]
        region = event["region"]

        # Rendering the readable string
        if new_state == "OK":
            readable_message = alarm_ok_state_message(alarm_name, region, reason)
        else:
            readable_message = alarm_alarm_state_message(alarm_name, region, reason)
            f"-------------------------------------\n"
            f"Action: Please check the CloudWatch console for more details."
        
        sns_client.publish(
            TopicArn=DISTRIBUTION_TOPIC_ARN,
            Subject=f"ABFilms Monitoring - Alert: {alarm_name} Change State",
            Message=readable_message
        )
        logger.info("Successfully processed alarm and sent notification.")
    except Exception as e:
        logger.error(f"Error parsing alarm: {str(e)}")
        logger.error(f"Event received: {json.dumps(event)}")