# AWS AgentCore Runtime: Custom Zip + Boto3 Deployment Method

## The Problem We Solved
Your runtime wasn't starting because we were only uploading the Python source files without their dependencies, using wrong package names, and not setting proper file permissions.

## Complete Build Process

### **Step 1: Install ARM64 Dependencies**
```bash
uv pip install \
  --python-platform aarch64-manylinux2014 \
  --python-version 3.11 \
  --target deployment_package \
  --only-binary=:all: \
  -r requirements.txt
```

**Key points:**
- Must use `aarch64-manylinux2014` (ARM64 architecture for AWS Graviton)
- Python version must match runtime configuration (`PYTHON_3_11`)
- `--only-binary=:all:` ensures no compilation (runtime has no build tools)
- Install TO a directory, not into a virtual environment

### **Step 2: Set POSIX Permissions**
```bash
# Directories: 755 (rwxr-xr-x)
chmod 755 deployment_package/**/

# Files: 644 (rw-r--r--)
chmod 644 deployment_package/**/*
```

**Why:** The runtime extracts your zip and runs as a non-root user. Without proper permissions, Python can't read/import your modules → 30s initialization timeout.

### **Step 3: Create Zip with Native Command**
```bash
cd deployment_package
zip -r ../deployment_package.zip . -x "*.pyc" "*__pycache__*"
```

**Why native `zip` not Python's `zipfile`:** Native zip preserves Unix file permissions in the zip metadata. Python's zipfile module doesn't reliably store these permissions.

### **Step 4: Add Your Code to Zip Root**
```bash
cd ..
chmod 644 agent.py
zip deployment_package.zip agent.py
```

**Key point:** Your entrypoint file must be at the **root** of the zip, not in a subfolder.

### **Step 5: Upload to S3**
```python
s3_client.upload_file(
    'deployment_package.zip',
    'your-bucket-name',
    'runtime-name/deployment_package.zip'
)
```

### **Step 6: Create/Update Runtime**
```python
agentcore_client.create_agent_runtime(
    agentRuntimeName='your-runtime',
    agentRuntimeArtifact={
        'codeConfiguration': {
            'code': {
                's3': {
                    'bucket': 'your-bucket',
                    'prefix': 'runtime-name/deployment_package.zip'
                }
            },
            'runtime': 'PYTHON_3_11',
            'entryPoint': ['agent.py']  # Must match filename in zip root
        }
    },
    roleArn='arn:aws:iam::account:role/YourRole',
    networkConfiguration={'networkMode': 'PUBLIC'},
    protocolConfiguration={'serverProtocol': 'HTTP'}
)
```

## Critical Lessons Learned

### 1. **Package Names Matter**
- ❌ `strands` (wrong - no ARM64 wheels)
- ✅ `strands-agents` (correct - has pre-built ARM64 wheels)

### 2. **Import Path is Crucial**
- ❌ `from bedrock_agentcore import BedrockAgentCoreApp` (wrong module path)
- ✅ `from bedrock_agentcore.runtime import BedrockAgentCoreApp` (correct)

### 3. **Lazy Initialization Required**
Don't initialize heavy objects at module import time:
```python
# ❌ BAD - Agent initialized at import (can timeout)
agent = Agent()

# ✅ GOOD - Lazy initialization
_agent = None
def get_agent():
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent
```

### 4. **What the 30s Timeout Covers**
- Downloading zip from S3
- Extracting zip
- Starting Python interpreter
- **Importing your module** (`import agent`)
- Starting the HTTP server

Heavy work (model downloads, DB connections) must happen **after** initialization, not during import.

## Behind the Scenes: How AgentCore Runtime Works

Based on all the requirements, here's what's happening:

```
1. AWS fetches your zip from S3
2. Extracts it to /var/task in an ARM64 Linux container (Graviton)
3. Runs as non-root user (needs 644/755 permissions)
4. Executes: python3.11 agent.py (30s timeout)
5. Your app.run() starts an HTTP server
6. Runtime forwards requests to your server
```

It's essentially **AWS Lambda's execution model but for long-running HTTP services** instead of short functions.

## Size Limits
- 250 MB (zipped)
- 750 MB (unzipped)

## Working Implementation

**Your working script:** `deploy_runtime_with_deps.py` correctly implements all these steps! 🚀

## Why AWS Requires These Specific Steps

### ARM64 Architecture
AWS is running your code on ARM64-based servers (AWS Graviton processors) for cost efficiency and performance. This is a custom container runtime, not Lambda.

### POSIX Permissions
The runtime extracts your zip and runs it in a Linux container with a non-root user for security. Without proper permissions, the Python interpreter can't import your modules.

### Native `zip` Command
Python's `zipfile` module often doesn't preserve Unix file permissions in the zip metadata. The runtime extraction process relies on zip file permission metadata stored by the native `zip` command.

### `--only-binary=:all:` Flag
Forces pip to only use pre-built wheels, no compilation. The runtime environment has no C compiler or build tools - it's a minimal runtime container for fast cold starts.

### Two-Step Zip Process
Ensures your code is at the root level of the zip, not nested. The Python interpreter's `sys.path` starts at the zip root. If files are nested, Python can't find them as modules.
