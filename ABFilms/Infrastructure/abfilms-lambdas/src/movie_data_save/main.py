import json
import logging
import boto3
import os
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SUPABASE_URL=os.environ.get("SUPABASE_URL")
SERVICE_ROLE_KEY=os.environ.get("SERVICE_ROLE_KEY")
SHOWS_PUBLIC_CLOUDFRONT_URL=os.environ.get("SHOWS_PUBLIC_CLOUDFRONT_URL")
DRM_ENABLED=os.environ.get("DRM_ENABLED")
DRM_LICENCE_URL=os.environ.get("DRM_LICENCE_URL")
ALLOW_SUPABASE_WRITE=os.environ.get("ALLOW_SUPABASE_WRITE")
headers = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def drm_enabled():
    if str(DRM_ENABLED) == "True":
        return True
    return False

def update_videos(data, video_id):
    thumbnail = data["Original_CSV_Data"]["PosterUrl"]
    video_data = {
        "title": f"{data["Original_CSV_Data"]["Movie/Show Title"]}",
        "description": f"{data["Original_CSV_Data"]["Movie/Show Synopsis"]}",
        "duration": int(data["Original_CSV_Data"]["Movie Running Time"]),
        "category": f"{data["Original_CSV_Data"]["Genre"]}",
        "thumbnail": str(thumbnail),
        "video_url": f"{data["UserMetadata"]["MasterFileURL"]}",
        "drm_protected": drm_enabled(),
        "drm_license_url": str(DRM_LICENCE_URL),
        "featured": True, # need to ask the value for this
        "release_year": int(data["Original_CSV_Data"]["Production Year"]),
        "rating":  f"{data["Original_CSV_Data"]["Rating"]}",
        "cast_members": str(data["Original_CSV_Data"]["Cast"]).split(","),
        "director": str(data["Original_CSV_Data"]["Director(s)"]),
        "trailer_url": f"{str(SHOWS_PUBLIC_CLOUDFRONT_URL)}/s3_key/img.mp4",
        "subscription_required": "premium",
        "is_premium": True,
        "quality": "HD",
        "producer": str(data["Original_CSV_Data"]["Producer(s)"]),
        "production_company": str(data["Original_CSV_Data"]["Studio"]),
        "genre": f"{data["Original_CSV_Data"]["Genre"]}",
        "is_rentable": True,
        "rental_price": 4.99
    }
    try:
        response = requests.patch(f"{SUPABASE_URL}/videos?id=eq.{video_id}", headers=headers, json=video_data)
        
        response.raise_for_status()
        
        result = response.json()

        return result[0] if isinstance(result, list) else result

    except Exception as e:
        logger.error(f"-- Function update_videos:  Error saving ing Supabase: {e}")
        raise Exception(f"-- Function update_videos:  Error saving ing Supabase: {e}")

def save_video(data):
    # save the video if episode does not exist in the video table
    # return video_id
    thumbnail = data["Original_CSV_Data"]["PosterUrl"]
    video_data = {
        "title": f"{data["Original_CSV_Data"]["Movie/Show Title"]}",
        "description": f"{data["Original_CSV_Data"]["Movie/Show Synopsis"]}",
        "duration": int(data["Original_CSV_Data"]["Movie Running Time"]),
        "category": f"{data["Original_CSV_Data"]["Genre"]}",
        "category": f"Test",
        "thumbnail": str(thumbnail),
        "video_url": f"{data["UserMetadata"]["MasterFileURL"]}",
        "drm_protected": drm_enabled(),
        "drm_license_url": str(DRM_LICENCE_URL),
        "featured": True, # need to ask the value for this
        "release_year": int(data["Original_CSV_Data"]["Production Year"]),
        "rating":  f"{data["Original_CSV_Data"]["Rating"]}",
        "cast_members": str(data["Original_CSV_Data"]["Cast"]).split(", "),
        "director": str(data["Original_CSV_Data"]["Director(s)"]),
        "trailer_url": f"{str(SHOWS_PUBLIC_CLOUDFRONT_URL)}/s3_key/img.mp4",
        "subscription_required": "premium",
        "is_premium": True,
        "quality": "HD",
        "producer": str(data["Original_CSV_Data"]["Producer(s)"]),
        "production_company": str(data["Original_CSV_Data"]["Studio"]),
        "genre": f"{data["Original_CSV_Data"]["Genre"]}",
        "genre": "Test",
        "is_rentable": True,
        "rental_price": 4.99
    }
    
    logger.info(json.dumps(video_data))
    try:
        response = requests.post(f"{SUPABASE_URL}/videos", headers=headers, json=video_data)
        
        response.raise_for_status()
        
        result = response.json()

        return result[0] if isinstance(result, list) else result

    except Exception as e:
        logger.error(f"-- Function save_video:  Error saving ing Supabase: {e}")
        raise Exception(f"-- Function save_video:  Error saving ing Supabase: {e}")

def video_exists(movie_title):
    # video_exists = select video where the title is $series_title Episode $episode_number - $episode_title
    # if episode exists:
    #   return return video.id
    # else:
    #   return 0
    # if seriest title exists on the series table:
    #   return series.id
    # else:
    # return 0
    target_title = f"{movie_title}"
    params = {
        "title": f"eq.{target_title}",
        "select": "id"
    }

    try:
        response = requests.get(
            f"{SUPABASE_URL}/videos", 
            headers=headers, 
            params=params
        )
        
        # Raise an exception for 4xx or 5xx errors
        response.raise_for_status()
        
        data = response.json()

        # 3. Evaluate results
        if data and len(data) > 0:
            # Return the id of the first match found
            return data[0].get('id')
        
        # Return -1 if the list is empty (no match)
        return -1

    except Exception as e:
        logger.error(f"-- Function video_exists:  Error querying Supabase: {e}")
        raise Exception(f"-- Function video_exists error {e}")

def get_video(data, movie_title):
    video_id = video_exists(movie_title)
    if video_id == -1:
        return save_video(data)["id"]
    return video_id

def lambda_handler(event, context):
    # 1. Print the event as a formatted JSON string
    # 'indent=4' makes it readable in CloudWatch
    logger.info(json.dumps(event))

    try:
        if ALLOW_SUPABASE_WRITE == "True":
            video_id = get_video(event, event["Original_CSV_Data"]["Movie/Show Title"])
            logger.info(f"-- video_id: {video_id}")

            logger.info(json.dumps(update_videos(event, video_id)))

            logger.info("-- Finish All Updates")
        else:
            logger.info(f"-- Supabase Updates Ignored because of flag: {ALLOW_SUPABASE_WRITE}")
        return event

    except Exception as e:
        logger.error(f">> Function: lambda_handler: {str(e)}")
        raise Exception(f">> Function: lambda_handler: {str(e)}")