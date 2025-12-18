from strands import Agent

# Phase 1: Hello World Agent
agent = Agent(
    system_prompt="You are a helpful assistant. When asked anything, respond with 'Hello World'."
)

def handler(event, context):
    """
    Handler function for Bedrock AgentCore runtime.
    """
    user_input = event.get("input", "")
    response = agent(user_input)
    return {"response": response}
