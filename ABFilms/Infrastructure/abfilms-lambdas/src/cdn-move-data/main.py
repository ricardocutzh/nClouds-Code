import json
import logging
import boto3
import os
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

environment = os.environ.get("ENVIRONMENT")
cdn_bucket = os.environ.get("CDN_S3_BUCKET")
ingest_bucket = os.environ.get("INGEST_BUCKET")
CLOUDFRONT_ENDPOINT = os.environ.get("CLOUDFRONT_ENDPOINT")

s3 = boto3.resource('s3')

def get_result_key(event):
    result_key = None
    if event["UserMetadata"]["Type"] == "Movie":
        result_key = f"{event["UserMetadata"]["Type"]}/{event["UserMetadata"]["Title"]}/static"
    else:
        result_key = f"{event["UserMetadata"]["Type"]}/{event["UserMetadata"]["Title"]}/{event["UserMetadata"]["Season"]}/{event["UserMetadata"]["Episode"]}_{event["UserMetadata"]["Episode Name"]}/static"

    return result_key

def copy_to_s3(event, parent_folder, filename):
    copy_source = {
        'Bucket': str(ingest_bucket),
        'Key': f"{parent_folder}/{filename}"
    }

    result_key = get_result_key(event)

    s3.meta.client.copy(copy_source, str(cdn_bucket), f"{result_key}/{filename}")

    logger.info(f"-- Moved file to {cdn_bucket}/{result_key}/{filename}")
    time.sleep(3)


def move_images(event):
    img_2_3 = event["Original_CSV_Data"]["Key Art 2:3 Filename"]
    img_3_4 = event["Original_CSV_Data"]["Key Art 3:4 Filename"]
    img_16_9 = event["Original_CSV_Data"]["Key Art 16:9 Filename"]
    other_key_art_imgs = str(event["Original_CSV_Data"]["Other Key Art Filenames"]).split(", ")
    other_images = str(event["Original_CSV_Data"]["Other Images Filenames"]).split(", ")

    copy_to_s3(event, event["ParentS3Folder"], img_2_3)

    copy_to_s3(event, event["ParentS3Folder"], img_3_4)

    copy_to_s3(event, event["ParentS3Folder"], img_16_9)

    try:

        for img in other_key_art_imgs:
            copy_to_s3(event, event["ParentS3Folder"], img)

        for img in other_images:
            copy_to_s3(event, event["ParentS3Folder"], img)
    except Exception as e:
        logger.error(f"-- Error: {str(e)}")
        return False

    return True

def move_trailer(event):
    trailer_file_name = None
    if event["Original_CSV_Data"]["Trailer"] == "Yes":
        trailer_file_name = event["Original_CSV_Data"]["Trailer Filename"]
        copy_to_s3(event, event["ParentS3Folder"], trailer_file_name)
    return True

def lambda_handler(event, context):
    logger.info(f">> Running Lambda:")
    logger.info(json.dumps(event))

    try:
        move_images(event)
        move_trailer(event)
        result_key = get_result_key(event)

        event["UserMetadata"]["PosterUrl"] = f"{CLOUDFRONT_ENDPOINT}/{result_key}/{event["Original_CSV_Data"]["Key Art 2:3 Filename"]}"
        event["UserMetadata"]["Thumbnail16_9Url"] = f"{CLOUDFRONT_ENDPOINT}/{result_key}/{event["Original_CSV_Data"]["Key Art 16:9 Filename"]}"
        if event["Original_CSV_Data"]["Trailer"] == "Yes":
            event["UserMetadata"]["TrailerUrl"] = f"{CLOUDFRONT_ENDPOINT}/{result_key}/{event["Original_CSV_Data"]["Trailer Filename"]}"
        return event
    except Exception as e:
        logger.error(f">> Function: lambda_handler: {str(e)}")
        raise Exception(f">> Function: lambda_handler: {str(e)}")