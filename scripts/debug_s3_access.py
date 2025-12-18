#!/usr/bin/env python3
"""
Debug S3 access for AgentCore runtime role.
This script checks if the AgentCoreRunTimeRole can access the S3 object.
"""
import boto3
import json

ROLE_ARN = 'arn:aws:iam::788835021449:role/AgentCoreRunTimeRole'
S3_BUCKET = 'agentcore-runtime-pr-deployment-demo'
REGION = 'us-east-1'

def check_role_trust_policy():
    """Check the role's trust policy."""
    iam = boto3.client('iam')
    role_name = ROLE_ARN.split('/')[-1]
    
    try:
        response = iam.get_role(RoleName=role_name)
        trust_policy = response['Role']['AssumeRolePolicyDocument']
        
        print("=" * 60)
        print("TRUST POLICY:")
        print("=" * 60)
        print(json.dumps(trust_policy, indent=2))
        
        # Check if bedrock-agentcore is in the trust policy
        for statement in trust_policy.get('Statement', []):
            principal = statement.get('Principal', {})
            service = principal.get('Service', '')
            if isinstance(service, list):
                services = service
            else:
                services = [service] if service else []
            
            print(f"\nTrusted services: {services}")
            if 'bedrock-agentcore.amazonaws.com' in services:
                print("✅ bedrock-agentcore.amazonaws.com is trusted")
            else:
                print("❌ bedrock-agentcore.amazonaws.com is NOT in trust policy!")
                print("   The role cannot be assumed by AgentCore service")
        
        return True
    except Exception as e:
        print(f"❌ Failed to get role: {e}")
        return False

def check_role_policies():
    """Check the role's attached and inline policies for S3 access."""
    iam = boto3.client('iam')
    role_name = ROLE_ARN.split('/')[-1]
    
    try:
        # Check attached policies
        print("\n" + "=" * 60)
        print("ATTACHED POLICIES:")
        print("=" * 60)
        response = iam.list_attached_role_policies(RoleName=role_name)
        
        for policy in response['AttachedPolicies']:
            print(f"\n📋 {policy['PolicyName']}")
            print(f"   ARN: {policy['PolicyArn']}")
            
        # Check inline policies
        print("\n" + "=" * 60)
        print("INLINE POLICIES:")
        print("=" * 60)
        response = iam.list_role_policies(RoleName=role_name)
        
        for policy_name in response['PolicyNames']:
            print(f"\n📋 {policy_name}")
            policy_response = iam.get_role_policy(
                RoleName=role_name,
                PolicyName=policy_name
            )
            print(json.dumps(policy_response['PolicyDocument'], indent=2))
        
        return True
    except Exception as e:
        print(f"❌ Failed to get policies: {e}")
        return False

def check_s3_bucket_policy():
    """Check if S3 bucket has any policy that might block access."""
    s3 = boto3.client('s3', region_name=REGION)
    
    try:
        print("\n" + "=" * 60)
        print("S3 BUCKET POLICY:")
        print("=" * 60)
        
        try:
            response = s3.get_bucket_policy(Bucket=S3_BUCKET)
            policy = json.loads(response['Policy'])
            print(json.dumps(policy, indent=2))
        except s3.exceptions.from_code('NoSuchBucketPolicy'):
            print("No bucket policy configured (using IAM permissions only)")
        
        # Check bucket ACL
        print("\n" + "=" * 60)
        print("S3 BUCKET ACL:")
        print("=" * 60)
        response = s3.get_bucket_acl(Bucket=S3_BUCKET)
        print(f"Owner: {response['Owner']}")
        for grant in response['Grants']:
            print(f"  Grantee: {grant['Grantee']}")
            print(f"  Permission: {grant['Permission']}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to check bucket policy: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Debugging S3 Access for AgentCore Runtime Role")
    print(f"Role: {ROLE_ARN}")
    print(f"Bucket: {S3_BUCKET}")
    print(f"Region: {REGION}\n")
    
    check_role_trust_policy()
    check_role_policies()
    check_s3_bucket_policy()
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    print("""
1. Trust Policy must include:
   {
     "Effect": "Allow",
     "Principal": {
       "Service": "bedrock-agentcore.amazonaws.com"
     },
     "Action": "sts:AssumeRole"
   }

2. Role must have S3 permissions:
   - s3:GetObject on the bucket/prefix/*
   - s3:ListBucket on the bucket
   
3. S3 bucket must not have policies blocking the role's access
""")
