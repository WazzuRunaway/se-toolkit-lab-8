"""HTTP client for VictoriaLogs and VictoriaTraces APIs."""

from __future__ import annotations

import httpx

from mcp_obs.settings import ObsSettings


class ObsClient:
    """Client for querying VictoriaLogs and VictoriaTraces."""

    def __init__(self, settings: ObsSettings) -> None:
        self.victorialogs_url = settings.victorialogs_url
        self.victoriatraces_url = settings.victoriatraces_url
        self._http_client: httpx.AsyncClient | None = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient()
        return self._http_client

    async def close(self) -> None:
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self) -> "ObsClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    # VictoriaLogs API methods
    async def logs_search(
        self, query: str, limit: int = 100, time_range: str = "1h"
    ) -> list[dict]:
        """Search logs using LogsQL query.

        Args:
            query: LogsQL query string (e.g., 'service.name:"backend" severity:ERROR')
            limit: Maximum number of log entries to return
            time_range: Time range filter (e.g., '1h', '10m', '1d')

        Returns:
            List of log entries
        """
        # Add time range to query if not already present
        if "_time:" not in query:
            query = f"_time:{time_range} {query}"

        url = f"{self.victorialogs_url}/select/logsql/query"
        params = {"query": query, "limit": limit}

        response = await self.http_client.post(url, params=params)
        response.raise_for_status()

        # VictoriaLogs returns JSON with hits array
        data = response.json()
        if isinstance(data, dict):
            return data.get("hits", [])
        return data if isinstance(data, list) else []

    async def logs_error_count(
        self, service: str | None = None, time_range: str = "1h"
    ) -> dict:
        """Count errors per service over a time window.

        Args:
            service: Optional service name filter
            time_range: Time range filter (e.g., '1h', '10m', '1d')

        Returns:
            Dictionary with error count
        """
        query = f"_time:{time_range} severity:ERROR"
        if service:
            query += f' service.name:"{service}"'

        url = f"{self.victorialogs_url}/select/logsql/query"
        params = {"query": query, "limit": 1000}

        response = await self.http_client.post(url, params=params)
        response.raise_for_status()

        data = response.json()
        hits = data.get("hits", []) if isinstance(data, dict) else data
        return {"error_count": len(hits), "service": service, "time_range": time_range}

    # VictoriaTraces API methods
    async def traces_list(
        self, service: str | None = None, limit: int = 10
    ) -> list[dict]:
        """List recent traces.

        Args:
            service: Optional service name filter
            limit: Maximum number of traces to return

        Returns:
            List of trace summaries
        """
        url = f"{self.victoriatraces_url}/select/jaeger/api/traces"
        params = {"limit": limit}
        if service:
            params["service"] = service

        response = await self.http_client.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        # Jaeger API returns {"data": [...]}
        return data.get("data", []) if isinstance(data, dict) else []

    async def traces_get(self, trace_id: str) -> dict:
        """Fetch a specific trace by ID.

        Args:
            trace_id: The trace ID to fetch

        Returns:
            Full trace data with spans
        """
        url = f"{self.victoriatraces_url}/select/jaeger/api/traces/{trace_id}"
        response = await self.http_client.get(url)
        response.raise_for_status()

        data = response.json()
        # Jaeger API returns {"data": [...]}
        traces_data = data.get("data", [])
        return traces_data[0] if traces_data else {}
