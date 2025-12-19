from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
import os

app = BedrockAgentCoreApp()

# Agent with configurable prompt
# Initialize agent lazily to avoid timeout during runtime initialization
_agent = None

def load_prompt():
    """Load system prompt from file, with fallback to default."""
    prompt_file = "system_prompt.txt"
    
    # Try to load from prompt file in the same directory
    if os.path.exists(prompt_file):
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Warning: Failed to load prompt from {prompt_file}: {e}")
    
    # Fallback to default prompt
    return """You are a helpful AI assistant. Respond to user queries in a clear, concise, and friendly manner."""

def get_agent():
    """Lazy initialization of agent to avoid runtime initialization timeout"""
    global _agent
    if _agent is None:
        system_prompt = load_prompt()
        _agent = Agent(system_prompt=system_prompt)
    return _agent

@app.entrypoint
def invoke(payload):
    """Handler for AgentCore Runtime"""
    user_message = payload.get("prompt", "")
    agent = get_agent()
    result = agent(user_message)
    return {"result": result.message}

if __name__ == "__main__":
    app.run()
