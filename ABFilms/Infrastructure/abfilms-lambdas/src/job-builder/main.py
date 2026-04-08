import json
import logging
import boto3
import os
from jinja2 import Template
import pycountry

environment = os.environ.get("ENVIRONMENT")
cf_endpoint = os.environ.get("CLOUDFRONT_ENDPOINT")
drm_api_endpoint = os.environ.get("DRMTODAY_API_ENDPOINT")
drm_system_ids = str(os.environ.get("DRMTODAY_SYSTEM_IDS"))

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# reference here: https://docs.aws.amazon.com/sdk-for-ruby/v2/api/Aws/MediaConvert/Types/HlsCaptionLanguageMapping.html
# language_codes = [
#     "ENG", "SPA", "FRA", "DEU", "GER", "ZHO", "ARA", "HIN", "JPN", "RUS", 
#     "POR", "ITA", "URD", "VIE", "KOR", "PAN", "ABK", "AAR", "AFR", "AKA", 
#     "SQI", "AMH", "ARG", "HYE", "ASM", "AVA", "AVE", "AYM", "AZE", "BAM", 
#     "BAK", "EUS", "BEL", "BEN", "BIH", "BIS", "BOS", "BRE", "BUL", "MYA", 
#     "CAT", "KHM", "CHA", "CHE", "NYA", "CHU", "CHV", "COR", "COS", "CRE", 
#     "HRV", "CES", "DAN", "DIV", "NLD", "DZO", "ENM", "EPO", "EST", "EWE", 
#     "FAO", "FIJ", "FIN", "FRM", "FUL", "GLA", "GLG", "LUG", "KAT", "ELL", 
#     "GRN", "GUJ", "HAT", "HAU", "HEB", "HER", "HMO", "HUN", "ISL", "IDO", 
#     "IBO", "IND", "INA", "ILE", "IKU", "IPK", "GLE", "JAV", "KAL", "KAN", 
#     "KAU", "KAS", "KAZ", "KIK", "KIN", "KIR", "KOM", "KON", "KUA", "KUR", 
#     "LAO", "LAT", "LAV", "LIM", "LIN", "LIT", "LUB", "LTZ", "MKD", "MLG", 
#     "MSA", "MAL", "MLT", "GLV", "MRI", "MAR", "MAH", "MON", "NAU", "NAV", 
#     "NDE", "NBL", "NDO", "NEP", "SME", "NOR", "NOB", "NNO", "OCI", "OJI", 
#     "ORI", "ORM", "OSS", "PLI", "FAS", "POL", "PUS", "QUE", "QAA", "RON", 
#     "ROH", "RUN", "SMO", "SAG", "SAN", "SRD", "SRB", "SNA", "III", "SND", 
#     "SIN", "SLK", "SLV", "SOM", "SOT", "SUN", "SWA", "SSW", "SWE", "TGL", 
#     "TAH", "TGK", "TAM", "TAT", "TEL", "THA", "BOD", "TIR", "TON", "TSO", 
#     "TSN", "TUR", "TUK", "TWI", "UIG", "UKR", "UZB", "VEN", "VOL", "WLN", 
#     "CYM", "FRY", "WOL", "XHO", "YID", "YOR", "ZHA", "ZUL", "ORJ", "QPC", "TNG"
# ]

def setup_drm_encryption(result_object, resource_id):
    for og in result_object["Settings"]["OutputGroups"]:
        og["OutputGroupSettings"]["HlsGroupSettings"]["Encryption"] = {
            "EncryptionMethod": "SAMPLE_AES",
            "SpekeKeyProvider": {
                "ResourceId": str(resource_id),
                "SystemIds": drm_system_ids.split(","),
                "Url": str(drm_api_endpoint)
            },
            "Type": "SPEKE"
        }

def map_to_mediaconvert_lang(input_code):
    """
    Maps any language input (2-letter, 3-letter, or name) to 
    the strict 3-letter Terminology code supported by MediaConvert.
    """
    # 1. Clean the input
    raw_code = str(input_code).strip().upper()
    
    # 2. Hardcoded Overrides for regional and tricky terminology codes
    # MediaConvert needs these specific 3-letter strings
    overrides = {
        "ES-419": {"LanguageCode": "SPA", "LanguageDescription": "Spanish"},
        "CS":     {"LanguageCode": "CES", "LanguageDescription": "Czech"},
        "CZ":     {"LanguageCode": "CES", "LanguageDescription": "Czech"},
        "DE":     {"LanguageCode": "DEU", "LanguageDescription": "German"},
        "FR":     {"LanguageCode": "FRA", "LanguageDescription": "French"},
        "NL":     {"LanguageCode": "NLD", "LanguageDescription": "Dutch"},
        "HY":     {"LanguageCode": "HYE", "LanguageDescription": "Armenian"},
        "EN":     {"LanguageCode": "ENG", "LanguageDescription": "English"}
    }
    
    if raw_code in overrides:
        return overrides[raw_code]

    # 3. Dynamic Lookup using pycountry
    try:
        # .lookup is smart: it checks names, alpha_2, and alpha_3
        lang = pycountry.languages.lookup(raw_code)
        
        # MediaConvert prefers the 'terminology' code (3 letters)
        # If terminology doesn't exist, fall back to alpha_3
        mc_code = getattr(lang, 'terminology', lang.alpha_3)
        mc_desc = lang.name
        
        return {
            "LanguageCode": mc_code.upper(), 
            "LanguageDescription": mc_desc
        }
    except Exception as e:
        logger.error(f">> Function: map_to_mediaconvert_lang: {str(e)}")
        raise Exception(f">> Function: map_to_mediaconvert_lang: {str(e)}")

def generate_captions(subtitles_data, input_bucket, input_folder):

    base_path = f"s3://{input_bucket}/{input_folder}"

    selectors = {}
    subtitles_outputs = []

    for s in subtitles_data:
        lang = s['sub_language_code']
        lang = lang.upper()
        selectors[lang] = {
            "SourceSettings": {
                "SourceType": "SRT",
                "FileSourceSettings": {
                    "SourceFile": f"{base_path}/{s["sub_file_name"]}"
                }
            }
        }

        language_object = map_to_mediaconvert_lang(lang)

        if language_object is None:
            subtitles_outputs.append(
                {
                    "NameModifier": f"_vtt_{lang.lower()}",
                    "ContainerSettings": {
                        "Container": "M3U8"
                    },
                    "CaptionDescriptions": [
                        {
                            "CaptionSelectorName": f"{lang}",
                            "DestinationSettings": {
                                "DestinationType": "WEBVTT"
                            }
                        }
                    ]
                }
            )
        else:
            subtitles_outputs.append(
                {
                    "NameModifier": f"_vtt_{lang.lower()}",
                    "ContainerSettings": {
                        "Container": "M3U8"
                    },
                    "CaptionDescriptions": [
                        {
                            "CaptionSelectorName": f"{lang}",
                            "DestinationSettings": {
                                "DestinationType": "WEBVTT"
                            },
                            "LanguageCode": f"{language_object["LanguageCode"]}",
                            "LanguageDescription": f"{language_object["LanguageDescription"]}"
                        }
                    ]
                }
            )

    return {
        "caption_selectors": selectors,
        "subtitles_outputs": subtitles_outputs
    }

def add_captions_descriptions(processed_object, caption_descriptions):

    print("adding caption descriptions")

    for c in caption_descriptions:
        processed_object["Settings"]["OutputGroups"][0]["Outputs"].append(c)

def add_metadata(type, result_object, original_data):

    metadata = {}
    MasterFileUrl = None

    if type == "show":
        Season = f"Season_{original_data["Season Number"].replace(" ", "")}"
        EpisodeNumber = f"Episode_{original_data["Episode Number"].replace(" ", "")}"
        EpisodeName = original_data["Episode Name"].replace(" ", "_")
        Title = original_data["Movie/Show Title"].replace(" ", "_")
        if drm_api_endpoint != "NOT_SET" and drm_system_ids != "NOT_SET":
            MasterFileUrl = f"https://{cf_endpoint}/Shows/{Title}/{Season}/{EpisodeNumber}_{EpisodeName}_{original_data["Episode SKU"]}/output/hls/index.m3u8"
        else: 
            MasterFileUrl = f"https://{cf_endpoint}/Shows/{Title}/{Season}/{EpisodeNumber}_{EpisodeName}/output/hls/index.m3u8"
        metadata = {
            "Type": "Show",
            "Environment": str(environment),
            "Season": str(Season),
            "Episode": str(EpisodeNumber),
            "Episode Name": str(EpisodeName),
            "Title": str(Title),
            "MasterFileURL": str(MasterFileUrl)
        }
        
    if type == "movie":
        Title = original_data["Movie/Show Title"].replace(" ", "_")
        if drm_api_endpoint != "NOT_SET" and drm_system_ids != "NOT_SET":
            MasterFileUrl = f"https://{cf_endpoint}/Movies/{Title}_{original_data["Movie/Show Filmhub SKU"]}/output/hls/index.m3u8"
        else: 
            MasterFileUrl = f"https://{cf_endpoint}/Movies/{Title}/output/hls/index.m3u8"
        metadata = {
            "Type": "Movie",
            "Environment": str(environment),
            "Title": str(Title),
            "MasterFileURL": str(MasterFileUrl)
        }

    result_object["UserMetadata"] = metadata

def add_selectos(processed_object, caption_selectors):

    processed_object["Settings"]["Inputs"][0]["CaptionSelectors"] = caption_selectors

def lambda_handler(event, context):
    # 1. Print the event as a formatted JSON string
    # 'indent=4' makes it readable in CloudWatch
    logger.info(f">> Running Lambda:")
    logger.info(json.dumps(event))

    try:

        generated_captions = generate_captions(event["subtitles_data"], event["s3_bucket"], event["parent_folder"])

        destination = None
        input_mp4_file = None
        resource_id = None

        if event["type"] == "movie":
            if drm_api_endpoint != "NOT_SET" and drm_system_ids != "NOT_SET":
                destination = f"s3://{event["out_s3_bucket"]}/Movies/{event["original_data"]["Movie/Show Title"].replace(" ", "_")}_{event["original_data"]["Movie/Show Filmhub SKU"]}/output/hls/index"
            else:
                destination = f"s3://{event["out_s3_bucket"]}/Movies/{event["original_data"]["Movie/Show Title"].replace(" ", "_")}/output/hls/index"
            input_mp4_file = event["original_data"]["Movie Filename"]
            resource_id = f"{event["original_data"]["Movie/Show Filmhub SKU"]}"
        if event["type"] == "show":
            input_mp4_file = event["original_data"]["Episode Filename"]
            Season = f"Season_{event["original_data"]["Season Number"].replace(" ", "")}"
            EpisodeNumber = f"Episode_{event["original_data"]["Episode Number"].replace(" ", "")}"
            EpisodeName = event["original_data"]["Episode Name"].replace(" ", "_")
            Title = event["original_data"]["Movie/Show Title"].replace(" ", "_")
            if drm_api_endpoint != "NOT_SET" and drm_system_ids != "NOT_SET":
                destination = f"s3://{event["out_s3_bucket"]}/Shows/{Title}/{Season}/{EpisodeNumber}_{EpisodeName}_{event["original_data"]["Episode SKU"]}/output/hls/index"
            else:
                destination = f"s3://{event["out_s3_bucket"]}/Shows/{Title}/{Season}/{EpisodeNumber}_{EpisodeName}/output/hls/index"
            resource_id = f"{event["original_data"]["Episode SKU"]}"

        variables = {
            "mediaconvert_queue": event["mediaconvert_queue"],
            "mediaconvert_role": event["mediaconvert_role"],
            "input_bucket": event["s3_bucket"],
            "input_folder": event["parent_folder"],
            "input_mp4_file": input_mp4_file,
            "out_s3_bucket": event["out_s3_bucket"],
            "destination": destination
        }

        with open('templates/job-template.json', 'r') as f:
            template_content = f.read()

        template = Template(template_content)
        final_output = template.render(variables)
        json_object = json.loads(final_output)

        add_selectos(json_object, generated_captions["caption_selectors"])

        add_captions_descriptions(json_object, generated_captions["subtitles_outputs"] )

        logger.info(json.dumps(json_object))

        add_metadata(event["type"], json_object, event["original_data"])

        json_object["Original_CSV_Data"] = event["original_data"]

        if drm_api_endpoint != "NOT_SET" and drm_system_ids != "NOT_SET":
            setup_drm_encryption(json_object, resource_id)
        return json_object
    except Exception as e:
        logger.error(f">> Function: lambda_handler: {str(e)}")
        raise Exception(f">> Function: lambda_handler: {str(e)}")