#!/bin/bash

# Usage: ./deploy.sh dev
ENV=$1
IDENTIFIER=$2

# 1. Validation: Ensure an environment was passed
if [ -z "$ENV" ]; then
    echo "Usage: ./deploy.sh [dev|stg|prod] [identifier]"
    exit 1
fi

# 2. Configuration Variables
STACK_NAME="abfilms-filmhub-ingest-bucket"
TEMPLATE_FILE="abfilms-filmhub-ingest-bucket.yaml"
PARAM_FILE="./parameters/${IDENTIFIER}-${ENV}.json"
TAG_FILE="./tags/${IDENTIFIER}-${ENV}.json"
REGION="us-east-1"

echo "-------------------------------------------------------"
echo "🚀 Deploying Stack: $STACK_NAME to $REGION"
echo "Environment: $ENV"
echo "Identifier: $IDENTIFIER"
echo "-------------------------------------------------------"

# 3. Execution: Run the CloudFormation Deploy
# We use 'aws cloudformation deploy' because it handles the Waiter automatically
aws cloudformation deploy \
    --stack-name "$STACK_NAME" \
    --template-file "$TEMPLATE_FILE" \
    --parameter-overrides $(cat $PARAM_FILE | jq -r '.[] | "\(.ParameterKey)=\(.ParameterValue)"') \
    --tags $(cat "$TAG_FILE" | jq -r '.[] | "\(.Key)=\(.Value)"') \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
    --region "$REGION"

# 4. Tracking: Post-deployment status check
if [ $? -eq 0 ]; then
    echo "-------------------------------------------------------"
    echo "✅ Deployment Successful!"
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].Outputs' \
        --output table
else
    echo "-------------------------------------------------------"
    echo "❌ Deployment Failed. Checking events..."
    aws cloudformation describe-stack-events \
        --stack-name "$STACK_NAME" \
        --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`].[LogicalResourceId, ResourceStatusReason]' \
        --output table
    exit 1
fi