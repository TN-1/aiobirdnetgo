"""Tests for aiobirdnetgo data models."""

from __future__ import annotations

from aiobirdnetgo.models import (
    AudioLevelEvent,
    AudioSource,
    BirdImageInfo,
    DashboardKPIs,
    DatabaseHealth,
    Detection,
    HealthResponse,
    PingResponse,
    SpeciesDailySummary,
    SpeciesSummary,
    SystemInfo,
    WeatherInfo,
)


def test_ping_response() -> None:
    """Test PingResponse parsing."""
    resp = PingResponse.from_dict({"status": "ok"})
    assert resp.status == "ok"

    empty = PingResponse.from_dict({})
    assert empty.status == "unknown"


def test_health_response() -> None:
    """Test HealthResponse parsing."""
    data = {
        "status": "healthy",
        "version": "v1.2.3",
        "build_date": "2026-09-01",
        "timestamp": "2026-09-06T18:00:00Z",
        "environment": "production",
        "database": {"status": "connected", "error": None},
    }
    resp = HealthResponse.from_dict(data)
    assert resp.status == "healthy"
    assert resp.version == "v1.2.3"
    assert resp.build_date == "2026-09-01"
    assert resp.environment == "production"
    assert resp.database is not None
    assert resp.database.status == "connected"
    assert resp.database.error is None

    # Test missing database
    no_db = HealthResponse.from_dict({"status": "healthy"})
    assert no_db.database is None


def test_database_health() -> None:
    """Test DatabaseHealth parsing."""
    dh = DatabaseHealth.from_dict({"status": "error", "error": "db timeout"})
    assert dh.status == "error"
    assert dh.error == "db timeout"


def test_dashboard_kpis() -> None:
    """Test DashboardKPIs parsing."""
    data = {
        "lifetimeSpecies": 42,
        "todayDetections": 138,
        "bestDay": {"date": "2026-05-15", "count": 420},
        "detectionStreak": {"days": 17, "startDate": "2026-08-20"},
    }
    kpis = DashboardKPIs.from_dict(data)
    assert kpis.lifetime_species == 42
    assert kpis.today_detections == 138
    assert kpis.best_day.date == "2026-05-15"
    assert kpis.best_day.count == 420
    assert kpis.detection_streak.days == 17
    assert kpis.detection_streak.start_date == "2026-08-20"

    # Test snake_case fallback
    snake_data = {
        "lifetime_species": 10,
        "today_detections": 5,
        "best_day": {"date": "2026-01-01", "count": 10},
        "detection_streak": {"days": 1, "start_date": "2026-01-01"},
    }
    kpis_snake = DashboardKPIs.from_dict(snake_data)
    assert kpis_snake.lifetime_species == 10
    assert kpis_snake.today_detections == 5


def test_audio_source() -> None:
    """Test AudioSource parsing."""
    src = AudioSource.from_dict(
        {
            "id": "soundcard_0",
            "name": "USB Mic",
            "type": "audio_card",
            "state": "running",
        }
    )
    assert src.id == "soundcard_0"
    assert src.name == "USB Mic"
    assert src.type == "audio_card"
    assert src.state == "running"

    # Fallback to displayName
    src2 = AudioSource.from_dict({"id": "rtsp_1", "displayName": "Garden"})
    assert src2.name == "Garden"


def test_bird_image_info() -> None:
    """Test BirdImageInfo parsing."""
    img = BirdImageInfo.from_dict(
        {
            "url": "/api/v2/media/image/Turdus%20merula",
            "attribution": "Photo by John",
            "license": "CC BY-SA",
            "licenseUrl": "https://example.com/license",
        }
    )
    assert img.url == "/api/v2/media/image/Turdus%20merula"
    assert img.attribution == "Photo by John"
    assert img.license == "CC BY-SA"
    assert img.license_url == "https://example.com/license"


def test_weather_info() -> None:
    """Test WeatherInfo parsing."""
    w = WeatherInfo.from_dict(
        {
            "weatherIcon": "02d",
            "weatherMain": "Clouds",
            "description": "few clouds",
            "temperature": 18.5,
            "windSpeed": 3.2,
            "windGust": 5.1,
            "humidity": 60,
            "units": "metric",
            "moonPhase": 0.25,
            "moonPhaseName": "First Quarter",
            "moonIllumination": 0.5,
        }
    )
    assert w.weather_icon == "02d"
    assert w.weather_main == "Clouds"
    assert w.description == "few clouds"
    assert w.temperature == 18.5
    assert w.wind_speed == 3.2
    assert w.wind_gust == 5.1
    assert w.humidity == 60
    assert w.units == "metric"
    assert w.moon_phase == 0.25
    assert w.moon_phase_name == "First Quarter"
    assert w.moon_illumination == 0.5


def test_detection() -> None:
    """Test Detection parsing with all fields."""
    data = {
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
        "locked": True,
        "isNewSpecies": True,
        "birdImage": {
            "url": "/api/v2/media/image/Turdus%20merula",
        },
        "weather": {
            "temperature": 21.0,
        },
    }
    det = Detection.from_dict(data)
    assert det.id == 101
    assert det.date == "2026-09-06"
    assert det.time == "14:20:15"
    assert det.timestamp == "2026-09-06T14:20:15Z"
    assert det.source_id == "rtsp_cam1"
    assert det.source_name == "Garden RTSP Feed"
    assert det.scientific_name == "Turdus merula"
    assert det.common_name == "Eurasian Blackbird"
    assert det.confidence == 0.94
    assert det.species_code == "EABL1"
    assert det.clip_name == "blackbird_101.wav"
    assert det.model_type == "bird"
    assert det.verified == "correct"
    assert det.locked is True
    assert det.is_new_species is True
    assert det.bird_image is not None
    assert det.bird_image.url == "/api/v2/media/image/Turdus%20merula"
    assert det.weather is not None
    assert det.weather.temperature == 21.0

    # Test string source format (from MQTT/SSE variants)
    data_str_src = {
        "id": 102,
        "source": "Backyard Mic",
        "sourceId": "mic_1",
        "commonName": "Robin",
        "scientificName": "Erithacus rubecula",
        "confidence": 0.85,
    }
    det_str = Detection.from_dict(data_str_src)
    assert det_str.source_name == "Backyard Mic"
    assert det_str.source_id == "mic_1"

    # Test raw sourceName and sourceId keys when source is not present
    data_raw_src = {
        "id": 103,
        "sourceName": "Deck Camera",
        "sourceId": "deck_cam",
        "commonName": "Blue Tit",
        "scientificName": "Cyanistes caeruleus",
        "confidence": 0.91,
    }
    det_raw = Detection.from_dict(data_raw_src)
    assert det_raw.source_name == "Deck Camera"
    assert det_raw.source_id == "deck_cam"


def test_species_daily_summary() -> None:
    """Test SpeciesDailySummary parsing."""
    data = {
        "scientific_name": "Turdus merula",
        "common_name": "Eurasian Blackbird",
        "count": 28,
        "hourly_counts": [1, 2, 3],
        "high_confidence": True,
        "max_confidence": 0.96,
        "first_heard": "04:15:22",
        "latest_heard": "13:45:10",
        "thumbnail_url": "/thumb.jpg",
        "is_new_species": True,
    }
    summary = SpeciesDailySummary.from_dict(data)
    assert summary.scientific_name == "Turdus merula"
    assert summary.common_name == "Eurasian Blackbird"
    assert summary.count == 28
    assert summary.hourly_counts == [1, 2, 3]
    assert summary.high_confidence is True
    assert summary.max_confidence == 0.96
    assert summary.first_heard == "04:15:22"
    assert summary.latest_heard == "13:45:10"
    assert summary.thumbnail_url == "/thumb.jpg"
    assert summary.is_new_species is True


def test_species_summary() -> None:
    """Test SpeciesSummary parsing."""
    data = {
        "scientific_name": "Turdus merula",
        "common_name": "Eurasian Blackbird",
        "count": 150,
        "first_heard": "2026-05-01",
        "last_heard": "2026-09-06",
        "avg_confidence": 0.88,
        "max_confidence": 0.99,
        "thumbnail_url": "/thumb.jpg",
    }
    summary = SpeciesSummary.from_dict(data)
    assert summary.scientific_name == "Turdus merula"
    assert summary.count == 150
    assert summary.avg_confidence == 0.88
    assert summary.max_confidence == 0.99


def test_system_info() -> None:
    """Test SystemInfo parsing."""
    data = {
        "hostname": "birdnet-pi",
        "platform_version": "Debian 12",
        "kernel_version": "6.1.0",
        "uptime_seconds": 86400,
        "app_uptime_seconds": 43200,
        "num_cpu": 4,
        "os_display": "Linux",
        "architecture": "aarch64",
        "system_model": "Raspberry Pi 4",
        "time_zone": "UTC",
    }
    sysinfo = SystemInfo.from_dict(data)
    assert sysinfo.hostname == "birdnet-pi"
    assert sysinfo.uptime_seconds == 86400
    assert sysinfo.num_cpu == 4
    assert sysinfo.system_model == "Raspberry Pi 4"


def test_audio_level_event() -> None:
    """Test AudioLevelEvent parsing."""
    data = {
        "type": "audio-level",
        "levels": {
            "mic1": {
                "source": "mic1",
                "name": "Microphone",
                "level": 45.2,
                "clipping": True,
            }
        },
    }
    event = AudioLevelEvent.from_dict(data)
    assert "mic1" in event.levels
    assert event.levels["mic1"].source_id == "mic1"
    assert event.levels["mic1"].name == "Microphone"
    assert event.levels["mic1"].level == 45.2
    assert event.levels["mic1"].clipping is True
