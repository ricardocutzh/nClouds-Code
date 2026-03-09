#FROM --platform=linux/amd64 homebrew/brew
FROM homebrew/brew
RUN brew install turbot/tap/powerpipe 
RUN brew install turbot/tap/steampipe
RUN steampipe plugin install aws

RUN mkdir dashboards

COPY powerpipe/mod.pp dashboards/mod.pp
COPY powerpipe/tags.spvars dashboards/tags.spvars

WORKDIR dashboards/

RUN mkdir output/
RUN powerpipe mod init
RUN powerpipe mod install
#RUN powerpipe mod install github.com/turbot/steampipe-mod-aws-tags

COPY ./docker/untagged.sh untagged.sh
COPY ./docker/dashboard.sh dashboard.sh
COPY ./docker/mandatory.sh mandatory.sh

RUN sudo chmod +x untagged.sh
RUN sudo chmod +x dashboard.sh
RUN sudo chmod +x mandatory.sh 

ENTRYPOINT ["bash"]