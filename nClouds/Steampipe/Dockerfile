#FROM --platform=linux/amd64 homebrew/brew
FROM homebrew/brew
RUN brew install turbot/tap/powerpipe 
RUN brew install turbot/tap/steampipe
RUN steampipe plugin install aws

ENTRYPOINT ["bash"]