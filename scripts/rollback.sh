#!/bin/bash

if [ "$#" -lt 3 ]; then
    echo "Usage: ./rollback.sh <runtime-id> <endpoint-name> <version-number>"
    echo "Example: ./rollback.sh abc123xyz demo-prod-endpoint 2"
    exit 1
fi

RUNTIME_ID=$1
ENDPOINT_NAME=$2
VERSION=$3
REGION="us-east-1"

echo "🔄 Rolling back endpoint: $ENDPOINT_NAME to version: $VERSION"

# Wait for runtime to be READY
echo "⏳ Checking runtime status..."
MAX_WAIT=300
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    STATUS=$(aws bedrock-agentcore get-agent-runtime \
        --agent-runtime-id "$RUNTIME_ID" \
        --region "$REGION" \
        --query 'status' \
        --output text 2>/dev/null)
    
    if [ "$STATUS" = "READY" ]; then
        echo "✅ Runtime is READY"
        break
    elif [ "$STATUS" = "CREATE_FAILED" ] || [ "$STATUS" = "UPDATE_FAILED" ]; then
        echo "❌ Runtime is in failed state: $STATUS"
        exit 1
    fi
    
    echo "Runtime status: $STATUS (waiting...)"
    sleep 10
    ELAPSED=$((ELAPSED + 10))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "❌ Timeout waiting for runtime to be READY"
    exit 1
fi

aws bedrock-agentcore update-agent-runtime-endpoint \
    --agent-runtime-id "$RUNTIME_ID" \
    --endpoint-name "$ENDPOINT_NAME" \
    --agent-runtime-version "$VERSION" \
    --region "$REGION"

if [ $? -eq 0 ]; then
    echo "✅ Rollback complete! Endpoint now points to version $VERSION"
else
    echo "❌ Rollback failed"
    exit 1
fi
