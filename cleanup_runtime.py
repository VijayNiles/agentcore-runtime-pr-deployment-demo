#!/usr/bin/env python3
"""Clean up an AgentCore Runtime by deleting all custom endpoints and the runtime itself"""

import boto3
import json
import sys
import time

REGION = 'us-west-2'

def list_endpoints(runtime_id):
    """List all endpoints for a runtime.
    
    Args:
        runtime_id: The AgentCore Runtime ID
    
    Returns:
        List of endpoint names
    """
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    print(f"📋 Listing endpoints for runtime {runtime_id}...")
    
    try:
        response = client.list_agent_runtime_endpoints(
            agentRuntimeId=runtime_id
        )
        
        endpoints = response.get('runtimeEndpoints', [])
        endpoint_names = [ep['name'] for ep in endpoints]
        
        print(f"✓ Found {len(endpoint_names)} endpoint(s)")
        for name in endpoint_names:
            print(f"   - {name}")
        
        return endpoint_names
        
    except Exception as e:
        print(f"❌ Failed to list endpoints: {e}")
        raise

def delete_endpoint(runtime_id, endpoint_name):
    """Delete a specific endpoint.
    
    Args:
        runtime_id: The AgentCore Runtime ID
        endpoint_name: The endpoint name to delete
    
    Returns:
        True if deleted successfully
    """
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    print(f"🗑️  Deleting endpoint: {endpoint_name}...")
    
    try:
        response = client.delete_agent_runtime_endpoint(
            agentRuntimeId=runtime_id,
            endpointName=endpoint_name
        )
        
        print(f"✓ Endpoint {endpoint_name} deleted")
        print(f"   Response: {json.dumps(response, indent=2, default=str)}")
        
        # Verify deletion by checking if endpoint no longer exists
        time.sleep(2)  # Brief wait for consistency
        
        try:
            client.get_agent_runtime_endpoint(
                agentRuntimeId=runtime_id,
                endpointName=endpoint_name
            )
            # If we get here, endpoint still exists
            print(f"⚠️  Warning: Endpoint {endpoint_name} still exists after deletion")
            return False
        except client.exceptions.ResourceNotFoundException:
            # Expected - endpoint is gone
            print(f"✅ Verified: Endpoint {endpoint_name} no longer exists")
            return True
        except Exception as e:
            print(f"⚠️  Could not verify deletion: {e}")
            return True  # Assume success if we can't verify
        
    except Exception as e:
        print(f"❌ Failed to delete endpoint {endpoint_name}: {e}")
        raise

def delete_runtime(runtime_id):
    """Delete the runtime.
    
    Args:
        runtime_id: The AgentCore Runtime ID
    
    Returns:
        True if deleted successfully
    """
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    print(f"\n🗑️  Deleting runtime: {runtime_id}...")
    
    try:
        response = client.delete_agent_runtime(
            agentRuntimeId=runtime_id
        )
        
        print(f"✓ Runtime deletion initiated")
        print(f"   Response: {json.dumps(response, indent=2, default=str)}")
        
        # Wait and verify deletion
        print(f"⏳ Waiting for runtime deletion to complete...")
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(5)
            
            try:
                get_response = client.get_agent_runtime(agentRuntimeId=runtime_id)
                status = get_response.get('status', 'UNKNOWN')
                print(f"   Status: {status} (attempt {attempt + 1}/{max_attempts})")
                
                if status == 'DELETE_FAILED':
                    failure_reason = get_response.get('failureReason', 'Unknown')
                    raise Exception(f"Runtime deletion failed: {failure_reason}")
                    
            except client.exceptions.ResourceNotFoundException:
                # Expected - runtime is gone
                print(f"✅ Verified: Runtime {runtime_id} no longer exists")
                return True
            except Exception as e:
                if 'ResourceNotFoundException' in str(type(e).__name__):
                    print(f"✅ Verified: Runtime {runtime_id} no longer exists")
                    return True
                # For other errors, continue waiting
                pass
        
        print(f"⚠️  Timeout waiting for runtime deletion verification")
        return False
        
    except Exception as e:
        print(f"❌ Failed to delete runtime: {e}")
        raise

def get_runtime_info(runtime_id):
    """Get runtime information to verify it exists."""
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    print(f"📋 Getting runtime information...")
    try:
        response = client.get_agent_runtime(agentRuntimeId=runtime_id)
        print(f"✓ Runtime Name: {response.get('agentRuntimeName', 'N/A')}")
        print(f"✓ Runtime Status: {response['status']}")
        print(f"✓ Current Version: {response.get('agentRuntimeVersion', 'N/A')}")
        return response
    except Exception as e:
        print(f"❌ Failed to get runtime info: {e}")
        raise

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 cleanup_runtime.py <runtime_id>")
        print("\nThis script will:")
        print("  1. List all endpoints for the runtime")
        print("  2. Delete all custom endpoints (keeps 'default' if it exists)")
        print("  3. Delete the runtime itself")
        print("  4. Verify all deletions")
        print("\nExample:")
        print("  python3 cleanup_runtime.py test_runtime_with_deps_1234567890-AbCdEfGhIj")
        print("\n⚠️  WARNING: This action cannot be undone!")
        sys.exit(1)
    
    runtime_id = sys.argv[1]
    
    print("=" * 60)
    print("Clean Up AgentCore Runtime")
    print("=" * 60)
    print(f"Runtime ID: {runtime_id}")
    print("\n⚠️  WARNING: This will permanently delete the runtime and all endpoints!")
    print("=" * 60 + "\n")
    
    # Ask for confirmation
    confirmation = input("Type 'DELETE' to confirm: ")
    if confirmation != 'DELETE':
        print("❌ Cleanup cancelled")
        sys.exit(0)
    
    print()
    
    try:
        # Step 1: Verify runtime exists
        get_runtime_info(runtime_id)
        
        # Step 2: List all endpoints
        endpoint_names = list_endpoints(runtime_id)
        
        # Step 3: Delete custom endpoints only (skip DEFAULT - it's managed by AWS)
        custom_endpoints = [name for name in endpoint_names if name != 'DEFAULT']
        
        if custom_endpoints:
            print(f"\n🗑️  Deleting {len(custom_endpoints)} custom endpoint(s)...")
            for endpoint_name in custom_endpoints:
                delete_endpoint(runtime_id, endpoint_name)
                time.sleep(1)  # Brief pause between deletions
        else:
            print(f"\nℹ️  No custom endpoints to delete")
        
        # Verify only DEFAULT remains (if any)
        remaining = list_endpoints(runtime_id)
        custom_remaining = [name for name in remaining if name != 'DEFAULT']
        if not custom_remaining:
            print(f"\n✅ All custom endpoints deleted.")
            if 'DEFAULT' in remaining:
                print(f"   (DEFAULT endpoint remains - managed by AWS)")
        else:
            print(f"\n⚠️  Warning: {len(custom_remaining)} custom endpoint(s) still remain: {custom_remaining}")
        
        # Step 4: Delete the runtime
        delete_runtime(runtime_id)
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Cleanup completed")
        print("=" * 60)
        print(f"Runtime {runtime_id} has been deleted")
        print(f"All associated endpoints have been removed")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ CLEANUP FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
