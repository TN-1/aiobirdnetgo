"""Asynchronous Python client for BirdNET-Go."""

from __future__ import annotations

from .client import BirdNetGoClient
from .const import (
    DEFAULT_PORT,
    DEFAULT_RECONNECT_INTERVAL,
    DEFAULT_SSE_TIMEOUT,
    DEFAULT_TIMEOUT,
    MAX_RECONNECT_INTERVAL,
    SSE_EVENT_AUDIO_LEVEL,
    SSE_EVENT_CONNECTED,
    SSE_EVENT_DETECTION,
    SSE_EVENT_HEARTBEAT,
    SSE_EVENT_PENDING,
)
from .exceptions import (
    BirdNetGoAuthenticationError,
    BirdNetGoConnectionError,
    BirdNetGoError,
    BirdNetGoNotFoundError,
    BirdNetGoResponseError,
    BirdNetGoTimeoutError,
)
from .models import (
    AudioLevelEvent,
    AudioLevelItem,
    AudioSource,
    BestDayInfo,
    BirdImageInfo,
    DashboardKPIs,
    DatabaseHealth,
    Detection,
    HealthResponse,
    PingResponse,
    SpeciesDailySummary,
    SpeciesSummary,
    StreakInfo,
    SystemInfo,
    WeatherInfo,
)
from .stream import AudioLevelStream, DetectionStream, SSEMessage

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_PORT",
    "DEFAULT_RECONNECT_INTERVAL",
    "DEFAULT_SSE_TIMEOUT",
    "DEFAULT_TIMEOUT",
    "MAX_RECONNECT_INTERVAL",
    "SSE_EVENT_AUDIO_LEVEL",
    "SSE_EVENT_CONNECTED",
    "SSE_EVENT_DETECTION",
    "SSE_EVENT_HEARTBEAT",
    "SSE_EVENT_PENDING",
    "AudioLevelEvent",
    "AudioLevelItem",
    "AudioLevelStream",
    "AudioSource",
    "BestDayInfo",
    "BirdImageInfo",
    "BirdNetGoAuthenticationError",
    "BirdNetGoClient",
    "BirdNetGoConnectionError",
    "BirdNetGoError",
    "BirdNetGoNotFoundError",
    "BirdNetGoResponseError",
    "BirdNetGoTimeoutError",
    "DashboardKPIs",
    "DatabaseHealth",
    "Detection",
    "DetectionStream",
    "HealthResponse",
    "PingResponse",
    "SSEMessage",
    "SpeciesDailySummary",
    "SpeciesSummary",
    "StreakInfo",
    "SystemInfo",
    "WeatherInfo",
]
