#!/usr/bin/env python3
"""Update an existing endpoint to point to a different runtime version"""

import boto3
import json
import sys

REGION = 'us-west-2'

def update_endpoint(runtime_id, endpoint_name, new_version):
    """Update an endpoint to point to a new runtime version.
    
    Args:
        runtime_id: The AgentCore Runtime ID
        endpoint_name: The endpoint name to update
        new_version: The new runtime version to point to
    
    Returns:
        Tuple of (endpoint_name, endpoint_arn)
    """
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    print(f"\n🔄 Updating endpoint to new version...")
    print(f"   Runtime ID: {runtime_id}")
    print(f"   Endpoint Name: {endpoint_name}")
    print(f"   New Version: {new_version}")
    
    try:
        response = client.update_agent_runtime_endpoint(
            agentRuntimeId=runtime_id,
            endpointName=endpoint_name,
            agentRuntimeVersion=new_version
        )
        
        print(f"✅ Endpoint updated successfully!")
        print(f"\n📋 API Response:")
        print("=" * 60)
        print(json.dumps(response, indent=2, default=str))
        print("=" * 60 + "\n")
        
        endpoint_arn = response.get('agentRuntimeEndpointArn', 'N/A')
        
        print(f"   Endpoint Name: {endpoint_name}")
        print(f"   Endpoint ARN: {endpoint_arn}")
        print(f"   Now points to version: {new_version}")
        
        return endpoint_name, endpoint_arn
        
    except Exception as e:
        print(f"❌ Failed to update endpoint: {e}")
        print(f"   Error type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response}")
        raise

def get_endpoint_info(runtime_id, endpoint_name):
    """Get current endpoint information."""
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    print(f"📋 Getting current endpoint information...")
    try:
        response = client.get_agent_runtime_endpoint(
            agentRuntimeId=runtime_id,
            endpointName=endpoint_name
        )
        current_version = response.get('agentRuntimeVersion', 'N/A')
        status = response.get('status', 'N/A')
        print(f"✓ Endpoint Status: {status}")
        print(f"✓ Current Version: {current_version}")
        return response
    except Exception as e:
        print(f"❌ Failed to get endpoint info: {e}")
        raise

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 update_endpoint.py <runtime_id> <endpoint_name> <new_version>")
        print("\nArguments:")
        print("  runtime_id      - The AgentCore Runtime ID")
        print("  endpoint_name   - The name of the endpoint to update")
        print("  new_version     - The new runtime version to point to (e.g., '2', '3', '4')")
        print("\nExample:")
        print("  python3 update_endpoint.py test_runtime_with_deps_1234567890-AbCdEfGhIj prod_deployment 2")
        sys.exit(1)
    
    runtime_id = sys.argv[1]
    endpoint_name = sys.argv[2]
    new_version = sys.argv[3]
    
    print("=" * 60)
    print("Update AgentCore Runtime Endpoint")
    print("=" * 60)
    
    try:
        # Step 1: Get current endpoint info
        get_endpoint_info(runtime_id, endpoint_name)
        
        # Step 2: Update endpoint to new version
        endpoint_name, endpoint_arn = update_endpoint(runtime_id, endpoint_name, new_version)
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Endpoint updated")
        print("=" * 60)
        print(f"Endpoint Name: {endpoint_name}")
        print(f"Endpoint ARN: {endpoint_arn}")
        print(f"Runtime ID: {runtime_id}")
        print(f"New Version: {new_version}")
        print(f"\n💡 The endpoint now points to version {new_version}")
        print(f"   You can test it from the AWS console")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
