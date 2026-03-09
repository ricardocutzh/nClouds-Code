#!/bin/bash
steampipe service start
sleep 60
powerpipe benchmark run aws_tags.benchmark.mandatory --var-file tags.spvars  --output csv >> output/report.csv