"""
Shared pytest configuration for fastapi_app tests.

Sets environment variables that must be in place *before* any test-module
imports happen (i.e. before conftest finishes loading).  Doing this here
instead of inside individual test files ensures they take effect even when
pytest collects in parallel or in a different order.

The pytest_configure hook fires at the very start of the pytest session —
before any test modules or plugins are imported — which guarantees the env
vars are present even if something deep in the import chain (e.g. litellm
via llm_service via agents.graph) triggers a network call.
"""
import os


def pytest_configure(config):  # noqa: ARG001
    """Set guard env-vars at the earliest pytest hook so no import can race ahead."""
    # ── LiteLLM ────────────────────────────────────────────────────────────
    # Prevent LiteLLM from attempting a remote HTTPS fetch of model cost data
    # during import.  Without this flag the first test run blocks for ~90 s
    # waiting for an SSL handshake to https://raw.githubusercontent.com/... to
    # time out before falling back to the bundled local copy.
    os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

    # ── CrewAI / OpenTelemetry telemetry ───────────────────────────────────
    os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")


# Also set at module-load time as a belt-and-suspenders fallback
# (conftest.py itself is imported before most test modules, but after
#  pytest_configure has already fired via the hook above).
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
