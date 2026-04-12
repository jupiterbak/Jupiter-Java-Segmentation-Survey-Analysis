# ============================================================
# Agent Definition — Jupiter Java Segmentation Survey Analysis
# ============================================================
# This module builds the root ADK Agent (Marveryx) and wires
# in MCP toolsets based on environment-variable feature flags.
# ============================================================

import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()  # Load variables from .env into os.environ

from google.adk.agents import Agent
from google.adk.agents.llm_agent import ToolUnion
from google.adk.planners import PlanReActPlanner
from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    StreamableHTTPConnectionParams,
    StdioConnectionParams,       # Used by commented optional toolsets below
)
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


# --- Agent factory ---
def get_root_agent() -> Agent:
    # Step 1 — Resolve model and shared runtime context
    MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")
    utc_now = datetime.now(timezone.utc)  # Used in the alternative inline instruction below

    # Step 2 — Build the tool list dynamically from feature flags
    tools: list[ToolUnion] = []

    # Step 2a — Alteryx Agentyx (workflow MCP tool)
    if get_bool_env_var("AGENTYX_ENABLED", False):
        agentyx_url = get_required_env_var("AGENTYX_URL")
        agentyx_token = get_required_env_var("AGENTYX_TOKEN")

        tools.append(McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=agentyx_url,
                headers={"Authorization": f"Bearer {agentyx_token}"},
            ),
        ))

    # Step 2b — Alteryx Auto Insights (analytics MCP tool)
    if get_bool_env_var("INSIGHTS_ENABLED", False):
        insights_url = get_required_env_var("INSIGHTS_URL")
        insights_access_key = get_required_env_var("INSIGHTS_ACCESS_KEY")
        insights_secret = get_required_env_var("INSIGHTS_SECRET")

        tools.append(McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=insights_url,
                headers={
                    "x-access-key": insights_access_key,
                    "x-secret": insights_secret,
                },
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
        planner=PlanReActPlanner(),              # Uses Plan-then-ReAct reasoning strategy
    )


# --- Module-level agent instance (loaded once at import time by ADK) ---
root_agent = get_root_agent()
