#!/usr/bin/env python3
"""Update existing AgentCore Runtime with proper ARM64 dependencies included"""

import boto3
import time
import json
import sys
import argparse
from deployment_utils import create_deployment_package

ROLE_ARN = 'arn:aws:iam::788835021449:role/AgentCoreRunTimeRole'
S3_BUCKET = 'agentcore-runtime-pr-deployment-demo'
REGION = 'us-west-2'

def find_runtime_by_name(runtime_name):
    """Find runtime ID by name."""
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    print(f"🔍 Looking up runtime by name: {runtime_name}...")
    
    try:
        # List all runtimes and find matching name
        paginator = client.get_paginator('list_agent_runtimes')
        for page in paginator.paginate():
            for runtime in page.get('agentRuntimeSummaries', []):
                if runtime['agentRuntimeName'] == runtime_name:
                    runtime_id = runtime['agentRuntimeId']
                    print(f"✅ Found runtime ID: {runtime_id}")
                    return runtime_id
        
        raise Exception(f"No runtime found with name: {runtime_name}")
    except Exception as e:
        print(f"❌ Failed to find runtime: {e}")
        raise

def upload_to_s3(zip_path, runtime_name, new_version):
    """Upload zip to S3 with version structure."""
    s3 = boto3.client('s3', region_name=REGION)
    key = f"{runtime_name}/v{new_version}/code.zip"
    
    print(f"\n☁️  Uploading to S3...")
    print(f"   Bucket: {S3_BUCKET}")
    print(f"   Key: {key}")
    
    s3.upload_file(zip_path, S3_BUCKET, key)
    s3_uri = f"s3://{S3_BUCKET}/{key}"
    print(f"✅ Uploaded to: {s3_uri}")
    return S3_BUCKET, key

def update_runtime(runtime_id, bucket, key):
    """Update AgentCore Runtime with new version."""
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    print(f"\n🔄 Updating AgentCore Runtime: {runtime_id}")
    print(f"   Role: {ROLE_ARN}")
    print(f"   S3: s3://{bucket}/{key}")
    print(f"   Runtime: PYTHON_3_11")
    print(f"   Entry Point: agent.py")
    
    try:
        response = client.update_agent_runtime(
            agentRuntimeId=runtime_id,
            agentRuntimeArtifact={
                'codeConfiguration': {
                    'code': {
                        's3': {
                            'bucket': bucket,
                            'prefix': key
                        }
                    },
                    'runtime': 'PYTHON_3_11',
                    'entryPoint': ['agent.py']
                }
            },
            roleArn=ROLE_ARN,
            networkConfiguration={
                'networkMode': 'PUBLIC'
            },
            protocolConfiguration={
                'serverProtocol': 'HTTP'
            },
            description=f'Updated version - {time.strftime("%Y-%m-%d %H:%M:%S")}'
        )
        
        print(f"✅ Runtime update initiated!")
        print(f"\n📋 API Response:")
        print("=" * 60)
        print(json.dumps(response, indent=2, default=str))
        print("=" * 60 + "\n")
        
        runtime_arn = response['agentRuntimeArn']
        version = response['agentRuntimeVersion']
        
        print(f"   Runtime ARN: {runtime_arn}")
        print(f"   New Version: {version}")
        
        return runtime_arn, version
        
    except Exception as e:
        print(f"❌ Failed to update runtime: {e}")
        print(f"   Error type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response}")
        raise

def wait_for_runtime_ready(runtime_id, timeout=300):
    """Wait for runtime to be READY."""
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    start_time = time.time()
    
    print(f"\n⏳ Waiting for runtime to be READY (timeout: {timeout}s)...")
    
    while True:
        response = client.get_agent_runtime(agentRuntimeId=runtime_id)
        status = response['status']
        
        if status == 'READY':
            print(f"✅ Runtime is READY!")
            return True
        elif status in ['CREATE_FAILED', 'UPDATE_FAILED']:
            failure_reason = response.get('failureReason', 'Unknown')
            raise Exception(f"Runtime failed: {status} - {failure_reason}")
        
        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise Exception(f"Timeout waiting for runtime. Current status: {status}")
        
        print(f"   Status: {status} (elapsed: {int(elapsed)}s)")
        time.sleep(10)

def get_runtime_info(runtime_id):
    """Get current runtime information."""
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    print(f"📋 Getting current runtime information...")
    try:
        response = client.get_agent_runtime(agentRuntimeId=runtime_id)
        print(f"✓ Current Status: {response['status']}")
        print(f"✓ Current Version: {response.get('agentRuntimeVersion', 'N/A')}")
        
        runtime_name = response['agentRuntimeName']
        current_version = response['agentRuntimeVersion']
        return runtime_name, current_version
    except Exception as e:
        print(f"❌ Failed to get runtime info: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Update AgentCore Runtime with ARM64 dependencies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update with existing prompt
  python3 update_runtime_with_deps.py test_runtime_with_deps_1234567890-AbCdEfGhIj
  
  # Update with dad joke bot prompt
  python3 update_runtime_with_deps.py test_runtime_with_deps_1234567890-AbCdEfGhIj --prompt prompts/dad_joke_bot.txt
  
  # Update with motivational quotes bot prompt
  python3 update_runtime_with_deps.py test_runtime_with_deps_1234567890-AbCdEfGhIj --prompt prompts/motivational_quotes_bot.txt
        """
    )
    parser.add_argument(
        'runtime_identifier',
        type=str,
        help='The AgentCore Runtime ID or Name to update'
    )
    parser.add_argument(
        '--prompt',
        type=str,
        help='Path to prompt file to use for the agent (optional)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AgentCore Runtime Update with ARM64 Dependencies")
    print("=" * 60)
    
    try:
        # Step 0: Resolve runtime ID from name if needed
        runtime_id = args.runtime_identifier
        
        # Check if it looks like a runtime ID (contains hyphen with random suffix)
        # If not, assume it's a name and look it up
        if '-' not in runtime_id or not any(char.isdigit() for char in runtime_id.split('-')[-1]):
            # Looks like a name, not an ID
            runtime_id = find_runtime_by_name(args.runtime_identifier)
        
        print(f"Runtime ID: {runtime_id}")
        if args.prompt:
            print(f"📝 Using prompt file: {args.prompt}")
        print()
        
        # Step 1: Get current runtime info
        runtime_name, current_version = get_runtime_info(runtime_id)
        new_version = int(current_version) + 1
        
        print(f"Runtime Name: {runtime_name}")
        print(f"Current Version: {current_version}")
        print(f"New Version: {new_version}\n")
        
        # Step 2: Create deployment package with dependencies
        zip_path = create_deployment_package(prompt_file=args.prompt)
        
        # Step 3: Upload to S3
        bucket, key = upload_to_s3(zip_path, runtime_name, new_version)
        
        # Step 4: Update runtime
        runtime_arn, version = update_runtime(runtime_id, bucket, key)
        
        # Step 5: Wait for runtime to be ready
        wait_for_runtime_ready(runtime_id)
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Runtime update completed")
        print("=" * 60)
        print(f"Runtime ID: {runtime_id}")
        print(f"Runtime ARN: {runtime_arn}")
        print(f"New Version: {version}")
        if args.prompt:
            print(f"Prompt: {args.prompt}")
        print(f"\n💡 Next steps:")
        print(f"   1. Test the updated runtime from the AWS console")
        print(f"   2. Check CloudWatch logs if there are issues")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ UPDATE FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
