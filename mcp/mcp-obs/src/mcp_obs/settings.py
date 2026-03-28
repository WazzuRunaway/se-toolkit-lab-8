"""Settings for the observability MCP server."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ObsSettings:
    victorialogs_url: str
    victoriatraces_url: str

    @classmethod
    def from_env(cls) -> "ObsSettings":
        return cls(
            victorialogs_url=os.environ.get(
                "NANOBOT_VICTORIALOGS_URL", "http://localhost:9428"
            ),
            victoriatraces_url=os.environ.get(
                "NANOBOT_VICTORIATRACES_URL", "http://localhost:10428"
            ),
        )


def resolve_settings() -> ObsSettings:
    return ObsSettings.from_env()
