import json
import logging
import urllib3
import os

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Slack Webhook URL from Environment Variables
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')

def send_slack_payload(payload):
    """Internal helper to send the formatted JSON to Slack."""
    if not SLACK_WEBHOOK_URL:
        logger.error("SLACK_WEBHOOK_URL is not configured in environment variables.")
        return None

    http = urllib3.PoolManager()
    try:
        response = http.request(
            'POST',
            SLACK_WEBHOOK_URL,
            body=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        return response.status
    except Exception as e:
        logger.error(f"Error sending to Slack: {e}")
        return None

def status_succeeded(detail):
    """Processes 'SUCCEEDED' status using keys from Original_CSV_Data."""
    output = json.loads(detail.get('output', '{}'))
    csv_data = output.get('Original_CSV_Data', {})
    
    execution_arn = detail.get('executionArn')
    region = execution_arn.split(':')[3]
    console_link = f"https://{region}.console.aws.amazon.com/states/home?region={region}#/executions/details/{execution_arn}"

    prog_type = csv_data.get('Program Type', 'Unknown')
    title = csv_data.get('Movie/Show Title', 'Unknown Asset')
    genre = csv_data.get('Genre', 'N/A')

    # Build information string based on Program Type
    if prog_type == "Movie":
        info_text = (
            f"🎥 *Asset Name:* {title}\n"
            f"📂 *Pipeline:* Movie\n"
            f"🎭 *Genre:* {genre}"
        )
    else:
        ep_name = csv_data.get('Episode Name', 'N/A')
        season = csv_data.get('Season Number', 'N/A')
        episode = csv_data.get('Episode Number', 'N/A')
        info_text = (
            f"📺 *Show Name:* {title}\n"
            f"🎬 *Episode Processed:* {ep_name}\n"
            f"🔢 *Season:* {season} | *Episode:* {episode}\n"
            f"🎭 *Genre:* {genre}"
        )

    payload = {
        "attachments": [{
            "color": "#2ecc71",
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"✅ {prog_type.upper()} Pipeline Succeeded", "emoji": True}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": info_text}
                },
                {
                    "type": "actions",
                    "elements": [{
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Result"},
                        "url": console_link,
                        "style": "primary"
                    }]
                }
            ]
        }]
    }
    return send_slack_payload(payload)

def status_failed(detail):
    """Processes 'FAILED' status using keys from the input metadata."""
    # We use 'input' for failures because 'output' does not exist on failure
    input_data = json.loads(detail.get('input', '{}'))
    
    # Check if input has the CSV data structure or is a direct object
    csv_data = input_data.get('original_data', input_data)
    
    prog_type = csv_data.get('Program Type', 'Unknown Asset')
    title = csv_data.get('Movie/Show Title', 'Unknown Title')
    error_name = detail.get('error', 'ExecutionError')
    cause = detail.get('cause', 'Detailed cause not provided.')

    execution_arn = detail.get('executionArn')
    region = execution_arn.split(':')[3]
    console_link = f"https://{region}.console.aws.amazon.com/states/home?region={region}#/executions/details/{execution_arn}"

    payload = {
        "attachments": [{
            "color": "#e74c3c",
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"❌ {prog_type.upper()} Pipeline Failed", "emoji": True}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Asset:* {title}\n*Type:* {prog_type}\n*Error:* `{error_name}`"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Cause:* {cause}\n"}
                },
                {
                    "type": "actions",
                    "elements": [{
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Debug in Console"},
                        "url": console_link,
                        "style": "danger"
                    }]
                }
            ]
        }]
    }
    return send_slack_payload(payload)

def lambda_handler(event, context):
    """Main Entry Point for EventBridge Step Function events."""
    detail = event.get('detail', {})
    status = detail.get('status')

    logger.info(json.dumps(detail))

    logger.info(f"Received {status} event for: {detail.get('executionArn')}")

    if status == "SUCCEEDED":
        status_succeeded(detail)
    elif status == "FAILED":
        status_failed(detail)
    else:
        logger.info(f"Skipping notification for status: {status}")

    return {"statusCode": 200}