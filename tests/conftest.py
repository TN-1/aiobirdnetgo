"""Fixtures and test setup for aiobirdnetgo tests."""

from __future__ import annotations

import json
from typing import Any

import pytest
import pytest_asyncio
from aiohttp import web

from aiobirdnetgo import BirdNetGoClient


@pytest.fixture
def ping_response_data() -> dict[str, Any]:
    """Sample ping response."""
    return {"status": "ok"}


@pytest.fixture
def health_response_data() -> dict[str, Any]:
    """Sample health response."""
    return {
        "status": "healthy",
        "version": "v1.2.3",
        "build_date": "2026-09-01",
        "timestamp": "2026-09-06T18:00:00Z",
        "environment": "production",
        "database": {
            "status": "connected",
        },
    }


@pytest.fixture
def kpis_response_data() -> dict[str, Any]:
    """Sample dashboard KPIs response."""
    return {
        "lifetimeSpecies": 42,
        "todayDetections": 138,
        "bestDay": {
            "date": "2026-05-15",
            "count": 420,
        },
        "detectionStreak": {
            "days": 17,
            "startDate": "2026-08-20",
        },
    }


@pytest.fixture
def audio_sources_response_data() -> dict[str, Any]:
    """Sample audio sources response."""
    return {
        "sources": [
            {
                "id": "soundcard_default",
                "name": "USB Audio Device",
                "type": "audio_card",
                "state": "running",
            },
            {
                "id": "rtsp_cam1",
                "name": "Garden RTSP Feed",
                "type": "rtsp",
                "state": "running",
            },
        ]
    }


@pytest.fixture
def recent_detections_response_data() -> list[dict[str, Any]]:
    """Sample recent detections list."""
    return [
        {
            "id": 101,
            "date": "2026-09-06",
            "time": "14:20:15",
            "timestamp": "2026-09-06T14:20:15Z",
            "source": {
                "id": "rtsp_cam1",
                "displayName": "Garden RTSP Feed",
                "type": "rtsp",
            },
            "scientificName": "Turdus merula",
            "commonName": "Eurasian Blackbird",
            "confidence": 0.94,
            "speciesCode": "EABL1",
            "clipName": "blackbird_101.wav",
            "modelType": "bird",
            "verified": "correct",
            "locked": False,
            "isNewSpecies": True,
            "birdImage": {
                "url": "/api/v2/media/image/Turdus%20merula",
                "attribution": "Photo by Jane Doe",
                "license": "CC BY-SA 4.0",
                "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
            },
            "weather": {
                "weatherIcon": "01d",
                "weatherMain": "Clear",
                "temperature": 21.5,
                "humidity": 45,
            },
        }
    ]


@pytest.fixture
def daily_species_summary_response_data() -> list[dict[str, Any]]:
    """Sample daily species summary."""
    return [
        {
            "scientific_name": "Turdus merula",
            "common_name": "Eurasian Blackbird",
            "count": 28,
            "hourly_counts": [
                0,
                0,
                0,
                0,
                1,
                5,
                8,
                4,
                3,
                2,
                1,
                1,
                1,
                2,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
            "high_confidence": True,
            "max_confidence": 0.96,
            "first_heard": "04:15:22",
            "latest_heard": "13:45:10",
            "thumbnail_url": "/api/v2/media/image/Turdus%20merula",
            "is_new_species": False,
        }
    ]


@pytest.fixture
def system_info_response_data() -> dict[str, Any]:
    """Sample system info response."""
    return {
        "hostname": "birdnet-pi",
        "platform_version": "Debian 12",
        "kernel_version": "6.1.0-rpi",
        "uptime_seconds": 864000,
        "app_uptime_seconds": 432000,
        "num_cpu": 4,
        "os_display": "Linux",
        "architecture": "aarch64",
        "system_model": "Raspberry Pi 4 Model B",
        "time_zone": "Europe/London",
        "environment": "production",
    }


@pytest_asyncio.fixture
async def mock_birdnet_server(
    ping_response_data: dict[str, Any],
    health_response_data: dict[str, Any],
    kpis_response_data: dict[str, Any],
    audio_sources_response_data: dict[str, Any],
    recent_detections_response_data: list[dict[str, Any]],
    daily_species_summary_response_data: list[dict[str, Any]],
    system_info_response_data: dict[str, Any],
) -> Any:
    """Run an in-process aiohttp test server mocking BirdNET-Go API v2."""
    app = web.Application()

    async def handle_ping(request: web.Request) -> web.Response:
        return web.json_response(ping_response_data)

    async def handle_health(request: web.Request) -> web.Response:
        return web.json_response(health_response_data)

    async def handle_kpis(request: web.Request) -> web.Response:
        return web.json_response(kpis_response_data)

    async def handle_audio_sources(request: web.Request) -> web.Response:
        return web.json_response(audio_sources_response_data)

    async def handle_recent_detections(request: web.Request) -> web.Response:
        return web.json_response(recent_detections_response_data)

    async def handle_detections(request: web.Request) -> web.Response:
        return web.json_response(recent_detections_response_data)

    async def handle_single_detection(request: web.Request) -> web.Response:
        det_id = request.match_info.get("id")
        if det_id == "101":
            return web.json_response(recent_detections_response_data[0])
        return web.json_response({"error": "Detection not found"}, status=404)

    async def handle_daily_species(request: web.Request) -> web.Response:
        return web.json_response(daily_species_summary_response_data)

    async def handle_species_summary(request: web.Request) -> web.Response:
        return web.json_response(
            [
                {
                    "scientific_name": "Turdus merula",
                    "common_name": "Eurasian Blackbird",
                    "count": 150,
                    "first_heard": "2026-05-01",
                    "last_heard": "2026-09-06",
                    "avg_confidence": 0.88,
                    "max_confidence": 0.99,
                    "thumbnail_url": "/api/v2/media/image/Turdus%20merula",
                }
            ]
        )

    async def handle_system_info(request: web.Request) -> web.Response:
        return web.json_response(system_info_response_data)

    async def handle_restart(request: web.Request) -> web.Response:
        return web.json_response({"status": "restarting"})

    async def handle_reload(request: web.Request) -> web.Response:
        return web.json_response({"status": "reloaded"})

    async def handle_detection_stream(request: web.Request) -> web.StreamResponse:
        response = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
        await response.prepare(request)

        # 1. Connected event
        await response.write(b'event: connected\ndata: {"message": "Connected to stream"}\n\n')

        # 2. Heartbeat event
        await response.write(b'event: heartbeat\ndata: {"timestamp": 1700000000, "clients": 1}\n\n')

        # 3. Detection event
        detection_payload = json.dumps(recent_detections_response_data[0])
        await response.write(f"event: detection\ndata: {detection_payload}\n\n".encode())

        return response

    async def handle_soundlevel_stream(request: web.Request) -> web.StreamResponse:
        response = web.StreamResponse(
            status=200,
            headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
            },
        )
        await response.prepare(request)
        level_payload = json.dumps(
            {
                "type": "audio-level",
                "levels": {
                    "source_1": {
                        "source": "source_1",
                        "name": "Microphone",
                        "level": 42.5,
                        "clipping": False,
                    }
                },
            }
        )
        await response.write(f"event: audio-level\ndata: {level_payload}\n\n".encode())
        return response

    # Register routes
    app.router.add_get("/api/v2/ping", handle_ping)
    app.router.add_get("/api/v2/health", handle_health)
    app.router.add_get("/api/v2/dashboard/kpis", handle_kpis)
    app.router.add_get("/api/v2/system/audio/sources", handle_audio_sources)
    app.router.add_get("/api/v2/streams/sources", handle_audio_sources)
    app.router.add_get("/api/v2/detections/recent", handle_recent_detections)
    app.router.add_get("/api/v2/detections", handle_detections)
    app.router.add_get("/api/v2/detections/{id}", handle_single_detection)
    app.router.add_get("/api/v2/analytics/species/daily", handle_daily_species)
    app.router.add_get("/api/v2/analytics/species/summary", handle_species_summary)
    app.router.add_get("/api/v2/system/info", handle_system_info)
    app.router.add_post("/api/v2/control/restart", handle_restart)
    app.router.add_post("/api/v2/control/reload", handle_reload)
    app.router.add_get("/api/v2/detections/stream", handle_detection_stream)
    app.router.add_get("/api/v2/soundlevels/stream", handle_soundlevel_stream)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()

    # Get dynamic port
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[union-attr]

    yield f"127.0.0.1:{port}"

    await runner.cleanup()


@pytest_asyncio.fixture
async def client(mock_birdnet_server: str) -> Any:
    """Create a test BirdNetGoClient connected to the mock server."""
    host, port = mock_birdnet_server.split(":")
    async with BirdNetGoClient(host=host, port=int(port)) as birdnet_client:
        yield birdnet_client
