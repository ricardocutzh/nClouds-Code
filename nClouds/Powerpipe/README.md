# tag-reports


## Getting ready:

To get up and running:

1. Create an environment file, take as an example the *.env.example* file.

2 in the file docker-compose.yaml change the name of the .env file that you want to use in the env_file property

3. perform a docker-compose up

4. This will bring up a dashbaord that you can use to explore the tags setup in the account

5. To export a report in a CSV format, you can change the property command from *dashboard.sh* to *untagged.sh* this will generate a report in csv format of untagged resources