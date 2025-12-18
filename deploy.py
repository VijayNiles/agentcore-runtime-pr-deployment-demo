#!/usr/bin/env python3
import subprocess
import sys
import os
import json

def deploy(runtime_name, endpoint_name, is_prod=False):
    """Deploy agent using bedrock-agentcore-toolkit."""
    
    print(f"🚀 Deploying to runtime: {runtime_name}")
    print(f"📍 Endpoint: {endpoint_name}")
    
    # Package and deploy using toolkit
    cmd = [
        "bedrock-agentcore-toolkit", "deploy",
        "--runtime-name", runtime_name,
        "--endpoint-name", endpoint_name,
        "--region", "us-east-1",
        "--s3-bucket", "agentcore-runtime-pr-deployment-demo",
        "--model-id", "global.anthropic.claude-haiku-4-5-20251001-v1:0",
        "--code-path", "./agent"
    ]
    
    if is_prod:
        cmd.extend(["--create-new-version"])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Deployment successful!")
        print(result.stdout)
        
        # Extract runtime ID from output if available
        for line in result.stdout.split('\n'):
            if 'runtime' in line.lower() and 'id' in line.lower():
                print(f"\n📋 {line}")
        
        return True
    else:
        print("❌ Deployment failed!")
        print(result.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python deploy.py <runtime-name> <endpoint-name> [--prod]")
        sys.exit(1)
    
    runtime = sys.argv[1]
    endpoint = sys.argv[2]
    is_prod = "--prod" in sys.argv
    
    success = deploy(runtime, endpoint, is_prod)
    sys.exit(0 if success else 1)
