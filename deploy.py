#!/usr/bin/env python3
import boto3
from botocore.exceptions import ClientError
import zipfile
import sys
import time
import os
import shutil
import subprocess

ROLE_ARN = 'arn:aws:iam::788835021449:role/AgentCoreRunTimeRole'
S3_BUCKET = 'agentcore-runtime-pr-deployment-demo'
REGION = 'us-east-1'

def create_deployment_package():
    """Create zip file with agent code and dependencies."""
    temp_dir = "/tmp/agent_package"
    
    # Clean up old package
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    print("📦 Installing dependencies...")
    try:
        # Install dependencies (pure Python packages)
        subprocess.run([
            "pip", "install",
            "-r", "agent/requirements.txt",
            "-t", temp_dir
        ], check=True, capture_output=True, text=True)
        print("✓ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e.stderr}")
        raise
    
    # Copy agent code
    print("✓ Copying agent code...")
    shutil.copy("agent/agent.py", temp_dir)
    
    # Create zip from entire directory
    print("✓ Creating deployment package...")
    zip_path = "/tmp/agent_deployment.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    print("📦 Deployment package created")
    return zip_path

def upload_to_s3(zip_path, runtime_name):
    """Upload zip to S3."""
    s3 = boto3.client('s3', region_name=REGION)
    key = f"{runtime_name}/{int(time.time())}/agent.zip"
    
    s3.upload_file(zip_path, S3_BUCKET, key)
    print(f"☁️  Uploaded to: s3://{S3_BUCKET}/{key}")
    return S3_BUCKET, key

def verify_iam_role():
    """Verify IAM role exists and is accessible."""
    iam = boto3.client('iam')
    try:
        role_name = ROLE_ARN.split('/')[-1]
        iam.get_role(RoleName=role_name)
        print(f"✓ IAM role verified: {role_name}")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"❌ IAM role verification failed: {error_code} - {e.response['Error']['Message']}")
        print(f"   Make sure role exists: {ROLE_ARN}")
        return False

def verify_s3_bucket():
    """Verify S3 bucket exists and is accessible."""
    s3 = boto3.client('s3', region_name=REGION)
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
        print(f"✓ S3 bucket verified: {S3_BUCKET}")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"❌ S3 bucket verification failed: {error_code} - {e.response['Error']['Message']}")
        print(f"   Make sure bucket exists: {S3_BUCKET}")
        return False

def wait_for_runtime_ready(client, runtime_id, timeout=300):
    """Wait for runtime to be READY."""
    start_time = time.time()
    
    while True:
        response = client.get_agent_runtime(agentRuntimeId=runtime_id)
        status = response['agentRuntime']['status']
        
        if status == 'READY':
            print(f"✓ Runtime is READY")
            return True
        elif status in ['CREATE_FAILED', 'UPDATE_FAILED']:
            failure_reason = response['agentRuntime'].get('failureReason', 'Unknown')
            raise Exception(f"Runtime failed: {status} - {failure_reason}")
        
        if time.time() - start_time > timeout:
            raise Exception(f"Timeout waiting for runtime to be READY. Current status: {status}")
        
        print(f"⏳ Runtime status: {status}. Waiting...")
        time.sleep(10)  # Poll every 10 seconds

def deploy(runtime_name, endpoint_name, is_prod=False, force_create=False, force_update=False):
    """Deploy agent using AgentCore Control APIs."""
    
    print(f"🚀 Deploying to runtime: {runtime_name}")
    print(f"📍 Endpoint: {endpoint_name}")
    
    # Verify IAM role and S3 bucket
    if not verify_iam_role():
        return False
    if not verify_s3_bucket():
        return False
    
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    # Create deployment package and upload
    zip_path = create_deployment_package()
    bucket, key = upload_to_s3(zip_path, runtime_name)
    
    try:
        # Determine if we should create or update
        runtime_id = None
        
        if force_update:
            # Explicit update - get runtime ID
            response = client.list_agent_runtimes()
            for runtime in response.get('agentRuntimes', []):
                if runtime['agentRuntimeName'] == runtime_name:
                    runtime_id = runtime['agentRuntimeId']
                    print(f"✓ Found existing runtime: {runtime_id}")
                    break
            if not runtime_id:
                raise Exception(f"Runtime {runtime_name} not found for update")
        elif not force_create:
            # Auto-detect mode (for backwards compatibility)
            try:
                response = client.list_agent_runtimes()
                for runtime in response.get('agentRuntimes', []):
                    if runtime['agentRuntimeName'] == runtime_name:
                        runtime_id = runtime['agentRuntimeId']
                        print(f"✓ Found existing runtime: {runtime_id}")
                        break
            except ClientError as e:
                error_code = e.response['Error']['Code']
                print(f"⚠️  Could not list runtimes: {error_code}")
        
        # Create or update runtime and capture version
        latest_version = None
        
        if not runtime_id and not force_update:
            # Create new runtime
            print(f"✓ Creating new runtime: {runtime_name}")
            response = client.create_agent_runtime(
                agentRuntimeName=runtime_name,
                agentRuntimeArtifact={
                    'codeConfiguration': {
                        'code': {
                            's3': {
                                'bucket': bucket,
                                'key': key
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
                description='PR-based deployment demo runtime'
            )
            runtime_id = response['agentRuntime']['agentRuntimeId']
            runtime_arn = response['agentRuntime']['agentRuntimeArn']
            latest_version = response['agentRuntime']['agentRuntimeVersion']
            print(f"✅ Runtime created: {runtime_id}")
            print(f"📋 Runtime ARN: {runtime_arn}")
            print(f"📋 Version: {latest_version}")
            
            # Wait for runtime to be ready
            wait_for_runtime_ready(client, runtime_id)
        else:
            # Update existing runtime
            print(f"✓ Updating runtime: {runtime_id}")
            response = client.update_agent_runtime(
                agentRuntimeId=runtime_id,
                agentRuntimeArtifact={
                    'codeConfiguration': {
                        'code': {
                            's3': {
                                'bucket': bucket,
                                'key': key
                            }
                        },
                        'runtime': 'PYTHON_3_11',
                        'entryPoint': ['agent.py']
                    }
                },
                roleArn=ROLE_ARN
            )
            runtime_arn = response['agentRuntime']['agentRuntimeArn']
            latest_version = response['agentRuntime']['agentRuntimeVersion']
            print(f"✅ Runtime updated")
            print(f"📋 Runtime ARN: {runtime_arn}")
            print(f"📋 Version: {latest_version}")
            
            # Wait for runtime to be ready
            wait_for_runtime_ready(client, runtime_id)
        
        # Create or update endpoint
        endpoint_exists = False
        try:
            endpoints_response = client.list_agent_runtime_endpoints(agentRuntimeId=runtime_id)
            for ep in endpoints_response.get('agentRuntimeEndpoints', []):
                if ep['name'] == endpoint_name:
                    endpoint_exists = True
                    print(f"✓ Found existing endpoint: {endpoint_name}")
                    break
        except ClientError as e:
            error_code = e.response['Error']['Code']
            print(f"⚠️  Could not list endpoints: {error_code}")
        
        if not endpoint_exists:
            # Create endpoint
            print(f"✓ Creating endpoint: {endpoint_name}")
            if is_prod and latest_version:
                # PROD: Point to specific version
                endpoint_response = client.create_agent_runtime_endpoint(
                    agentRuntimeId=runtime_id,
                    name=endpoint_name,
                    agentRuntimeVersion=latest_version,
                    description=f'Production endpoint - Version {latest_version}'
                )
                print(f"✅ Endpoint created pointing to version {latest_version}")
            else:
                # PR: Create endpoint pointing to current version (will be updated after runtime updates)
                endpoint_response = client.create_agent_runtime_endpoint(
                    agentRuntimeId=runtime_id,
                    name=endpoint_name,
                    agentRuntimeVersion=latest_version,
                    description=f'PR endpoint for {runtime_name}'
                )
                print(f"✅ Endpoint created pointing to version {latest_version}")
        elif latest_version:
            # Update endpoint to point to new version (both PROD and PR)
            print(f"✓ Updating endpoint to version {latest_version}")
            if is_prod:
                client.update_agent_runtime_endpoint(
                    agentRuntimeId=runtime_id,
                    endpointName=endpoint_name,
                    agentRuntimeVersion=latest_version,
                    description=f'Production endpoint - Version {latest_version}'
                )
            else:
                client.update_agent_runtime_endpoint(
                    agentRuntimeId=runtime_id,
                    endpointName=endpoint_name,
                    agentRuntimeVersion=latest_version
                )
            print(f"✅ Endpoint updated to version {latest_version}")
        else:
            print(f"✅ Endpoint ready: {endpoint_name}")
        
        print(f"\n✅ Deployment successful!")
        print(f"📋 Runtime ID: {runtime_id}")
        if runtime_arn:
            print(f"📋 Runtime ARN: {runtime_arn}")
        print(f"📋 Endpoint: {endpoint_name}")
        
        # Output for GitHub Actions (using new syntax)
        github_output = os.getenv('GITHUB_OUTPUT')
        if github_output:
            try:
                with open(github_output, 'a') as f:
                    f.write(f"runtime_id={runtime_id}\n")
                    if runtime_arn:
                        f.write(f"runtime_arn={runtime_arn}\n")
                    f.write(f"endpoint_name={endpoint_name}\n")
                    if is_prod and latest_version:
                        f.write(f"version={latest_version}\n")
            except Exception as e:
                print(f"⚠️  Could not write GitHub Actions output: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python deploy.py <runtime-name> <endpoint-name> [--prod] [--create] [--update]")
        sys.exit(1)
    
    runtime = sys.argv[1]
    endpoint = sys.argv[2]
    is_prod = "--prod" in sys.argv
    force_create = "--create" in sys.argv
    force_update = "--update" in sys.argv
    
    if force_create and force_update:
        print("❌ Cannot specify both --create and --update")
        sys.exit(1)
    
    success = deploy(runtime, endpoint, is_prod, force_create, force_update)
    sys.exit(0 if success else 1)
