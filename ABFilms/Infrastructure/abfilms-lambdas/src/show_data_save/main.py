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

# returns boolean
def series_exist(series_title):
    # if seriest title exists on the series table:
    #   return series.id
    # else:
    # return 0
    params = {
        "title": f"eq.{series_title}",
        "select": "id"
    }

    try:
        response = requests.get(
            f"{SUPABASE_URL}/series", 
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
        logger.error(f"Error querying Supabase: {e}")
        raise Exception(f"-- Function {series_exist} error {e}")
        
def video_exists(series_title, episode_number, episode_title):
    # video_exists = select video where the title is $series_title Episode $episode_number - $episode_title
    # if episode exists:
    #   return return video.id
    # else:
    #   return 0
    # if seriest title exists on the series table:
    #   return series.id
    # else:
    # return 0
    target_title = f"{series_title} - Episode {episode_number} - {episode_title}"
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

def episode_exists(serie_id, video_id):
    # episode_id = select from series_episodes where series_id and video_id
    # if episode_id:
    #   return episode_id
    # else:
    #   return 0
    
    params = {
        "series_id": f"eq.{serie_id}",
        "video_id": f"eq.{video_id}",
        "select": "id"
    }

    try:
        response = requests.get(
            f"{SUPABASE_URL}/series_episodes", 
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
        logger.error(f"-- Function episode_exists:  Error querying Supabase: {e}")
        raise Exception(f"-- Function episode_exists error {e}")

def save_video(data):
    # save the video if episode does not exist in the video table
    # return video_id
    video_data = {
        "title": f"{data["Original_CSV_Data"]["Movie/Show Title"]} - Episode {data["Original_CSV_Data"]["Episode Number"]} - {data["Original_CSV_Data"]["Episode Name"]}",
        "description": f"{data["Original_CSV_Data"]["Episode Synopsis"]}",
        "duration": int(data["Original_CSV_Data"]["Episode Running Time"]),
        #"category": f"{data["Original_CSV_Data"]["Genre"]}",
        "thumbnail": f"{str(SHOWS_PUBLIC_CLOUDFRONT_URL)}/s3_key/img.jpg",
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
        response = requests.post(f"{SUPABASE_URL}/videos", headers=headers, json=video_data)
        
        response.raise_for_status()
        
        result = response.json()

        return result[0] if isinstance(result, list) else result

    except Exception as e:
        logger.error(f"-- Function save_video:  Error saving ing Supabase: {e}")
        raise Exception(f"-- Function save_video:  Error saving ing Supabase: {e}")
        

def save_series(data):
    # save the series and return id
    series_data = {
        "title": f"{data["Original_CSV_Data"]["Movie/Show Title"]}",
        "description": f"{data["Original_CSV_Data"]["Episode Synopsis"]}",
        "poster_url": f"{str(SHOWS_PUBLIC_CLOUDFRONT_URL)}/s3_key/img.jpg",
        "trailer_url": f"{str(SHOWS_PUBLIC_CLOUDFRONT_URL)}/s3_key/img.mp4",
        "director": str(data["Original_CSV_Data"]["Director(s)"]),
        "release_year": int(data["Original_CSV_Data"]["Production Year"]),
        "rating":  f"{data["Original_CSV_Data"]["Rating"]}",
        "is_premium": True,
        "featured": True, # need to ask the value for this
        "status": "upcoming",
        "total_seasons": 0, # first time it is created
        "total_episodes": 0 # first time it is created
        "genre": f"{data["Original_CSV_Data"]["Genre"]}",
        "is_rentable": True,
        "rental_price": 4.99
    }
    try:
        response = requests.post(f"{SUPABASE_URL}/series", headers=headers, json=video_data)
        
        response.raise_for_status()
        
        result = response.json()

        return result[0] if isinstance(result, list) else result

    except Exception as e:
        logger.error(f"-- Function save_series:  Error saving ing Supabase: {e}")
        raise Exception(f"-- Function save_series:  Error saving ing Supabase: {e}")

def save_episode(data):
    # save the episode 
    pass


def lambda_handler(event, context):
    # 1. Print the event as a formatted JSON string
    # 'indent=4' makes it readable in CloudWatch
    logger.info(json.dumps(event))

    try:
        # series_id = series_exist("Buster Beaver")
        # logger.info(f"series id: {series_id}")

        # video_id = video_exists("Buster Beaver", 6, "Love At First Fright")
        # logger.info(f"video id: {video_id}")

        # series_episode_id = episode_exists(series_id, video_id)
        # logger.info(f"series_episode id: {series_episode_id}")
        # return event        
        save_video(event)
    except Exception as e:
        logger.error(f">> Function: lambda_handler: {str(e)}")
        raise Exception(f">> Function: lambda_handler: {str(e)}")