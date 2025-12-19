# AgentCore Runtime Deployment Scripts

This repository contains scripts for deploying and managing AWS Bedrock AgentCore Runtimes with proper ARM64 dependencies.

## Prerequisites

- AWS credentials configured
- Python 3.9+
- `uv` package manager installed
- Required Python packages: `boto3`

## Scripts Overview

### 1. Deploy Runtime

Deploy a new AgentCore Runtime with ARM64 dependencies.

**Script:** `deploy_runtime_with_deps.py`

**Usage:**
```bash
# Deploy with default prompt
python3 deploy_runtime_with_deps.py

# Deploy with a specific prompt file
python3 deploy_runtime_with_deps.py --prompt <path_to_prompt_file>
```

**Examples:**
```bash
# Deploy with dad joke bot personality
python3 deploy_runtime_with_deps.py --prompt prompts/dad_joke_bot.txt

# Deploy with motivational quotes bot personality
python3 deploy_runtime_with_deps.py --prompt prompts/motivational_quotes_bot.txt
```

**Output:**
- Creates a new runtime with a unique ID
- Returns Runtime ID, Runtime ARN, and Version number

---

### 2. Update Runtime

Update an existing AgentCore Runtime with new code or a different prompt.

**Script:** `update_runtime_with_deps.py`

**Usage:**
```bash
# Update runtime (keeps existing prompt)
python3 update_runtime_with_deps.py <runtime_id>

# Update runtime with a new prompt
python3 update_runtime_with_deps.py <runtime_id> --prompt <path_to_prompt_file>
```

**Examples:**
```bash
# Update runtime keeping current configuration
python3 update_runtime_with_deps.py test_runtime_with_deps_1234567890-AbCdEfGhIj

# Update runtime with dad joke bot personality
python3 update_runtime_with_deps.py test_runtime_with_deps_1234567890-AbCdEfGhIj --prompt prompts/dad_joke_bot.txt

# Update runtime with motivational quotes bot personality
python3 update_runtime_with_deps.py test_runtime_with_deps_1234567890-AbCdEfGhIj --prompt prompts/motivational_quotes_bot.txt
```

**Output:**
- Creates a new version of the runtime
- Returns Runtime ARN and new Version number

---

### 3. Create Endpoint

Create an endpoint (alias) that points to a specific runtime version.

**Script:** `create_endpoint.py`

**Usage:**
```bash
# Create endpoint with auto-generated name
python3 create_endpoint.py <runtime_id> <version>

# Create endpoint with custom name
python3 create_endpoint.py <runtime_id> <version> <endpoint_name>
```

**Examples:**
```bash
# Create endpoint with auto-generated name pointing to version 1
python3 create_endpoint.py test_runtime_with_deps_1234567890-AbCdEfGhIj 1

# Create production endpoint pointing to version 1
python3 create_endpoint.py test_runtime_with_deps_1234567890-AbCdEfGhIj 1 prod_deployment

# Create staging endpoint pointing to version 2
python3 create_endpoint.py test_runtime_with_deps_1234567890-AbCdEfGhIj 2 staging_deployment
```

**Output:**
- Endpoint Name
- Endpoint ARN
- Confirms version it points to

---

### 4. Update Endpoint

Update an existing endpoint to point to a different runtime version.

**Script:** `update_endpoint.py`

**Usage:**
```bash
python3 update_endpoint.py <runtime_id> <endpoint_name> <new_version>
```

**Examples:**
```bash
# Update prod_deployment endpoint to point to version 2
python3 update_endpoint.py test_runtime_with_deps_1234567890-AbCdEfGhIj prod_deployment 2

# Update staging_deployment endpoint to point to version 3
python3 update_endpoint.py test_runtime_with_deps_1234567890-AbCdEfGhIj staging_deployment 3
```

**Output:**
- Shows current endpoint status and version
- Confirms update to new version
- Returns Endpoint ARN

---

### 5. Clean Up Runtime

Delete all custom endpoints and the runtime itself. This is a destructive operation that requires confirmation.

**Script:** `cleanup_runtime.py`

**Usage:**
```bash
python3 cleanup_runtime.py <runtime_id>
```

**Examples:**
```bash
# Clean up a runtime (will prompt for confirmation)
python3 cleanup_runtime.py test_runtime_with_deps_1234567890-AbCdEfGhIj
```

**What it does:**
1. Lists all endpoints for the runtime
2. Deletes all custom endpoints (keeps 'default' endpoint if present)
3. Verifies each endpoint deletion
4. Deletes the runtime itself
5. Waits for and verifies runtime deletion

**Output:**
- Lists all endpoints found
- Shows deletion progress for each endpoint
- Verifies endpoint deletions
- Confirms runtime deletion with status updates
- ⚠️ Requires typing 'DELETE' to confirm the operation

**Safety Features:**
- Interactive confirmation required (type 'DELETE')
- Preserves 'default' endpoint (if it exists)
- Verifies each deletion before proceeding
- Detailed status reporting
- Error handling with clear messages

---

## Complete Workflow Example

Here's a typical deployment workflow:

```bash
# 1. Deploy a new runtime with dad joke bot
python3 deploy_runtime_with_deps.py --prompt prompts/dad_joke_bot.txt
# Output: Runtime ID: test_runtime_with_deps_1234567890-AbCdEfGhIj, Version: 1

# 2. Create a production endpoint pointing to version 1
python3 create_endpoint.py test_runtime_with_deps_1234567890-AbCdEfGhIj 1 prod_deployment
# Output: Endpoint prod_deployment created, pointing to version 1

# 3. Update the runtime with a new personality
python3 update_runtime_with_deps.py test_runtime_with_deps_1234567890-AbCdEfGhIj --prompt prompts/motivational_quotes_bot.txt
# Output: New Version: 2

# 4. Update the production endpoint to use the new version
python3 update_endpoint.py test_runtime_with_deps_1234567890-AbCdEfGhIj prod_deployment 2
# Output: prod_deployment now points to version 2

# 5. When done, clean up the runtime and all endpoints
python3 cleanup_runtime.py test_runtime_with_deps_1234567890-AbCdEfGhIj
# Output: Deletes all custom endpoints, then deletes the runtime
```

---

## Available Prompts

The repository includes pre-configured prompts in the `prompts/` directory:

- **`dad_joke_bot.txt`** - Responds with dad jokes to everything
- **`motivational_quotes_bot.txt`** - Provides motivational quotes and encouragement

You can create your own prompt files following the same format.

---

## Agent Structure

The agent code is located in `agent/agent.py` and automatically reads the system prompt from a `system_prompt.txt` file if included in the deployment package.

**Requirements:**
- `agent/requirements.txt` - Python dependencies
  - `strands-agents` - Agent framework
  - `bedrock-agentcore` - AgentCore SDK

---

## Deployment Package Process

The deployment process (handled by `deployment_utils.py`):

1. Installs ARM64-compatible Python dependencies using `uv`
2. Sets proper POSIX permissions (644 for files, 755 for directories)
3. Creates a zip package using native `zip` command (preserves permissions)
4. Adds `agent.py` and optional `system_prompt.txt` to the zip root
5. Uploads to S3
6. Creates/updates the runtime via AWS API

---

## Troubleshooting

### Runtime initialization timeout
- Ensure your agent code doesn't perform heavy operations during import
- Use lazy initialization for expensive resources
- Check CloudWatch logs for detailed error messages

### Permission errors
- The deployment scripts handle permissions automatically
- If issues persist, verify your IAM role has proper S3 and AgentCore permissions

### Package size limits
- Maximum 250 MB (zipped), 750 MB (unzipped)
- The script will warn you if the package exceeds limits

---

## Additional Resources

- See `learnings-build-process.md` for detailed explanation of the build process
- Check AWS documentation for AgentCore Runtime API details
