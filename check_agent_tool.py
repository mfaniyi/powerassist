from agent_framework import tool

@tool
def sample_lookup(state: str) -> str:
    """Look up electricity information for a state."""
    return f"Looking up {state}"

print("Type:", type(sample_lookup).__name__)
print("Callable:", callable(sample_lookup))
print("Name:", sample_lookup.name)
