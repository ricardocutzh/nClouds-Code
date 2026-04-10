export TU_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJzZXJ2aWNlX3JvbGUiLAogICAgImlzcyI6ICJzdXBhYmFzZS1kZW1vIiwKICAgICJpYXQiOiAxNjQxNzY5MjAwLAogICAgImV4cCI6IDE3OTk1MzU2MDAKfQ.DaYlNEoUrrEn2Ig7tqibS-PHK5vgusbcbo7X36XVt4Q
INPUT_FILE=show_input.json
SHOW_SKU=$(cat $INPUT_FILE | jq -r '.Original_CSV_Data | ."Movie/Show Filmhub SKU"')
EPISODE_SKU=$(cat $INPUT_FILE | jq -r '.Original_CSV_Data | ."Episode SKU"')
SEASON_NUMBER=$(cat $INPUT_FILE | jq -r '.Original_CSV_Data | ."Season Number"')
EPISODE_NUMBER=$(cat $INPUT_FILE | jq -r '.Original_CSV_Data | ."Episode Number"')
EPISODE_NAME=$(cat $INPUT_FILE | jq -r '.Original_CSV_Data | ."Episode Name"')
MASTER_FILE_URL=$(cat $INPUT_FILE | jq -r '.UserMetadata | ."MasterFileURL"')
SHOW_NAME=$(cat $INPUT_FILE | jq -r '.Original_CSV_Data | ."Movie/Show Title"')
GENRE=$(cat $INPUT_FILE | jq -r '.Original_CSV_Data | ."Genre"')

curl -X POST "http://localhost:8000/rest/v1/processed_shows_raw_data" \
     -H "Content-Type: application/json" \
     -H "apikey: $TU_ANON_KEY" \
     -H "Authorization: Bearer $TU_ANON_KEY" \
     -H "Prefer: return=representation" \
     -d "{ \"show_sku\": \"$SHOW_SKU\", \"episode_sku\": \"$EPISODE_SKU\", \"season_number\": \"$SEASON_NUMBER\", \"episode_number\": \"$EPISODE_NUMBER\", \"episode_name\": \"$EPISODE_NAME\", \"master_file_url\": \"$MASTER_FILE_URL\", \"show_name\": \"$SHOW_NAME\", \"genre\": \"$GENRE\", \"raw_data\": $(cat $INPUT_FILE) }"