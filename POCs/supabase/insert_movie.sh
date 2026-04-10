
export TU_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJzZXJ2aWNlX3JvbGUiLAogICAgImlzcyI6ICJzdXBhYmFzZS1kZW1vIiwKICAgICJpYXQiOiAxNjQxNzY5MjAwLAogICAgImV4cCI6IDE3OTk1MzU2MDAKfQ.DaYlNEoUrrEn2Ig7tqibS-PHK5vgusbcbo7X36XVt4Q
SKU=$(cat movie_input.json | jq -r '.Original_CSV_Data | ."Movie/Show Filmhub SKU"')
MOVE_NAME=$(cat movie_input.json | jq -r '.Original_CSV_Data | ."Movie/Show Title"')
GENRE=$(cat movie_input.json | jq -r '.Original_CSV_Data | ."Genre"')
MASTER_FILE_URL=$(cat movie_input.json | jq -r '.UserMetadata | ."MasterFileURL"')
curl -X POST "http://localhost:8000/rest/v1/processed_movies_raw_data" \
     -H "Content-Type: application/json" \
     -H "apikey: $TU_ANON_KEY" \
     -H "Authorization: Bearer $TU_ANON_KEY" \
     -H "Prefer: return=representation" \
     -d "{ \"movie_sku\": \"$SKU\", \"name\": \"$MOVE_NAME\", \"genre\": \"$GENRE\", \"master_file_url\": \"$MASTER_FILE_URL\", \"raw_data\": $(cat movie_input.json) }"