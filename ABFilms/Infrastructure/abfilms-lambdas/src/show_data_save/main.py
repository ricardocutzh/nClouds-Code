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

def get_video(data, series_title, episode_number, episode_title):
    video_id = video_exists(series_title, episode_number, episode_title)
    if video_id == -1:
        return save_video(data)["id"]
    return video_id

def get_series(data, series_title):
    serie_id = series_exist(series_title)
    if serie_id == -1:
        return save_series(data)["id"]
    return serie_id

def get_series_episode(data, serie_id, video_id):
    episode_id = episode_exists(serie_id, video_id)
    if episode_id == -1:
        return save_episode(data, serie_id, video_id)["id"]
    return episode_id

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
        "category": f"{data["Original_CSV_Data"]["Genre"]}",
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
    rating = "PG" if str(data["Original_CSV_Data"]["Rating"]) == "" else str(data["Original_CSV_Data"]["Rating"])
    series_data = {
        "title": f"{data["Original_CSV_Data"]["Movie/Show Title"]}",
        "description": f"{data["Original_CSV_Data"]["Episode Synopsis"]}",
        "category": f"{data["Original_CSV_Data"]["Genre"]}",
        "poster_url": f"{str(SHOWS_PUBLIC_CLOUDFRONT_URL)}/s3_key/img.jpg",
        "trailer_url": f"{str(SHOWS_PUBLIC_CLOUDFRONT_URL)}/s3_key/img.mp4",
        "director": str(data["Original_CSV_Data"]["Director(s)"]),
        "release_year": int(data["Original_CSV_Data"]["Production Year"]),
        "rating":  str(rating),
        "is_premium": True,
        "featured": True, # need to ask the value for this
        "genre": f"{data["Original_CSV_Data"]["Genre"]}",
        "is_rentable": True,
        "review_status": "pending"
    }
    try:
        response = requests.post(f"{SUPABASE_URL}/series", headers=headers, json=series_data)
        
        response.raise_for_status()
        
        result = response.json()

        return result[0] if isinstance(result, list) else result

    except Exception as e:
        logger.error(f"-- Function save_series:  Error saving ing Supabase: {e}")
        raise Exception(f"-- Function save_series:  Error saving ing Supabase: {e}")

def save_episode(data, serie_id, video_id):
    # save the episode 
    episode_data = {
        "series_id": str(serie_id),
        "video_id": str(video_id),
        "season_number": int(data["Original_CSV_Data"]["Season Number"]),
        "episode_number": int(data["Original_CSV_Data"]["Episode Number"]),
        "episode_title": data["Original_CSV_Data"]["Episode Name"]
    }
    try:
        response = requests.post(f"{SUPABASE_URL}/series_episodes", headers=headers, json=episode_data)
        
        response.raise_for_status()
        
        result = response.json()

        return result[0] if isinstance(result, list) else result

    except Exception as e:
        logger.error(f"-- Function save_episode:  Error saving ing Supabase: {e}")
        raise Exception(f"-- Function save_episode:  Error saving ing Supabase: {e}")

def update_series(data, series_id):
    rating = "PG" if str(data["Original_CSV_Data"]["Rating"]) == "" else str(data["Original_CSV_Data"]["Rating"])
    series_data = {
        "title": f"{data["Original_CSV_Data"]["Movie/Show Title"]}",
        "description": f"{data["Original_CSV_Data"]["Episode Synopsis"]}",
        "category": f"{data["Original_CSV_Data"]["Genre"]}",
        "poster_url": f"{str(SHOWS_PUBLIC_CLOUDFRONT_URL)}/s3_key/img.jpg",
        "trailer_url": f"{str(SHOWS_PUBLIC_CLOUDFRONT_URL)}/s3_key/img.mp4",
        "director": str(data["Original_CSV_Data"]["Director(s)"]),
        "release_year": int(data["Original_CSV_Data"]["Production Year"]),
        "rating":  str(rating),
        "is_premium": True,
        "featured": True, # need to ask the value for this
        "genre": f"{data["Original_CSV_Data"]["Genre"]}",
        "is_rentable": True,
        "review_status": "pending",
        "total_seasons": get_total_seasons(data, series_id),
        "total_episodes": get_total_episodes(data, series_id)
    }
    try:
        response = requests.patch(f"{SUPABASE_URL}/series?id=eq.{series_id}", headers=headers, json=series_data)
        
        response.raise_for_status()
        
        result = response.json()

        return result[0] if isinstance(result, list) else result

    except Exception as e:
        logger.error(f"-- Function update_series:  Error saving ing Supabase: {e}")
        raise Exception(f"-- Function update_series:  Error saving ing Supabase: {e}")

def update_videos(data, video_id):
    video_data = {
        "title": f"{data["Original_CSV_Data"]["Movie/Show Title"]} - Episode {data["Original_CSV_Data"]["Episode Number"]} - {data["Original_CSV_Data"]["Episode Name"]}",
        "description": f"{data["Original_CSV_Data"]["Episode Synopsis"]}",
        "duration": int(data["Original_CSV_Data"]["Episode Running Time"]),
        "category": f"{data["Original_CSV_Data"]["Genre"]}",
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
        response = requests.patch(f"{SUPABASE_URL}/videos?id=eq.{video_id}", headers=headers, json=video_data)
        
        response.raise_for_status()
        
        result = response.json()

        return result[0] if isinstance(result, list) else result

    except Exception as e:
        logger.error(f"-- Function update_videos:  Error saving ing Supabase: {e}")
        raise Exception(f"-- Function update_videos:  Error saving ing Supabase: {e}")

def update_episodes(data, serie_id, video_id):
    params = {
        "video_id": f"eq.{video_id}",
        "series_id": f"eq.{serie_id}"
    }
    episode_data = {
        "season_number": int(data["Original_CSV_Data"]["Season Number"]),
        "episode_number": int(data["Original_CSV_Data"]["Episode Number"]),
        "episode_title": data["Original_CSV_Data"]["Episode Name"]
    }
    try:
        response = requests.patch(f"{SUPABASE_URL}/series_episodes", headers=headers, params=params, json=episode_data)
        
        response.raise_for_status()
        
        result = response.json()

        return result[0] if isinstance(result, list) else result

    except Exception as e:
        logger.error(f"-- Function update_episodes:  Error saving ing Supabase: {e}")
        raise Exception(f"-- Function update_episodes:  Error saving ing Supabase: {e}")

def get_total_seasons(event, serie_id):
    url = f"{SUPABASE_URL}/series_episodes"
    
    # URL Parameters:
    # 1. Filter by series_id
    # 2. Select only the season_number column
    # 3. Order by season_number in descending order (desc)
    params = {
        "series_id": f"eq.{serie_id}",
        "select": "season_number",
        "order": "season_number.desc"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        ordered_seasons = list(dict.fromkeys([item['season_number'] for item in data]))
        
        return len(ordered_seasons)

    except Exception as e:
        logger.error(f"-- Function get_latest_season:  Error saving ing Supabase: {e}")
        raise Exception(f"-- Function get_latest_season:  Error saving ing Supabase: {e}")

def get_total_episodes(event, serie_id):
    url = f"{SUPABASE_URL}/series_episodes"
    
    # URL Parameters:
    # 1. Filter by series_id
    # 2. Select only the season_number column
    # 3. Order by season_number in descending order (desc)
    params = {
        "series_id": f"eq.{serie_id}",
        "select": "episode_number"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        episodes = list(dict.fromkeys([item['episode_number'] for item in data]))
        
        return len(episodes)

    except Exception as e:
        logger.error(f"-- Function get_latest_season:  Error saving ing Supabase: {e}")
        raise Exception(f"-- Function get_latest_season:  Error saving ing Supabase: {e}")

def lambda_handler(event, context):
    # 1. Print the event as a formatted JSON string
    # 'indent=4' makes it readable in CloudWatch
    logger.info(json.dumps(event))

    try:
        video_id = get_video(event, event["Original_CSV_Data"]["Movie/Show Title"], event["Original_CSV_Data"]["Episode Number"], event["Original_CSV_Data"]["Episode Name"])
        logger.info(f"-- video_id: {video_id}")
        series_id = get_series(event, event["Original_CSV_Data"]["Movie/Show Title"])
        logger.info(f"-- series_id: {series_id}")
        episode_id = get_series_episode(event, series_id, video_id)
        logger.info(f"-- episode_id: {episode_id} with video_id {video_id} and series_id {series_id}")

        logger.info("-- Updating information required...")

        logger.info(json.dumps(update_episodes(event, series_id, video_id)))
        logger.info(json.dumps(update_videos(event, video_id)))
        logger.info(json.dumps(update_series(event, series_id)))

        logger.info("-- Finish All Updates")
        
        return event

    except Exception as e:
        logger.error(f">> Function: lambda_handler: {str(e)}")
        raise Exception(f">> Function: lambda_handler: {str(e)}")