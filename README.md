# PR-Based Deployments for Amazon Bedrock AgentCore

This demo showcases how to implement PR-based deployment workflows for agents on Amazon Bedrock AgentCore, demonstrating:

- **Isolation**: PR environments don't affect production
- **Versioning**: Multiple versions coexist on the same runtime
- **Instant Rollback**: Change version pointers without rebuilding

## Architecture

- **Shared PROD Runtime**: `demo-prod-runtime` with versioned deployments
- **Ephemeral PR Runtimes**: `demo-pr-{NUMBER}-runtime` created per PR
- **Direct Code Deployment**: Using Custom zip + boto3 method with AgentCore Control APIs
- **S3 Bucket**: `agentcore-runtime-pr-deployment-demo`
- **Agent Framework**: Strands Agents with BedrockAgentCoreApp
- **Execution Role**: `AgentCoreRunTimeRole` with BedrockAgentCoreFullAccess and S3 access

## Prerequisites

```bash
# Install dependencies
pip install boto3 strands bedrock-agentcore

# Configure AWS credentials (already set via OIDC for GitHub Actions)
aws configure
```

## Phase 1: The Setup (Baseline)

### Step 1: Initialize with "Hello World" Agent

The agent is already created in `agent/agent.py` with a "Hello World" prompt.

```bash
# Commit and push to main
git add .
git commit -m "Initial commit: Hello World agent"
git push origin main
```

### Step 2: Baseline Deploy

The GitHub Action will automatically deploy to production, creating Version 1.

**Note**: Save the Runtime ARN from the deployment output - you'll need it for testing.

### Step 3: Test Production

```bash
# Get the runtime ARN from the deployment output, then test:
python scripts/test_endpoint.py <RUNTIME_ARN> demo-prod-endpoint "What do you do?"
```

**Expected Output**: "Hello World"

---

## Phase 2: The Feature (PR Workflow)

### Step 4: Create Feature Branch

```bash
git checkout -b feature/joke-agent
```

### Step 5: Change Agent to Tell Jokes

Edit `agent/agent.py`:

```python
from strands import Agent
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

# Phase 2: Joke Agent
agent = Agent(
    system_prompt="You are a comedian. When asked anything, tell a short, funny joke."
)

@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt", "")
    result = agent(user_message)
    return {"result": result.message}

if __name__ == "__main__":
    app.run()
```

### Step 6: Push and Create PR

```bash
git add agent/agent.py
git commit -m "Feature: Add joke-telling capability"
git push origin feature/joke-agent

# Create PR on GitHub
```

### Step 7: GitHub Action Creates PR Runtime

The workflow will:
- Create `demo-pr-{NUMBER}-runtime`
- Deploy the joke agent
- Comment the runtime details on the PR (including Runtime ARN for testing)

### Step 8: Test PR Endpoint (Isolation Proof)

```bash
# Test PR endpoint - should tell a joke (get ARN from PR comment)
python scripts/test_endpoint.py <PR_RUNTIME_ARN> PR-{NUMBER}-Endpoint "Tell me something"

# Test PROD endpoint - should still say Hello World
python scripts/test_endpoint.py <PROD_RUNTIME_ARN> demo-prod-endpoint "Tell me something"
```

**Key Observation**: Both endpoints work independently. Production is unaffected!

### Step 9: Merge PR

Merge the PR on GitHub. The workflows will:
1. Delete the PR runtime (cleanup-pr.yml)
2. Deploy Version 2 to production runtime (deploy-prod.yml)

### Step 10: Verify Production Update

```bash
python scripts/test_endpoint.py <PROD_RUNTIME_ARN> demo-prod-endpoint "Tell me something"
```

**Expected Output**: A joke (Version 2 is now live)

---

## Phase 3: The Bug & Rollback (Production Safety)

### Step 11: Create Broken Agent

```bash
git checkout -b feature/broken
```

Edit `agent/agent.py`:

```python
from strands import Agent
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

# Phase 3: Broken Agent
agent = Agent(
    system_prompt="ERROR ERROR ERROR SYSTEM MALFUNCTION"
)

@app.entrypoint
def invoke(payload):
    user_message = payload.get("prompt", "")
    # Intentionally broken
    raise Exception("Critical system failure!")
    result = agent(user_message)
    return {"result": result.message}

if __name__ == "__main__":
    app.run()
```

### Step 12: Fast-Forward Merge (Simulate Bad Deploy)

```bash
git add agent/agent.py
git commit -m "Hotfix: Update agent (BROKEN)"
git push origin feature/broken

# Merge immediately to main (skip PR review)
```

### Step 13: Verify Production is Broken

```bash
python scripts/test_endpoint.py <PROD_RUNTIME_ARN> demo-prod-endpoint "Hello"
```

**Expected Output**: Error or broken response (Version 3 is broken)

### Step 14: Instant Rollback to Version 2

```bash
./scripts/rollback.sh <PROD_RUNTIME_ID> demo-prod-endpoint 2
```

### Step 15: Verify Rollback Success

```bash
python scripts/test_endpoint.py <PROD_RUNTIME_ARN> demo-prod-endpoint "Tell me something"
```

**Expected Output**: A joke (back to Version 2, instantly!)

**Key Observation**: No rebuild, no redeploy, just a pointer switch. Rollback in seconds!

---

## Key Takeaways

1. **PR Isolation**: Each PR gets its own runtime, production stays safe
2. **Version Management**: All versions exist simultaneously on the shared runtime
3. **Instant Rollback**: Change version pointers without rebuilding or redeploying
4. **Clean Workflows**: Automated deployment and cleanup via GitHub Actions

## Production Best Practices

While this demo uses a manual rollback script for speed demonstration, production teams typically:
- Wrap rollback in a manual GitHub Action workflow (workflow_dispatch)
- Require approval for rollback operations
- Maintain audit trails via GitOps principles
- Still benefit from instant pointer switching (no rebuild needed)

## Files Structure

```
.
├── agent/
│   ├── agent.py              # Strands agent code
│   └── requirements.txt      # Dependencies
├── .github/workflows/
│   ├── deploy-pr.yml         # PR preview deployments
│   ├── deploy-prod.yml       # Production deployments
│   └── cleanup-pr.yml        # PR runtime cleanup
├── scripts/
│   ├── test_endpoint.py      # Test endpoint script
│   └── rollback.sh           # Manual rollback script
├── deploy.py                 # Deployment helper
└── README.md                 # This file
```
