#!/usr/bin/env python3
import boto3
import sys
import json

def test_endpoint(runtime_arn, endpoint_name, prompt="Hello"):
    """Test an AgentCore endpoint with a prompt."""
    client = boto3.client('bedrock-agentcore', region_name='us-east-1')
    
    print(f"\n🧪 Testing endpoint: {endpoint_name}")
    print(f"📝 Prompt: {prompt}\n")
    
    try:
        payload = json.dumps({"prompt": prompt}).encode('utf-8')
        
        response = client.invoke_agent_runtime(
            agentRuntimeArn=runtime_arn,
            qualifier=endpoint_name,
            contentType='application/json',
            accept='application/json',
            payload=payload
        )
        
        # Read streaming response
        result = response['response'].read().decode('utf-8')
        result_json = json.loads(result)
        
        print(f"✅ Response: {result_json.get('result', result)}\n")
        return result_json
        
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_endpoint.py <runtime-arn> <endpoint-name> [prompt]")
        print("Example: python test_endpoint.py arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/abc123 demo-prod-endpoint 'Hello'")
        sys.exit(1)
    
    runtime_arn = sys.argv[1]
    endpoint_name = sys.argv[2]
    prompt = sys.argv[3] if len(sys.argv) > 3 else "Hello"
    
    test_endpoint(runtime_arn, endpoint_name, prompt)
