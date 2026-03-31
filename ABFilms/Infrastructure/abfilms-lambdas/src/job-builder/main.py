import json
import logging
import boto3
import os
from jinja2 import Template

environment = os.environ.get("ENVIRONMENT")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def generate_captions(subtitles_data, input_bucket, input_folder):

    base_path = f"s3://{input_bucket}/{input_folder}"

    selectors = {}
    descriptions = []

    for s in subtitles_data:
        lang = s['sub_language_code']
        selectors[lang] = {
            "SourceSettings": {
                "SourceType": "SRT",
                "FileSourceSettings": {
                    "SourceFile": f"{base_path}/{s["sub_file_name"]}"
                }
            }
        }

        descriptions.append({
            "CaptionSelectorName": lang,
            "DestinationSettings": {
                "DestinationType": "DVB_SUB"
            },
            #"LanguageCode": lang.upper()[:3] if len(lang) >= 2 else "ENG",
            "LanguageDescription": f"Subtitles {lang}"
        })

    return {
        "caption_selectors": selectors,
        "caption_descriptions": descriptions
    }

def add_captions_descriptions(processed_object, caption_descriptions):
    
    for output in processed_object["Settings"]["OutputGroups"]:
        for o in output["Outputs"]:
            o["CaptionDescriptions"] = caption_descriptions


def add_selectos(processed_object, caption_selectors):

    processed_object["Settings"]["Inputs"][0]["CaptionSelectors"] = caption_selectors

def lambda_handler(event, context):
    # 1. Print the event as a formatted JSON string
    # 'indent=4' makes it readable in CloudWatch
    logger.info(f">> Running Lambda:")
    logger.info(json.dumps(event))

    try:

        generated_captions = generate_captions(event["subtitles_data"], event["s3_bucket"], event["parent_folder"])

        variables = {
            "mediaconvert_queue": event["mediaconvert_queue"],
            "mediaconvert_role": event["mediaconvert_role"],
            "input_bucket": event["s3_bucket"],
            "input_folder": event["parent_folder"],
            "input_mp4_file": event["original_data"]["Movie Filename"],
            "out_s3_bucket": event["out_s3_bucket"]
        }

        with open('templates/job-template.json', 'r') as f:
            template_content = f.read()

        template = Template(template_content)
        final_output = template.render(variables)
        json_object = json.loads(final_output)

        add_selectos(json_object, generated_captions["caption_selectors"])

        add_captions_descriptions(json_object, generated_captions["caption_descriptions"] )

        #logger.info(generated_captions)

        print(json.dumps(json_object))
        return json_object
    except Exception as e:
        logger.error(f">> Error parsing event: Missing key {str(e)}")
        return {
            "statusCode": 400,
            "body": "Invalid event format"
        }