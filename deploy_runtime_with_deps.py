#!/usr/bin/env python3
"""Deploy AgentCore Runtime with proper ARM64 dependencies included"""

import boto3
import time
import json
import sys
import argparse
import os
from deployment_utils import create_deployment_package

ROLE_ARN = 'arn:aws:iam::788835021449:role/AgentCoreRunTimeRole'
S3_BUCKET = 'agentcore-runtime-pr-deployment-demo'
REGION = 'us-west-2'

def upload_to_s3(zip_path, runtime_name):
    """Upload zip to S3 with version structure."""
    s3 = boto3.client('s3', region_name=REGION)
    # Version 1 for new deployments
    key = f"{runtime_name}/v1/code.zip"
    
    print(f"\n☁️  Uploading to S3...")
    print(f"   Bucket: {S3_BUCKET}")
    print(f"   Key: {key}")
    
    s3.upload_file(zip_path, S3_BUCKET, key)
    s3_uri = f"s3://{S3_BUCKET}/{key}"
    print(f"✅ Uploaded to: {s3_uri}")
    return S3_BUCKET, key

def create_runtime(bucket, key, runtime_name):
    """Create AgentCore Runtime."""
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    print(f"\n🚀 Creating AgentCore Runtime: {runtime_name}")
    print(f"   Role: {ROLE_ARN}")
    print(f"   S3: s3://{bucket}/{key}")
    print(f"   Runtime: PYTHON_3_11")
    print(f"   Entry Point: agent.py")
    
    try:
        response = client.create_agent_runtime(
            agentRuntimeName=runtime_name,
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
            description='Runtime with ARM64 dependencies included'
        )
        
        print(f"✅ Runtime created!")
        print(f"\n📋 API Response:")
        print("=" * 60)
        print(json.dumps(response, indent=2, default=str))
        print("=" * 60 + "\n")
        
        runtime_id = response['agentRuntimeId']
        runtime_arn = response['agentRuntimeArn']
        version = response['agentRuntimeVersion']
        
        print(f"   Runtime ID: {runtime_id}")
        print(f"   Runtime ARN: {runtime_arn}")
        print(f"   Version: {version}")
        
        return runtime_id, runtime_arn, version
        
    except Exception as e:
        print(f"❌ Failed to create runtime: {e}")
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Deploy AgentCore Runtime with ARM64 dependencies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy with default prompt
  python3 deploy_runtime_with_deps.py
  
  # Deploy with dad joke bot prompt
  python3 deploy_runtime_with_deps.py --prompt prompts/dad_joke_bot.txt
  
  # Deploy with motivational quotes bot prompt
  python3 deploy_runtime_with_deps.py --prompt prompts/motivational_quotes_bot.txt
        """
    )
    parser.add_argument(
        '--prompt',
        type=str,
        help='Path to prompt file to use for the agent (optional)'
    )
    parser.add_argument(
        '--name',
        type=str,
        help='Custom runtime name (optional, defaults to timestamped name)'
    )
    
    args = parser.parse_args()
    
    # Use custom name or generate timestamped name
    runtime_name = args.name if args.name else f'test_runtime_with_deps_{int(time.time())}'
    
    print("=" * 60)
    print("AgentCore Runtime Deployment with ARM64 Dependencies")
    print("=" * 60)
    print(f"Runtime Name: {runtime_name}")
    if args.prompt:
        print(f"📝 Using prompt file: {args.prompt}")
    print()
    
    try:
        # Step 1: Create deployment package with dependencies
        zip_path = create_deployment_package(prompt_file=args.prompt)
        
        # Step 2: Upload to S3
        bucket, key = upload_to_s3(zip_path, runtime_name)
        
        # Step 3: Create runtime
        runtime_id, runtime_arn, version = create_runtime(bucket, key, runtime_name)
        
        # Step 4: Wait for runtime to be ready
        wait_for_runtime_ready(runtime_id)
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Runtime deployment completed")
        print("=" * 60)
        print(f"Runtime ID: {runtime_id}")
        print(f"Runtime ARN: {runtime_arn}")
        print(f"Version: {version}")
        if args.prompt:
            print(f"Prompt: {args.prompt}")
        print(f"\n💡 Next steps:")
        print(f"   1. Test the runtime from the AWS console")
        print(f"   2. Check CloudWatch logs if there are issues")
        print(f"   3. Use update script to deploy code changes")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ DEPLOYMENT FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
