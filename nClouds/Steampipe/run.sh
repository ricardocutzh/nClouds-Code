#!/bin/bash

ENVIFILE=./envfiles/prime-research-app.env

docker build -t steampipe . && docker run -it --env-file $ENVIFILE  --rm --name steampipe-app steampipe 