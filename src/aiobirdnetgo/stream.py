"""Server-Sent Events (SSE) stream consumers for aiobirdnetgo."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout

from .const import (
    DEFAULT_RECONNECT_INTERVAL,
    DEFAULT_SSE_TIMEOUT,
    MAX_RECONNECT_INTERVAL,
    SSE_EVENT_AUDIO_LEVEL,
    SSE_EVENT_CONNECTED,
    SSE_EVENT_DETECTION,
    SSE_EVENT_HEARTBEAT,
)
from .exceptions import BirdNetGoAuthenticationError, BirdNetGoConnectionError
from .models import AudioLevelEvent, Detection

if TYPE_CHECKING:
    from .client import BirdNetGoClient

_LOGGER = logging.getLogger(__package__)


class SSEMessage:
    """Represents a raw Server-Sent Event message."""

    def __init__(self, event: str = "message", data: str = "", event_id: str | None = None) -> None:
        """Initialize SSE message."""
        self.event = event
        self.data = data
        self.event_id = event_id

    def json(self) -> dict[str, Any]:
        """Parse the event data as JSON."""
        try:
            return json.loads(self.data)  # type: ignore[no-any-return]
        except (json.JSONDecodeError, TypeError):
            return {}


async def _parse_sse_stream(
    response: ClientResponse,
) -> AsyncIterator[SSEMessage]:
    """Parse raw SSE stream lines from a ClientResponse into SSEMessages."""
    current_event = "message"
    data_lines: list[str] = []
    current_id: str | None = None

    async for raw_line in response.content:
        line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")

        # Comment or keepalive line
        if line.startswith(":"):
            continue

        # Blank line triggers event dispatch
        if not line:
            if data_lines:
                yield SSEMessage(
                    event=current_event,
                    data="\n".join(data_lines),
                    event_id=current_id,
                )
                current_event = "message"
                data_lines = []
            continue

        if line.startswith("event:"):
            current_event = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
        elif line.startswith("id:"):
            current_id = line[3:].strip()

    # Flush any remaining message at end of stream
    if data_lines:
        yield SSEMessage(
            event=current_event,
            data="\n".join(data_lines),
            event_id=current_id,
        )


class DetectionStream:
    """Consumer for the BirdNET-Go real-time detection SSE stream."""

    def __init__(
        self,
        client: BirdNetGoClient,
        auto_reconnect: bool = True,
        reconnect_interval: float = DEFAULT_RECONNECT_INTERVAL,
        max_reconnect_interval: float = MAX_RECONNECT_INTERVAL,
        read_timeout: float = DEFAULT_SSE_TIMEOUT,
    ) -> None:
        """Initialize detection stream consumer."""
        self._client = client
        self._auto_reconnect = auto_reconnect
        self._reconnect_interval = reconnect_interval
        self._max_reconnect_interval = max_reconnect_interval
        self._read_timeout = read_timeout
        self._stop_event = asyncio.Event()
        self._session: ClientSession | None = None

    @property
    def stopped(self) -> bool:
        """Return whether stream is stopped."""
        return self._stop_event.is_set()

    def stop(self) -> None:
        """Stop listening to the stream."""
        self._stop_event.set()

    async def __aiter__(self) -> AsyncIterator[Detection]:
        """Iterate over incoming detection events asynchronously."""
        current_delay = self._reconnect_interval

        while not self.stopped:
            try:
                url = self._client.get_endpoint_url(self._client.detection_stream_endpoint)
                headers = self._client.get_headers()

                session = self._client.session
                async with session.get(
                    url,
                    headers=headers,
                    timeout=ClientTimeout(total=self._read_timeout),
                ) as response:
                    if response.status in (401, 403):
                        raise BirdNetGoAuthenticationError(
                            f"Authentication failed with status {response.status}"
                        )
                    if response.status != 200:
                        raise BirdNetGoConnectionError(
                            f"Unexpected status from SSE endpoint: {response.status}"
                        )

                    # Reset backoff upon successful connection
                    current_delay = self._reconnect_interval

                    async for message in _parse_sse_stream(response):
                        if message.event == SSE_EVENT_DETECTION:
                            payload = message.json()
                            if payload:
                                yield Detection.from_dict(payload)
                        elif message.event == SSE_EVENT_CONNECTED:
                            _LOGGER.debug(
                                "Connected to BirdNET-Go detection stream: %s", message.data
                            )
                        elif message.event == SSE_EVENT_HEARTBEAT:
                            _LOGGER.debug("Received detection stream heartbeat")

            except asyncio.CancelledError:
                self.stop()
                raise
            except BirdNetGoAuthenticationError:
                _LOGGER.error("Authentication error on detection stream; stopping reconnect")
                raise
            except (TimeoutError, ClientError, BirdNetGoConnectionError) as err:
                if not self._auto_reconnect:
                    raise BirdNetGoConnectionError(f"Detection stream disconnected: {err}") from err

                _LOGGER.warning(
                    "Detection stream disconnected (%s). Reconnecting in %.1fs...",
                    err,
                    current_delay,
                )
                await asyncio.sleep(current_delay)
                current_delay = min(current_delay * 1.5, self._max_reconnect_interval)
            except Exception as err:
                _LOGGER.exception("Unexpected error in detection stream: %s", err)
                if not self._auto_reconnect:
                    raise
                await asyncio.sleep(current_delay)


class AudioLevelStream:
    """Consumer for the BirdNET-Go real-time sound level SSE stream."""

    def __init__(
        self,
        client: BirdNetGoClient,
        auto_reconnect: bool = True,
        reconnect_interval: float = DEFAULT_RECONNECT_INTERVAL,
        max_reconnect_interval: float = MAX_RECONNECT_INTERVAL,
        read_timeout: float = DEFAULT_SSE_TIMEOUT,
    ) -> None:
        """Initialize audio level stream consumer."""
        self._client = client
        self._auto_reconnect = auto_reconnect
        self._reconnect_interval = reconnect_interval
        self._max_reconnect_interval = max_reconnect_interval
        self._read_timeout = read_timeout
        self._stop_event = asyncio.Event()

    @property
    def stopped(self) -> bool:
        """Return whether stream is stopped."""
        return self._stop_event.is_set()

    def stop(self) -> None:
        """Stop listening to the audio level stream."""
        self._stop_event.set()

    async def __aiter__(self) -> AsyncIterator[AudioLevelEvent]:
        """Iterate over incoming audio level events asynchronously."""
        current_delay = self._reconnect_interval

        while not self.stopped:
            try:
                url = self._client.get_endpoint_url(self._client.soundlevel_stream_endpoint)
                headers = self._client.get_headers()

                session = self._client.session
                async with session.get(
                    url,
                    headers=headers,
                    timeout=ClientTimeout(total=self._read_timeout),
                ) as response:
                    if response.status in (401, 403):
                        raise BirdNetGoAuthenticationError(
                            f"Authentication failed with status {response.status}"
                        )
                    if response.status != 200:
                        raise BirdNetGoConnectionError(
                            f"Unexpected status from soundlevel stream: {response.status}"
                        )

                    current_delay = self._reconnect_interval

                    async for message in _parse_sse_stream(response):
                        if message.event in (SSE_EVENT_AUDIO_LEVEL, "message"):
                            payload = message.json()
                            if payload:
                                yield AudioLevelEvent.from_dict(payload)

            except asyncio.CancelledError:
                self.stop()
                raise
            except BirdNetGoAuthenticationError:
                _LOGGER.error("Authentication error on soundlevel stream; stopping reconnect")
                raise
            except (TimeoutError, ClientError, BirdNetGoConnectionError) as err:
                if not self._auto_reconnect:
                    raise BirdNetGoConnectionError(
                        f"Soundlevel stream disconnected: {err}"
                    ) from err

                _LOGGER.warning(
                    "Soundlevel stream disconnected (%s). Reconnecting in %.1fs...",
                    err,
                    current_delay,
                )
                await asyncio.sleep(current_delay)
                current_delay = min(current_delay * 1.5, self._max_reconnect_interval)
            except Exception as err:
                _LOGGER.exception("Unexpected error in soundlevel stream: %s", err)
                if not self._auto_reconnect:
                    raise
                await asyncio.sleep(current_delay)
