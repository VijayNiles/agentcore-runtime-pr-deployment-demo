#!/bin/bash

if [ "$#" -lt 2 ]; then
    echo "Usage: ./rollback.sh <endpoint-name> <version-number>"
    echo "Example: ./rollback.sh demo-prod-endpoint 2"
    exit 1
fi

ENDPOINT_NAME=$1
VERSION=$2
REGION="us-east-1"

echo "🔄 Rolling back endpoint: $ENDPOINT_NAME to version: $VERSION"

aws bedrock-agent update-agent-alias \
    --agent-id "$ENDPOINT_NAME" \
    --agent-alias-id TSTALIASID \
    --agent-alias-name "prod" \
    --routing-configuration "agentVersion=$VERSION" \
    --region "$REGION"

if [ $? -eq 0 ]; then
    echo "✅ Rollback complete! Endpoint now points to version $VERSION"
else
    echo "❌ Rollback failed"
    exit 1
fi
