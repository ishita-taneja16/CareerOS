"""
CareerOS Multi-Agent Workflows Package
---------------------------------------
Contains LangGraph supervisor/specialist agents and CrewAI demonstration tools.

NOTE: compiled_graph is intentionally NOT imported at module level.
Importing graph.py triggers litellm (via llm_service) which makes a network
request during import unless LITELLM_LOCAL_MODEL_COST_MAP=True is already set.
During pytest collection this causes a ~90 s hang because conftest.py hasn't
had a chance to set the environment variable yet.

Use ``from agents.graph import compiled_graph`` directly in code that needs it
(after the env-var guard in conftest.py has executed), or call get_compiled_graph().
"""

__all__ = ["get_compiled_graph"]


def get_compiled_graph():
    """Lazy accessor for the compiled LangGraph workflow.

    Import is deferred so that litellm (pulled in transitively by llm_service)
    is not imported at pytest-collection time before conftest.py sets
    LITELLM_LOCAL_MODEL_COST_MAP=True.
    """
    from .graph import compiled_graph  # noqa: PLC0415
    return compiled_graph
