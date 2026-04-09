#!/bin/bash

# Usage: source assume.sh arn:aws:iam::123456789012:role/MyRole
ROLE_ARN=arn:aws:iam::098072157095:role/nc_cross_acc_fullaccess_default
SESSION_NAME="CLI-Session-$(date +%s)"

if [ -z "$ROLE_ARN" ]; then
    echo "Error: Role ARN is required."
    echo "Usage: eval \$(./assume.sh <ROLE_ARN>)"
    return 1
fi

# 1. Clear existing session tokens to avoid conflicts during the call

# 2. Call AssumeRole
KMS_CREDS=$(aws sts assume-role \
    --role-arn "$ROLE_ARN" \
    --role-session-name "$SESSION_NAME" \
    --output json)

if [ $? -ne 0 ]; then
    echo "Error: AssumeRole failed."
    return 1
fi

# 3. Parse the JSON and format as export commands
# We use 'eval' on the calling side, so we output the export strings here
echo "export AWS_ACCESS_KEY_ID=$(echo $KMS_CREDS | jq -r '.Credentials.AccessKeyId')"
echo "export AWS_SECRET_ACCESS_KEY=$(echo $KMS_CREDS | jq -r '.Credentials.SecretAccessKey')"
echo "export AWS_SESSION_TOKEN=$(echo $KMS_CREDS | jq -r '.Credentials.SessionToken')"
echo "echo 'Successfully assumed role: $ROLE_ARN'"