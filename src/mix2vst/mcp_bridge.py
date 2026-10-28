"""Optional stdio MCP read-only boundary.

Host MUST constrain MIX2VST_WORKSPACE to an approved local private directory.
No remote execution/GPU tool is exposed. Registration/deployment is separate.
"""
from __future__ import annotations
import json
import os
from pathlib import Path

from .batch import BatchPlan
from .exports import audit_instrument


def _approved_path(value: str) -> Path:
    root = os.environ.get("MIX2VST_WORKSPACE")
    if not root:
        raise PermissionError("MIX2VST_WORKSPACE must be set")
    base = Path(root).expanduser().resolve(strict=True)
    # Resolve and check containment BEFORE insisting the target exists.
    # This ensures outside-workspace requests consistently fail closed,
    # even if their destination filename has not been created yet.
    candidate = (base / value).resolve(strict=False)
    if not candidate.is_relative_to(base):
        raise PermissionError("path is outside approved workspace")
    return candidate.resolve(strict=True)


def plan_batch_tool(spec_path: str) -> dict:
    return BatchPlan.from_json(_approved_path(spec_path)).describe()


def audit_library_tool(library_path: str) -> dict:
    return audit_instrument(_approved_path(library_path), require_audio=False)


def main():
    try:
        from fastmcp import FastMCP
    except ImportError as exc:
        raise SystemExit("Install the optional FastMCP package first") from exc
    mcp = FastMCP("VST Sample Library")
    mcp.tool()(plan_batch_tool)
    mcp.tool()(audit_library_tool)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
