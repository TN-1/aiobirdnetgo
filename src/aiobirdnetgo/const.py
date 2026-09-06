"""Constants for the aiobirdnetgo library."""

from __future__ import annotations

from typing import Final

# Network defaults
DEFAULT_PORT: Final[int] = 8080
DEFAULT_TIMEOUT: Final[float] = 10.0
DEFAULT_SSE_TIMEOUT: Final[float] = 300.0
DEFAULT_RECONNECT_INTERVAL: Final[float] = 5.0
MAX_RECONNECT_INTERVAL: Final[float] = 60.0

# API Version & Base Paths
API_V2_PREFIX: Final[str] = "/api/v2"

# Endpoints
ENDPOINT_PING: Final[str] = f"{API_V2_PREFIX}/ping"
ENDPOINT_HEALTH: Final[str] = f"{API_V2_PREFIX}/health"
ENDPOINT_KPIS: Final[str] = f"{API_V2_PREFIX}/dashboard/kpis"
ENDPOINT_AUDIO_SOURCES: Final[str] = f"{API_V2_PREFIX}/system/audio/sources"
ENDPOINT_STREAM_SOURCES: Final[str] = f"{API_V2_PREFIX}/streams/sources"
ENDPOINT_DETECTIONS: Final[str] = f"{API_V2_PREFIX}/detections"
ENDPOINT_RECENT_DETECTIONS: Final[str] = f"{API_V2_PREFIX}/detections/recent"
ENDPOINT_DETECTION_STREAM: Final[str] = f"{API_V2_PREFIX}/detections/stream"
ENDPOINT_SOUNDLEVEL_STREAM: Final[str] = f"{API_V2_PREFIX}/soundlevels/stream"
ENDPOINT_DAILY_SPECIES: Final[str] = f"{API_V2_PREFIX}/analytics/species/daily"
ENDPOINT_SPECIES_SUMMARY: Final[str] = f"{API_V2_PREFIX}/analytics/species/summary"
ENDPOINT_SYSTEM_INFO: Final[str] = f"{API_V2_PREFIX}/system/info"
ENDPOINT_CONTROL_RESTART: Final[str] = f"{API_V2_PREFIX}/control/restart"
ENDPOINT_CONTROL_RELOAD: Final[str] = f"{API_V2_PREFIX}/control/reload"

# SSE Event Types
SSE_EVENT_CONNECTED: Final[str] = "connected"
SSE_EVENT_DETECTION: Final[str] = "detection"
SSE_EVENT_HEARTBEAT: Final[str] = "heartbeat"
SSE_EVENT_PENDING: Final[str] = "pending"
SSE_EVENT_AUDIO_LEVEL: Final[str] = "audio-level"
