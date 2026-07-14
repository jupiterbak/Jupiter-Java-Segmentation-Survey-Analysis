# ============================================================
# Agent Definition — Jupiter Java Segmentation Survey Analysis
# ============================================================
# This module builds the root ADK Agent (Marveryx) and wires
# in MCP toolsets based on environment-variable feature flags.
# ============================================================

import os
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from dotenv import load_dotenv

load_dotenv()  # Load variables from .env into os.environ

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.llm_agent import ToolUnion
from google.adk.models.llm_response import LlmResponse
from google.adk.planners import PlanReActPlanner
from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    StreamableHTTPConnectionParams,
    StdioConnectionParams,       # Used by commented optional toolsets below
)
from google.genai import types as genai_types
from mcp import StdioServerParameters  # Used by commented optional toolsets below

from .prompts import return_instructions_root


# --- Helper: read a boolean environment variable safely ---
def get_bool_env_var(env_var_name: str, default: bool) -> bool:
    """Returns True if the env var is set to 'true' (case-insensitive)."""
    return os.getenv(env_var_name, str(default)).lower() == "true"


# --- Helper: read a required environment variable or raise early ---
def get_required_env_var(var_name: str) -> str:
    """Raises ValueError at startup if a required env var is missing."""
    value = os.getenv(var_name)
    if not value:
        raise ValueError(f"{var_name} not set")
    return value


# --- Helper: append MCP query params (toolsets, readOnly) to the base URL ---
def build_mcp_url(base_url: str, toolsets: list[str], read_only: bool) -> str:
    """Appends ?toolsets=...&readOnly=true to the MCP server URL, per Alteryx MCP conventions."""
    parsed = urlparse(base_url)
    query = dict(parse_qsl(parsed.query))
    if toolsets:
        query["toolsets"] = ",".join(toolsets)
    if read_only:
        query["readOnly"] = "true"
    return urlunparse(parsed._replace(query=urlencode(query)))


# --- Callback: surface a message when the model's turn ends with no content ---
# Gemini occasionally emits a malformed function call (or is cut off) while
# chaining several tool calls in one turn. When that happens, ADK builds an
# LlmResponse with error_code set and no content/parts, and the agent loop
# ends the turn silently — the user sees the tools run and then nothing.
# This callback swaps that empty response for a visible, actionable message.
# def _recover_from_empty_model_response(
#     callback_context: CallbackContext, llm_response: LlmResponse
# ) -> Optional[LlmResponse]:
#     if llm_response.content and llm_response.content.parts:
#         return None  # Response already has visible content — leave it alone.
#     if not llm_response.error_code:
#         return None  # No content but no error either — nothing to recover from.

#     return LlmResponse(
#         content=genai_types.Content(
#             role="model",
#             parts=[genai_types.Part(text=(
#                 "I hit an internal snag chaining tool calls for that request "
#                 f"(`{llm_response.error_code}`) and couldn't finish the analysis. "
#                 "Could you narrow the question — e.g. one cluster, one measure, "
#                 "or one time period at a time — and I'll try again?"
#             ))],
#         ),
#     )


# --- Agent factory ---
def get_root_agent() -> Agent:
    # Step 1 — Resolve model and shared runtime context
    MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")
    utc_now = datetime.now(timezone.utc)  # Used in the alternative inline instruction below

    # Step 2 — Build the tool list dynamically from feature flags
    tools: list[ToolUnion] = []

    # Step 2a — Alteryx MCP server (single endpoint, toolsets selected via query params:
    # ?toolsets=agentyx,insights and, optionally, &readOnly=true)
    toolsets: list[str] = []
    if get_bool_env_var("AGENTYX_ENABLED", False):
        toolsets.append("agentyx")
    if get_bool_env_var("INSIGHTS_ENABLED", False):
        toolsets.append("insights")

    if toolsets:
        alteryx_mcp_url = get_required_env_var("ALTERYX_MCP_URL")
        alteryx_mcp_token = get_required_env_var("ALTERYX_MCP_TOKEN")
        read_only = get_bool_env_var("ALTERYX_MCP_READ_ONLY", False)

        tools.append(McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=build_mcp_url(alteryx_mcp_url, toolsets, read_only),
                headers={"Authorization": f"Bearer {alteryx_mcp_token}"},
            ),
        ))

    # Step 2c — (Optional) AntV charting via stdio MCP — enable with CHARTING_ENABLED=TRUE
    # if get_bool_env_var("CHARTING_ENABLED", False):
    #     tools.append(McpToolset(
    #         connection_params=StdioConnectionParams(
    #             server_params=StdioServerParameters(
    #                 command="npx",
    #                 args=["-y", "@antv/mcp-server-chart"],
    #             ),
    #             timeout=300,  # Increased timeout for better reliability
    #         ),
    #     ))

    # Step 2d — (Optional) Sequential thinking toolset via stdio MCP
    # tools.append(
    #     McpToolset(
    #         connection_params=StdioConnectionParams(
    #             server_params=StdioServerParameters(
    #                 command="npx",
    #                 args=["-y", "@modelcontextprotocol/server-sequential-thinking"],
    #             ),
    #             timeout=300,  # Increased timeout for better reliability
    #         ),
    #     ),
    # )

    # Step 4 — Assemble and return the agent
    return Agent(
        name="agentyx_agent",
        model=MODEL_NAME,
        description="Marveryx the Alteryx Agent that can answer user questions using Auto-Insights.",
        instruction=return_instructions_root(),  # Loads system prompt from prompts.py
        tools=tools,
        # planner=PlanReActPlanner(),              # Uses Plan-then-ReAct reasoning strategy
        # after_model_callback=_recover_from_empty_model_response,
    )


# --- Module-level agent instance (loaded once at import time by ADK) ---
root_agent = get_root_agent()
