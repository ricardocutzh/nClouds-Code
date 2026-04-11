
export TU_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyAgCiAgICAicm9sZSI6ICJzZXJ2aWNlX3JvbGUiLAogICAgImlzcyI6ICJzdXBhYmFzZS1kZW1vIiwKICAgICJpYXQiOiAxNjQxNzY5MjAwLAogICAgImV4cCI6IDE3OTk1MzU2MDAKfQ.DaYlNEoUrrEn2Ig7tqibS-PHK5vgusbcbo7X36XVt4Q

curl -X GET "http://localhost:8000/rest/v1/processed_shows_raw_data?select=show_sku,episode_sku,show_name,genre,season_number,episode_number,episode_name,master_file_url" \
     -H "apikey: $TU_ANON_KEY" \
     -H "Authorization: Bearer $TU_ANON_KEY"