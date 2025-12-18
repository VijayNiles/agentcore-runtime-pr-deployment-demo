# Fix Required: AgentCoreRunTimeRole Configuration

## Error
```
ValidationException: S3 operation failed: Bad Request (Service: S3, Status Code: 400)
```

## Root Cause
The `AgentCoreRunTimeRole` (arn:aws:iam::788835021449:role/AgentCoreRunTimeRole) is missing required permissions or trust policy configuration.

## Required Fixes in AWS Console

### 1. Trust Policy (CRITICAL)
The role MUST trust the Bedrock AgentCore service to assume it.

**Navigate to**: IAM → Roles → AgentCoreRunTimeRole → Trust relationships → Edit trust policy

**Required trust policy**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock-agentcore.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### 2. S3 Permissions (CRITICAL)
The role MUST have permissions to read objects from the S3 bucket.

**Navigate to**: IAM → Roles → AgentCoreRunTimeRole → Permissions → Add permissions

**Option A - Attach AWS Managed Policy**:
- Attach: `AmazonS3ReadOnlyAccess` (broad access)

**Option B - Create Inline Policy** (recommended for least privilege):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::agentcore-runtime-pr-deployment-demo",
        "arn:aws:s3:::agentcore-runtime-pr-deployment-demo/*"
      ]
    }
  ]
}
```

### 3. Bedrock Permissions (Already configured)
The role should already have `AmazonBedrockFullAccess` or equivalent. Verify:

**Navigate to**: IAM → Roles → AgentCoreRunTimeRole → Permissions

**Should see one of**:
- `AmazonBedrockFullAccess` (AWS managed policy)
- OR custom policy with `bedrock:*` permissions

## Verification Steps

After making the changes:

1. **Verify Trust Policy**:
   ```bash
   aws iam get-role --role-name AgentCoreRunTimeRole --query 'Role.AssumeRolePolicyDocument'
   ```
   Should show `bedrock-agentcore.amazonaws.com` in the Principal.Service

2. **Verify S3 Permissions**:
   ```bash
   aws iam list-attached-role-policies --role-name AgentCoreRunTimeRole
   aws iam list-role-policies --role-name AgentCoreRunTimeRole
   ```
   Should show S3 read access policies

3. **Test Deployment**:
   After fixing, re-run the GitHub Actions workflow. The deployment should succeed.

## Why This Error Occurs

When you call `create_agent_runtime`, AgentCore:
1. Tries to assume the `AgentCoreRunTimeRole`
2. Attempts to download the code from S3 using that role
3. If the role can't be assumed → Access Denied
4. If the role lacks S3 permissions → S3 400 Bad Request

The "S3 operation failed: Bad Request" happens when AgentCore successfully assumes the role but that role doesn't have permission to access the S3 object.

## Summary Checklist

- [ ] Trust policy includes `bedrock-agentcore.amazonaws.com`
- [ ] Role has S3 GetObject permission on the bucket
- [ ] Role has S3 ListBucket permission on the bucket  
- [ ] Role has Bedrock permissions (already configured)
- [ ] Re-run deployment after fixes
