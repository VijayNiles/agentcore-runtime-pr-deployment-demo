#!/usr/bin/env python3
import boto3
import sys
import json

def test_endpoint(endpoint_name, prompt="Hello"):
    """Test an AgentCore endpoint with a prompt."""
    client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    
    print(f"\n🧪 Testing endpoint: {endpoint_name}")
    print(f"📝 Prompt: {prompt}\n")
    
    try:
        response = client.invoke_agent(
            agentId=endpoint_name,
            sessionId='test-session',
            inputText=prompt
        )
        
        # Parse streaming response
        result = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    result += chunk['bytes'].decode('utf-8')
        
        print(f"✅ Response: {result}\n")
        return result
        
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_endpoint.py <endpoint-name> [prompt]")
        sys.exit(1)
    
    endpoint = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else "Hello"
    
    test_endpoint(endpoint, prompt)
