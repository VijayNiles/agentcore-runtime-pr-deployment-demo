#!/usr/bin/env python3
"""Create an endpoint (alias) for an existing AgentCore Runtime"""

import boto3
import time
import json
import sys

REGION = 'us-west-2'

def create_endpoint(runtime_id, version, endpoint_name=None):
    """Create an endpoint for the specified runtime and version.
    
    Args:
        runtime_id: The AgentCore Runtime ID
        version: The runtime version to point the endpoint to
        endpoint_name: Optional custom endpoint name. If not provided, generates one.
    
    Returns:
        Tuple of (endpoint_name, endpoint_arn)
    """
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    # Generate endpoint name if not provided
    if not endpoint_name:
        endpoint_name = f"endpoint_{runtime_id}_{int(time.time())}"
    
    print(f"\n🔗 Creating endpoint for runtime...")
    print(f"   Runtime ID: {runtime_id}")
    print(f"   Version: {version}")
    print(f"   Endpoint Name: {endpoint_name}")
    
    try:
        response = client.create_agent_runtime_endpoint(
            agentRuntimeId=runtime_id,
            endpointName=endpoint_name,
            agentRuntimeVersion=version,
            description=f'Endpoint for runtime {runtime_id} version {version}'
        )
        
        print(f"✅ Endpoint created successfully!")
        print(f"\n📋 API Response:")
        print("=" * 60)
        print(json.dumps(response, indent=2, default=str))
        print("=" * 60 + "\n")
        
        endpoint_arn = response.get('agentRuntimeEndpointArn', 'N/A')
        
        print(f"   Endpoint Name: {endpoint_name}")
        print(f"   Endpoint ARN: {endpoint_arn}")
        
        return endpoint_name, endpoint_arn
        
    except Exception as e:
        print(f"❌ Failed to create endpoint: {e}")
        print(f"   Error type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response}")
        raise

def get_runtime_info(runtime_id):
    """Get runtime information to verify it exists and show current version."""
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    print(f"📋 Getting runtime information...")
    try:
        response = client.get_agent_runtime(agentRuntimeId=runtime_id)
        print(f"✓ Runtime Status: {response['status']}")
        print(f"✓ Current Version: {response.get('agentRuntimeVersion', 'N/A')}")
        print(f"✓ Runtime Name: {response.get('agentRuntimeName', 'N/A')}")
        return response
    except Exception as e:
        print(f"❌ Failed to get runtime info: {e}")
        raise

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 create_endpoint.py <runtime_id> <version> [endpoint_name]")
        print("\nArguments:")
        print("  runtime_id      - The AgentCore Runtime ID")
        print("  version         - The runtime version (e.g., '1', '2', '3')")
        print("  endpoint_name   - (Optional) Custom endpoint name")
        print("\nExample:")
        print("  python3 create_endpoint.py test_runtime_with_deps_1234567890-AbCdEfGhIj 2")
        print("  python3 create_endpoint.py test_runtime_with_deps_1234567890-AbCdEfGhIj 2 my-custom-endpoint")
        sys.exit(1)
    
    runtime_id = sys.argv[1]
    version = sys.argv[2]
    endpoint_name = sys.argv[3] if len(sys.argv) > 3 else None
    
    print("=" * 60)
    print("Create AgentCore Runtime Endpoint")
    print("=" * 60)
    
    try:
        # Step 1: Verify runtime exists
        get_runtime_info(runtime_id)
        
        # Step 2: Create endpoint
        endpoint_name, endpoint_arn = create_endpoint(runtime_id, version, endpoint_name)
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Endpoint created")
        print("=" * 60)
        print(f"Endpoint Name: {endpoint_name}")
        print(f"Endpoint ARN: {endpoint_arn}")
        print(f"Runtime ID: {runtime_id}")
        print(f"Version: {version}")
        print(f"\n💡 You can now invoke this endpoint from the AWS console or via API")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
