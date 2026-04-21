FROM nginx:alpine

# Copy the HTML to a template location
COPY index.html /usr/share/nginx/html/index.template.html

# Set default env values (can be overridden by compose)
ENV PLAYBACK_MODE=encrypted
ENV MANIFEST_URL=https://d27y62lnm1dcpo.cloudfront.net/Movies/Tears_of_Steel_0004-9498/output/dash-iso/index.mpd
ENV TOKEN_URL=https://aau8hlwb58.execute-api.us-east-1.amazonaws.com/prod/token
ENV LICENSE_URL=https://lic.drmtoday.com/license-proxy-widevine/cenc/?specConform=true
ENV ASSET_ID=0004-9498

# Entrypoint script to replace env vars in the HTML file
CMD ["/bin/sh", "-c", "envsubst '${PLAYBACK_MODE} ${MANIFEST_URL} ${TOKEN_URL} ${LICENSE_URL} ${ASSET_ID}' < /usr/share/nginx/html/index.template.html > /usr/share/nginx/html/index.html && nginx -g 'daemon off;'"]