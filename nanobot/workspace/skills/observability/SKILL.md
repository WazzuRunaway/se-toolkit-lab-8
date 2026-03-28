---
name: observability
description: Use observability MCP tools for logs and traces
always: true
---

# Observability Skill

You have access to observability MCP tools for querying VictoriaLogs and VictoriaTraces. Use these tools to investigate system health, errors, and failures.

## Available Tools

- `mcp_obs_logs_search` — Search logs by keyword and/or time range using LogsQL
- `mcp_obs_logs_error_count` — Count errors per service over a time window
- `mcp_obs_traces_list` — List recent traces for a service
- `mcp_obs_traces_get` — Fetch a specific trace by ID

## Strategy

### When the user asks about errors or system health:

1. Start with `mcp_obs_logs_error_count` to see whether there are recent errors
   - Use a narrow time window (e.g., "10m" or "1h") for fresh data
   - Optionally filter by service name (e.g., "Learning Management Service")

2. If errors exist, use `mcp_obs_logs_search` to inspect the relevant logs
   - Query for `severity:ERROR` and the service name
   - Look for `trace_id` fields in the log entries

3. If you find a `trace_id`, use `mcp_obs_traces_get` to fetch the full trace
   - This shows the complete request flow across services
   - Identify where the failure occurred in the span hierarchy

4. Summarize findings concisely — don't dump raw JSON
   - Mention what service is affected
   - Explain what operation failed
   - Include evidence from both logs and traces

### When the user asks "What went wrong?" or "Check system health":

Follow this investigation flow:

1. Call `mcp_obs_logs_error_count` with a recent time window (e.g., 10 minutes)
2. If errors exist, call `mcp_obs_logs_search` scoped to the failing service
3. Extract a `trace_id` from the error logs
4. Call `mcp_obs_traces_get` with that trace ID
5. Provide a short summary that cites:
   - The error count and time window
   - The specific error from logs (e.g., "PostgreSQL connection refused")
   - The failing operation from traces (e.g., "db_query span failed")
   - Which service is affected

### Example LogsQL queries:

- Recent errors in LMS backend: `_time:10m service.name:"Learning Management Service" severity:ERROR`
- All errors in the last hour: `_time:1h severity:ERROR`
- Specific event: `_time:30m event:"db_query" severity:ERROR`

## Response Style

- Keep responses concise and focused on actionable information
- Cite evidence from both logs and traces when available
- Don't dump raw JSON — summarize the key findings
- If no errors found, say the system looks healthy for the time window checked
