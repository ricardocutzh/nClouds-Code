#!/bin/sh

ENV=$1

S3_BUCKET=deleteme-ricardo-codepipeline

 sam build

 sam deploy --config-env $ENV --s3-bucket $S3_BUCKET --parameter-overrides $(jq -r 'to_entries | map("\(.key)=\(.value)") | join(" ")' ./params/$ENV.json)