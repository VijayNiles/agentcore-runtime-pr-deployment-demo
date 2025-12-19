# TODOs

## Remaining Work

1. **Get prod-promote working by solving for how to get the prod-runtime-id**
   - Current status: Workflow auto-looks up prod runtime by name using `get_agent_runtime(agentRuntimeId="prod")`
   - Need to verify this works in GitHub Actions environment
   - Alternative: If lookup fails, hardcode or pass as input parameter

2. **Update README to show end to end workflow**
   - Document the complete PR → Deploy → Merge → Promote → Cleanup flow
   - Include examples of GitHub issue creation and CLI commands
   - Add screenshots or workflow diagrams
