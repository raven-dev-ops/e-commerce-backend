import os
from importlib import util

"""Optional DataDog APM integration."""

# Only patch if ddtrace is installed and tracing is enabled
if util.find_spec("ddtrace") and os.getenv("DD_TRACE_ENABLED", "true").lower() in {
    "true",
    "1",
}:
    from ddtrace import patch_all  # type: ignore

    patch_all()
