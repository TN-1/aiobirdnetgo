"""Tests for the BirdNetGoClient."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
import pytest_asyncio
from aiohttp import web

from aiobirdnetgo import BirdNetGoClient
from aiobirdnetgo.exceptions import (
    BirdNetGoAuthenticationError,
    BirdNetGoConnectionError,
    BirdNetGoNotFoundError,
    BirdNetGoResponseError,
)


def test_client_init_properties() -> None:
    """Test client initialization and property getters."""
    client = BirdNetGoClient(host="192.168.1.100", port=8080, use_ssl=False)
    assert client.host == "192.168.1.100"
    assert client.port == 8080
    assert client.use_ssl is False
    assert client.base_url == "http://192.168.1.100:8080"
    assert client.get_endpoint_url("/api/v2/ping") == "http://192.168.1.100:8080/api/v2/ping"
    assert client.get_endpoint_url("api/v2/ping") == "http://192.168.1.100:8080/api/v2/ping"

    # Test full URL with https
    https_client = BirdNetGoClient(host="https://birdnet.local:8443/custom")
    assert https_client.host == "birdnet.local"
    assert https_client.port == 8443
    assert https_client.use_ssl is True
    assert https_client.base_url == "https://birdnet.local:8443"

    # Test explicit base_path
    base_path_client = BirdNetGoClient(
        host="birdnet.local", port=8443, use_ssl=True, base_path="/custom"
    )
    assert base_path_client.base_url == "https://birdnet.local:8443/custom"

    # Test Auth Headers
    api_key_client = BirdNetGoClient(host="localhost", api_key="secret-token")
    headers = api_key_client.get_headers()
    assert headers["Authorization"] == "Bearer secret-token"

    basic_auth_client = BirdNetGoClient(host="localhost", username="admin", password="password123")
    bheaders = basic_auth_client.get_headers()
    assert bheaders["Authorization"].startswith("Basic ")


@pytest.mark.asyncio
async def test_ping(client: BirdNetGoClient) -> None:
    """Test ping() helper."""
    assert await client.ping() is True


@pytest.mark.asyncio
async def test_get_ping(client: BirdNetGoClient) -> None:
    """Test get_ping()."""
    resp = await client.get_ping()
    assert resp.status == "ok"


@pytest.mark.asyncio
async def test_get_health(client: BirdNetGoClient) -> None:
    """Test get_health()."""
    health = await client.get_health()
    assert health.status == "healthy"
    assert health.version == "v1.2.3"
    assert health.database is not None
    assert health.database.status == "connected"


@pytest.mark.asyncio
async def test_get_kpis(client: BirdNetGoClient) -> None:
    """Test get_kpis()."""
    kpis = await client.get_kpis()
    assert kpis.lifetime_species == 42
    assert kpis.today_detections == 138
    assert kpis.best_day.count == 420
    assert kpis.detection_streak.days == 17


@pytest.mark.asyncio
async def test_get_kpis_malformed(client: BirdNetGoClient) -> None:
    """Test get_kpis() with malformed responses."""
    # Missing required keys
    with patch.object(client, "_request", return_value={"message": "ok"}):
        with pytest.raises(BirdNetGoResponseError, match="Malformed KPI response"):
            await client.get_kpis()

    # Non-dictionary response
    with patch.object(client, "_request", return_value=["not", "a", "dict"]):
        with pytest.raises(BirdNetGoResponseError, match="Expected JSON object"):
            await client.get_kpis()


@pytest.mark.asyncio
async def test_get_audio_sources(client: BirdNetGoClient) -> None:
    """Test get_audio_sources()."""
    sources = await client.get_audio_sources()
    assert len(sources) == 2
    assert sources[0].id == "soundcard_default"
    assert sources[0].name == "USB Audio Device"
    assert sources[1].id == "rtsp_cam1"

    # Test stream sources only
    stream_sources = await client.get_audio_sources(streams_only=True)
    assert len(stream_sources) == 2


@pytest.mark.asyncio
async def test_get_recent_detections(client: BirdNetGoClient) -> None:
    """Test get_recent_detections()."""
    detections = await client.get_recent_detections(limit=10)
    assert len(detections) == 1
    det = detections[0]
    assert det.id == 101
    assert det.common_name == "Eurasian Blackbird"
    assert det.confidence == 0.94
    assert det.is_new_species is True


@pytest.mark.asyncio
async def test_get_detections(client: BirdNetGoClient) -> None:
    """Test get_detections() with filter parameters."""
    detections = await client.get_detections(date="2026-09-06", min_confidence=0.8)
    assert len(detections) == 1
    assert detections[0].id == 101


@pytest.mark.asyncio
async def test_get_single_detection(client: BirdNetGoClient) -> None:
    """Test get_detection()."""
    det = await client.get_detection(101)
    assert det.id == 101
    assert det.common_name == "Eurasian Blackbird"

    with pytest.raises(BirdNetGoNotFoundError):
        await client.get_detection(999)


@pytest.mark.asyncio
async def test_get_daily_species_summary(client: BirdNetGoClient) -> None:
    """Test get_daily_species_summary()."""
    summaries = await client.get_daily_species_summary()
    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.scientific_name == "Turdus merula"
    assert summary.count == 28


@pytest.mark.asyncio
async def test_get_species_summary(client: BirdNetGoClient) -> None:
    """Test get_species_summary()."""
    summaries = await client.get_species_summary()
    assert len(summaries) == 1
    assert summaries[0].count == 150


@pytest.mark.asyncio
async def test_get_system_info(client: BirdNetGoClient) -> None:
    """Test get_system_info()."""
    sysinfo = await client.get_system_info()
    assert sysinfo.hostname == "birdnet-pi"
    assert sysinfo.num_cpu == 4


@pytest.mark.asyncio
async def test_control_operations(client: BirdNetGoClient) -> None:
    """Test restart_analysis and reload_model."""
    assert await client.restart_analysis() is True
    assert await client.reload_model() is True


def test_url_helpers(client: BirdNetGoClient) -> None:
    """Test URL construction helpers."""
    assert client.get_audio_clip_url(101).endswith("/api/v2/audio/101")
    assert client.get_spectrogram_url(101).endswith("/api/v2/spectrogram/101")
    assert client.get_species_image_url("Turdus merula").endswith(
        "/api/v2/media/image/Turdus%20merula"
    )


@pytest_asyncio.fixture
async def error_server() -> Any:
    """Run server that returns error statuses."""
    app = web.Application()

    async def handle_401(request: web.Request) -> web.Response:
        return web.Response(status=401, text="Unauthorized")

    async def handle_500(request: web.Request) -> web.Response:
        return web.Response(status=500, text="Internal Error")

    app.router.add_get("/api/v2/health", handle_500)
    app.router.add_get("/api/v2/ping", handle_401)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]

    yield f"127.0.0.1:{port}"
    await runner.cleanup()


@pytest.mark.asyncio
async def test_error_handling(error_server: str) -> None:
    """Test error handling on bad response codes."""
    host, port = error_server.split(":")
    async with BirdNetGoClient(host=host, port=int(port), request_timeout=2.0) as err_client:
        # 401 raises BirdNetGoAuthenticationError on direct request
        with pytest.raises(BirdNetGoAuthenticationError):
            await err_client.get_ping()

        # ping() catches it and returns False
        assert await err_client.ping() is False

        # 500 raises BirdNetGoResponseError
        with pytest.raises(BirdNetGoResponseError) as exc_info:
            await err_client.get_health()
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_connection_error() -> None:
    """Test unreachable host raises BirdNetGoConnectionError."""
    # Use a non-listening local port
    async with BirdNetGoClient(host="127.0.0.1", port=59999, request_timeout=1.0) as dead_client:
        assert await dead_client.ping() is False
        with pytest.raises(BirdNetGoConnectionError):
            await dead_client.get_health()


@pytest_asyncio.fixture
async def malformed_server() -> Any:
    """Run server returning unexpected non-dict/non-list payloads."""
    app = web.Application()

    async def handle_empty_text(request: web.Request) -> web.Response:
        return web.Response(status=200, text="plain string", content_type="text/plain")

    app.router.add_get("/api/v2/system/audio/sources", handle_empty_text)
    app.router.add_get("/api/v2/detections/recent", handle_empty_text)
    app.router.add_get("/api/v2/detections", handle_empty_text)
    app.router.add_get("/api/v2/analytics/species/daily", handle_empty_text)
    app.router.add_get("/api/v2/analytics/species/summary", handle_empty_text)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]

    yield f"127.0.0.1:{port}"
    await runner.cleanup()


@pytest.mark.asyncio
async def test_malformed_fallbacks(malformed_server: str) -> None:
    """Test client returns empty collections when API returns non-JSON/unexpected shapes."""
    host, port = malformed_server.split(":")
    async with BirdNetGoClient(host=host, port=int(port), request_timeout=2.0) as bad_client:
        assert await bad_client.get_audio_sources() == []
        assert await bad_client.get_recent_detections() == []
        assert await bad_client.get_detections() == []
        assert await bad_client.get_daily_species_summary() == []
        assert await bad_client.get_species_summary() == []
