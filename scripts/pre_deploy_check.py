#!/usr/bin/env python3
"""
Pre-deployment check script.
Run this before deploying to catch configuration issues early.
"""
import boto3
import sys
from botocore.exceptions import ClientError

REGION = 'us-east-1'
ROLE_ARN = 'arn:aws:iam::788835021449:role/AgentCoreRunTimeRole'
S3_BUCKET = 'agentcore-runtime-pr-deployment-demo'

def main():
    print("🔍 Pre-Deployment Checks\n")
    
    # Test 1: Check AWS credentials
    print("1️⃣  Checking AWS credentials...")
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"   ✅ Authenticated as: {identity['Arn']}\n")
    except Exception as e:
        print(f"   ❌ Authentication failed: {e}\n")
        return False
    
    # Test 2: Test bedrock-agentcore service access
    print("2️⃣  Testing bedrock-agentcore service...")
    try:
        client = boto3.client('bedrock-agentcore', region_name=REGION)
        response = client.list_agent_runtimes()
        runtimes = response.get('agentRuntimes', [])
        print(f"   ✅ Service accessible. Found {len(runtimes)} runtimes")
        for runtime in runtimes:
            print(f"      - {runtime.get('agentRuntimeName')} (ID: {runtime.get('agentRuntimeId')})")
        print()
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print(f"   ❌ ACCESS DENIED to bedrock-agentcore")
            print(f"   📋 Add this policy to GitHub-Actions-Role:")
            print("""
   {
     "Effect": "Allow",
     "Action": [
       "bedrock-agentcore:*"
     ],
     "Resource": "*"
   }
            """)
        else:
            print(f"   ❌ Error: {error_code} - {e.response['Error']['Message']}")
        print()
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}\n")
        return False
    
    # Test 3: Verify execution role exists
    print("3️⃣  Verifying execution role...")
    try:
        iam = boto3.client('iam')
        role_name = ROLE_ARN.split('/')[-1]
        role = iam.get_role(RoleName=role_name)
        print(f"   ✅ Role exists: {role_name}")
        
        # Check trust policy
        trust = role['Role']['AssumeRolePolicyDocument']
        services = [stmt.get('Principal', {}).get('Service', '') 
                   for stmt in trust.get('Statement', [])]
        
        if any('bedrock-agentcore.amazonaws.com' in str(s) for s in services):
            print(f"   ✅ Trust policy allows bedrock-agentcore.amazonaws.com")
        else:
            print(f"   ⚠️  Trust policy may need bedrock-agentcore.amazonaws.com")
            print(f"      Current services: {services}")
        print()
    except ClientError as e:
        print(f"   ❌ Error accessing role: {e.response['Error']['Code']}\n")
        return False
    
    # Test 4: Verify S3 bucket access
    print("4️⃣  Verifying S3 bucket...")
    try:
        s3 = boto3.client('s3', region_name=REGION)
        s3.head_bucket(Bucket=S3_BUCKET)
        print(f"   ✅ Bucket accessible: {S3_BUCKET}\n")
    except ClientError as e:
        print(f"   ❌ Error: {e.response['Error']['Code']}\n")
        return False
    
    # Test 5: Try to test PassRole (indirect)
    print("5️⃣  Checking IAM PassRole permission...")
    try:
        # We can't directly test PassRole, but we can check policies
        iam = boto3.client('iam')
        caller_arn = sts.get_caller_identity()['Arn']
        
        if 'GitHub-Actions-Role' in caller_arn:
            print(f"   ✅ Running as GitHub-Actions-Role")
            print(f"   ℹ️  PassRole will be tested during actual deployment")
        elif 'assumed-role' in caller_arn:
            print(f"   ✅ Running with assumed role")
        else:
            print(f"   ℹ️  Running as: {caller_arn}")
        print()
    except Exception as e:
        print(f"   ⚠️  Could not verify: {e}\n")
    
    print("=" * 60)
    print("✅ All pre-deployment checks passed!")
    print("=" * 60)
    print("\nYou can proceed with deployment.")
    print("Run: python deploy.py <runtime-name> <endpoint-name> [--prod]")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
