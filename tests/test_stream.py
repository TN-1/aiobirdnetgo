"""Tests for the Server-Sent Events (SSE) streaming consumers."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
import pytest_asyncio
from aiohttp import web

from aiobirdnetgo import BirdNetGoClient
from aiobirdnetgo.exceptions import BirdNetGoAuthenticationError, BirdNetGoConnectionError
from aiobirdnetgo.stream import SSEMessage, _parse_sse_stream


def test_sse_message_json() -> None:
    """Test SSEMessage JSON parsing."""
    msg = SSEMessage(event="detection", data='{"id": 1, "commonName": "Robin"}', event_id="10")
    assert msg.event == "detection"
    assert msg.event_id == "10"
    assert msg.json() == {"id": 1, "commonName": "Robin"}

    invalid = SSEMessage(event="detection", data="invalid json")
    assert invalid.json() == {}


class MockContentStream:
    """Mock aiohttp response content stream for testing _parse_sse_stream directly."""

    def __init__(self, lines: list[bytes]) -> None:
        self._lines = lines

    def __aiter__(self) -> MockContentStream:
        self._iter = iter(self._lines)
        return self

    async def __anext__(self) -> bytes:
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration from None


class MockResponse:
    """Mock ClientResponse."""

    def __init__(self, lines: list[bytes]) -> None:
        self.content = MockContentStream(lines)


@pytest.mark.asyncio
async def test_parse_sse_stream_parsing_details() -> None:
    """Test line parsing in _parse_sse_stream with comments, IDs, and final flush."""
    lines = [
        b": keepalive comment\n",
        b"id: msg_1\n",
        b"event: custom\n",
        b'data: {"test": 1}\n',
        b"\n",
        b'data: {"trailing": true}\n',  # No trailing newline to test stream end flush
    ]
    resp = MockResponse(lines)
    messages = [msg async for msg in _parse_sse_stream(resp)]  # type: ignore[arg-type]

    assert len(messages) == 2
    assert messages[0].event == "custom"
    assert messages[0].event_id == "msg_1"
    assert messages[0].json() == {"test": 1}

    assert messages[1].event == "message"
    assert messages[1].json() == {"trailing": True}


@pytest.mark.asyncio
async def test_detection_stream(client: BirdNetGoClient) -> None:
    """Test streaming detections from mock server."""
    stream = client.stream_detections(read_timeout=5.0)

    detections = []
    async for detection in stream:
        detections.append(detection)
        stream.stop()

    assert len(detections) == 1
    assert detections[0].id == 101
    assert detections[0].common_name == "Eurasian Blackbird"


@pytest.mark.asyncio
async def test_audio_level_stream(client: BirdNetGoClient) -> None:
    """Test streaming audio levels from mock server."""
    stream = client.stream_audio_levels(read_timeout=5.0)

    events = []
    async for event in stream:
        events.append(event)
        stream.stop()

    assert len(events) == 1
    assert "source_1" in events[0].levels
    assert events[0].levels["source_1"].level == 42.5


@pytest.mark.asyncio
async def test_stream_connection_error_no_reconnect() -> None:
    """Test stream raises connection error when auto_reconnect=False."""
    async with BirdNetGoClient(host="127.0.0.1", port=59999, request_timeout=1.0) as dead_client:
        stream = dead_client.stream_detections(auto_reconnect=False, read_timeout=1.0)
        with pytest.raises(BirdNetGoConnectionError):
            async for _ in stream:
                pass


@pytest.mark.asyncio
async def test_stream_cancellation(client: BirdNetGoClient) -> None:
    """Test stream cancellation behaves cleanly."""
    stream = client.stream_detections(read_timeout=5.0)

    async def consume() -> None:
        async for _ in stream:
            await asyncio.sleep(10.0)

    task = asyncio.create_task(consume())
    await asyncio.sleep(0.05)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task


@pytest_asyncio.fixture
async def sse_error_server() -> Any:
    """Run server returning error statuses on SSE endpoints."""
    app = web.Application()

    async def handle_401(request: web.Request) -> web.Response:
        return web.Response(status=401, text="Unauthorized")

    async def handle_503(request: web.Request) -> web.Response:
        return web.Response(status=503, text="Service Unavailable")

    app.router.add_get("/api/v2/detections/stream", handle_401)
    app.router.add_get("/api/v2/soundlevels/stream", handle_503)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]

    yield f"127.0.0.1:{port}"
    await runner.cleanup()


@pytest.mark.asyncio
async def test_stream_auth_and_status_errors(sse_error_server: str) -> None:
    """Test stream error handling for 401 and 503 statuses."""
    host, port = sse_error_server.split(":")
    async with BirdNetGoClient(host=host, port=int(port), request_timeout=1.0) as err_client:
        # Detection stream 401
        det_stream = err_client.stream_detections(auto_reconnect=False, read_timeout=1.0)
        with pytest.raises(BirdNetGoAuthenticationError):
            async for _ in det_stream:
                pass

        # Soundlevel stream 503
        sound_stream = err_client.stream_audio_levels(auto_reconnect=False, read_timeout=1.0)
        with pytest.raises(BirdNetGoConnectionError):
            async for _ in sound_stream:
                pass
