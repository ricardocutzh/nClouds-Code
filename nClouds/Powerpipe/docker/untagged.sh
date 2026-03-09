#!/bin/bash

steampipe service start
sleep 60
powerpipe benchmark run aws_tags.benchmark.untagged --var-file tags.spvars --output csv >> output/report.csv

############################### REPORT FILTERING ###############################
exclude_controls=('aws_tags.control.config_rule_untagged' 'aws_tags.control.eventbridge_rule_untagged' 'aws_tags.control.guardduty_detector_untagged' 'aws_tags.control.iam_role_untagged' 'aws_tags.control.iam_user_untagged' 'aws_tags.control.rds_db_parameter_group_untagged' 'aws_tags.control.vpc_security_group_untagged' 'aws_tags.control.ssm_parameter_untagged')
exclude_pattern=$(IFS="|"; echo "${exclude_controls[*]}")
awk -F, 'NR==1 || $9 == "alarm"' "output/report.csv" > "output/report-alarm.csv"
awk -F, -v pattern="$exclude_pattern" 'NR==1 || $4 !~ pattern' "output/report-alarm.csv" > "output/$ACCOUNT_NAME-untagged-report.csv"
rm -rf output/report-alarm.csv
rm -rf output/report.csv
############################### REPORT FILTERING ###############################