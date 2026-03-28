"""Tool schemas, handlers, and registry for the observability MCP server."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from mcp.types import Tool
from pydantic import BaseModel, Field

from mcp_obs.client import ObsClient


class NoArgs(BaseModel):
    """Empty input model for tools that only need server-side configuration."""


class LogsSearchQuery(BaseModel):
    query: str = Field(
        description="LogsQL query string, e.g., 'service.name:\"backend\" severity:ERROR'"
    )
    limit: int = Field(
        default=100, ge=1, le=1000, description="Max log entries to return (default 100)"
    )
    time_range: str = Field(
        default="1h",
        description="Time range filter like '1h', '10m', '1d' (default 1h)",
    )


class LogsErrorCountQuery(BaseModel):
    service: str | None = Field(
        default=None, description="Optional service name filter"
    )
    time_range: str = Field(
        default="1h",
        description="Time range filter like '1h', '10m', '1d' (default 1h)",
    )


class TracesListQuery(BaseModel):
    service: str | None = Field(
        default=None, description="Optional service name filter"
    )
    limit: int = Field(
        default=10, ge=1, le=100, description="Max traces to return (default 10)"
    )


class TracesGetQuery(BaseModel):
    trace_id: str = Field(description="The trace ID to fetch")


ToolPayload = BaseModel | list | dict
ToolHandler = Callable[[ObsClient, BaseModel], Awaitable[ToolPayload]]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    model: type[BaseModel]
    handler: ToolHandler

    def as_tool(self) -> Tool:
        schema = self.model.model_json_schema()
        schema.pop("$defs", None)
        schema.pop("title", None)
        return Tool(name=self.name, description=self.description, inputSchema=schema)


async def _logs_search(client: ObsClient, args: BaseModel) -> ToolPayload:
    query = args.model_dump()
    return await client.logs_search(
        query=query["query"],
        limit=query["limit"],
        time_range=query["time_range"],
    )


async def _logs_error_count(client: ObsClient, args: BaseModel) -> ToolPayload:
    query = args.model_dump()
    return await client.logs_error_count(
        service=query.get("service"),
        time_range=query["time_range"],
    )


async def _traces_list(client: ObsClient, args: BaseModel) -> ToolPayload:
    query = args.model_dump()
    return await client.traces_list(
        service=query.get("service"),
        limit=query["limit"],
    )


async def _traces_get(client: ObsClient, args: BaseModel) -> ToolPayload:
    query = args.model_dump()
    return await client.traces_get(trace_id=query["trace_id"])


TOOL_SPECS = (
    ToolSpec(
        "logs_search",
        "Search logs by keyword and/or time range using LogsQL. Returns matching log entries.",
        LogsSearchQuery,
        _logs_search,
    ),
    ToolSpec(
        "logs_error_count",
        "Count errors per service over a time window. Returns error count and metadata.",
        LogsErrorCountQuery,
        _logs_error_count,
    ),
    ToolSpec(
        "traces_list",
        "List recent traces for a service. Returns trace summaries with IDs and durations.",
        TracesListQuery,
        _traces_list,
    ),
    ToolSpec(
        "traces_get",
        "Fetch a specific trace by ID. Returns full trace data with all spans.",
        TracesGetQuery,
        _traces_get,
    ),
)
TOOLS_BY_NAME = {spec.name: spec for spec in TOOL_SPECS}
