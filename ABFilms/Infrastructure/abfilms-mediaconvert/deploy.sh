#!/bin/sh

ENV=$1

S3_BUCKET=$2

 sam build --config-env $ENV

 sam deploy --config-env $ENV --s3-bucket $S3_BUCKET --parameter-overrides $(jq -r 'to_entries | map("\(.key)=\(.value)") | join(" ")' ./params/$ENV.json)