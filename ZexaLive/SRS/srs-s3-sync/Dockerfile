FROM alpine:latest

# Install AWS CLI and dependencies
RUN apk add --no-cache aws-cli

# Create source directory
WORKDIR /src

# Copy the sync script
COPY sync.sh /sync.sh
RUN chmod +x /sync.sh

# Run the script
CMD ["/sync.sh"]