import json
import logging
import boto3
import csv
import os
from pathlib import Path
from botocore.exceptions import ClientError
from datetime import datetime
import hashlib

# Best practice: Set up a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
sfn = boto3.client('stepfunctions')
movie_state_machine_arn = os.environ.get('MOVIE_STATE_MACHINE')
show_state_machine_arn = os.environ.get('SHOW_STATE_MACHINE')
environment = os.environ.get("ENVIRONMENT")

def csv_to_json_object(file_path: str):
    """
    Reads a CSV file and returns a list of dictionaries (JSON-like object).
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    data_list = []

    try:
        with open(path, mode='r', encoding='utf-8-sig') as f:
            # Using DictReader treats the first row as the keys
            # 'utf-8-sig' handles the BOM (Byte Order Mark) sometimes found in Excel-generated CSVs
            reader = csv.DictReader(f)
            
            for row in reader:
                # Clean the data: Strip whitespace from keys and values
                clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None}
                data_list.append(clean_row)

        # Log the JSON object (formatted for readability)
        logger.info(">> Successfully parsed CSV to JSON:")
        return data_list

    except Exception as e:
        logger.error(f">> Failed to process CSV: {e}")
        raise
        
def download_s3_to_local(bucket_name: str, s3_key: str, download_dir: str = "/tmp/") -> str:
    """
    Downloads an S3 object to a local directory and returns the absolute local path.
    """
    s3 = boto3.client('s3')
    
    filename = Path(s3_key).name
    local_directory = Path(download_dir)
    local_file_path = local_directory / filename

    try:
        logger.info(f">> Downloading {s3_key}...")
        
        # Boto3 download_file requires a string for the Filename argument
        s3.download_file(bucket_name, s3_key, str(local_file_path))
        
        # 3. Return the absolute path as a string
        return str(local_file_path.absolute())

    except ClientError as e:
        print(f"AWS Error: {e}")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

def lambda_handler(event, context):
    # 1. Print the event as a formatted JSON string
    # 'indent=4' makes it readable in CloudWatch
    logger.info(f">> Running Lambda:")
    logger.info(json.dumps(event))
    
    # 2. Extract specific data (Optional but helpful)
    try:
        data = {}

        bucket_name = event['detail']['bucket']['name']
        object_key = event['detail']['object']['key']
        metadatafile = f"s3://{bucket_name}/{object_key}"
        logger.info(f">> File uploaded: s3://{bucket_name}/{object_key}")

        saved_path = download_s3_to_local(bucket_name, object_key)
        logger.info(f">> File downloaded here: {saved_path}")

        metadata_json = csv_to_json_object(saved_path)

        for d in metadata_json:

            data = {
                's3_bucket': str(bucket_name),
                'parent_folder': str(object_key).split("/")[0],
                'origin_metadata_csv': str(object_key),
                'type': d["Program Type"].lower(),
                'env': str(environment),
                'original_data': d,
                'available_types': d["Avail Type(s)"].replace(" ", "").split(",")
            }
            

            now = datetime.now()
            timestamp_str = now.strftime("%Y%m%d%H%M%S%f")
            hash_input = f"{timestamp_str}".encode('utf-8')
            full_hash = hashlib.md5(hash_input).hexdigest()
            short_hash = full_hash[:10] # Take first 8 characters for readability
            sku = str(d["Movie/Show Filmhub SKU"]) if d["Program Type"] == "Movie" else str(d["Episode SKU"])

            safe_name = f"pln-{d["Program Type"].lower()}-{str(environment)}-{d["Movie/Show Title"].replace(" ", "")}-sku_{sku}-{short_hash}"

            if d["Program Type"] == "Movie":
                movie_subtitles_captions_languages = d["Movie Subtitles/Captions Languages"].replace(" ", "").split(",")
                movie_subtitles_captions_types = d["Movie Subtitles/Captions Types"].replace(" ", "").split(",")
                movie_subtitles_captions_filenames = d["Movie Subtitles/Captions Filenames"].replace(" ", "").split(",")
                subtitle_data = [
                    {"sub_language_code": lcode, "sub_type": stype, "sub_file_name": sfilename}
                    for lcode, stype, sfilename in zip(movie_subtitles_captions_languages, movie_subtitles_captions_types, movie_subtitles_captions_filenames)
                ]
                data["subtitles_data"] = subtitle_data
            if d["Program Type"] == "Show":
                show_subtitles_captions_languages = d["Episode Subtitles/Captions Languages"].replace(" ", "").split(",")
                show_subtitles_captions_types = d["Episode Subtitles/Captions Type"].replace(" ", "").split(",")
                show_subtitles_captions_filenames = d["Episode Subtitles/Captions Filenames"].replace(" ", "").split(",")
                subtitle_data = [
                    {"sub_language_code": lcode, "sub_type": stype, "sub_file_name": sfilename}
                    for lcode, stype, sfilename in zip(show_subtitles_captions_languages, show_subtitles_captions_types, show_subtitles_captions_filenames)
                ]
                data["subtitles_data"] = subtitle_data
                data["episode_name"] = d["Episode Name"]
                data["season_number"] = d["Season Number"]
                data["episode_number"] = d["Episode Number"]

            logger.info(json.dumps(data))
            
        return True
        
    except KeyError as e:
        logger.error(f">> Error parsing event: Missing key {str(e)}")
        return {
            "statusCode": 400,
            "body": "Invalid event format"
        }

    return {
        "statusCode": 200,
        "body": json.dumps(">> Event logged successfully")
    }