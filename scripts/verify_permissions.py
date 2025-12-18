#!/usr/bin/env python3
"""
Verify that the GitHub Actions role has all necessary permissions.
Run this locally or in GitHub Actions to diagnose permission issues.
"""
import boto3
import sys
from botocore.exceptions import ClientError

REGION = 'us-east-1'
ROLE_ARN = 'arn:aws:iam::788835021449:role/AgentCoreRunTimeRole'
S3_BUCKET = 'agentcore-runtime-pr-deployment-demo'

def test_bedrock_agentcore_permissions():
    """Test bedrock-agentcore API access"""
    print("🔍 Testing Bedrock AgentCore permissions...")
    client = boto3.client('bedrock-agentcore', region_name=REGION)
    
    try:
        response = client.list_agent_runtimes()
        print(f"✅ bedrock-agentcore:ListAgentRuntimes - SUCCESS")
        print(f"   Found {len(response.get('agentRuntimes', []))} runtimes")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"❌ bedrock-agentcore:ListAgentRuntimes - FAILED")
        print(f"   Error: {error_code} - {e.response['Error']['Message']}")
        return False

def test_iam_passrole():
    """Test IAM PassRole permission"""
    print("\n🔍 Testing IAM PassRole permission...")
    iam = boto3.client('iam', region_name=REGION)
    
    try:
        role_name = ROLE_ARN.split('/')[-1]
        response = iam.get_role(RoleName=role_name)
        print(f"✅ iam:GetRole - SUCCESS")
        print(f"   Role: {role_name}")
        
        # Check trust policy
        trust_policy = response['Role']['AssumeRolePolicyDocument']
        principals = trust_policy.get('Statement', [{}])[0].get('Principal', {})
        service = principals.get('Service', '')
        
        if 'bedrock-agentcore.amazonaws.com' in service:
            print(f"✅ Trust policy allows bedrock-agentcore.amazonaws.com")
        else:
            print(f"⚠️  Trust policy service: {service}")
            print(f"   Expected: bedrock-agentcore.amazonaws.com")
        
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"❌ iam:GetRole - FAILED")
        print(f"   Error: {error_code} - {e.response['Error']['Message']}")
        return False

def test_s3_permissions():
    """Test S3 bucket permissions"""
    print("\n🔍 Testing S3 permissions...")
    s3 = boto3.client('s3', region_name=REGION)
    
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
        print(f"✅ s3:HeadBucket - SUCCESS")
        print(f"   Bucket: {S3_BUCKET}")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"❌ s3:HeadBucket - FAILED")
        print(f"   Error: {error_code} - {e.response['Error']['Message']}")
        return False

def get_caller_identity():
    """Show which identity is being used"""
    print("🔍 Checking caller identity...")
    sts = boto3.client('sts')
    
    try:
        response = sts.get_caller_identity()
        print(f"✅ Current Identity:")
        print(f"   Account: {response['Account']}")
        print(f"   ARN: {response['Arn']}")
        print(f"   UserId: {response['UserId']}")
        return True
    except ClientError as e:
        print(f"❌ Could not get caller identity: {e}")
        return False

def main():
    print("=" * 60)
    print("AWS Permissions Verification")
    print("=" * 60)
    print()
    
    results = []
    
    # Check identity
    results.append(("Caller Identity", get_caller_identity()))
    print()
    
    # Test permissions
    results.append(("S3 Access", test_s3_permissions()))
    results.append(("IAM Role Access", test_iam_passrole()))
    results.append(("Bedrock AgentCore API", test_bedrock_agentcore_permissions()))
    
    # Summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All permissions verified! Deployment should work.")
        sys.exit(0)
    else:
        print("\n❌ Some permissions are missing. Fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
