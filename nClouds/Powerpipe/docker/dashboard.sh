#!/bin/bash
#export PP_VAR_mandatory_tags='["Tag1"]'
steampipe service start
powerpipe server --var-file tags.spvars --listen network