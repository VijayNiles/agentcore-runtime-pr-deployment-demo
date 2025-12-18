from strands import Agent
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

# Phase 1: Hello World Agent
agent = Agent(
    system_prompt="You are a helpful assistant. When asked anything, respond with 'Hello World'."
)

@app.entrypoint
def invoke(payload):
    """Handler for AgentCore Runtime"""
    user_message = payload.get("prompt", "")
    result = agent(user_message)
    return {"result": result.message}

if __name__ == "__main__":
    app.run()
