"""Data models for the aiobirdnetgo library."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PingResponse:
    """Response model for the /api/v2/ping endpoint."""

    status: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PingResponse:
        """Create a PingResponse from API dictionary."""
        return cls(status=str(data.get("status", "unknown")))


@dataclass(frozen=True)
class DatabaseHealth:
    """Database health status model."""

    status: str
    error: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DatabaseHealth:
        """Create DatabaseHealth from API dictionary."""
        return cls(
            status=str(data.get("status", "unknown")),
            error=data.get("error"),
        )


@dataclass(frozen=True)
class HealthResponse:
    """Response model for the /api/v2/health endpoint."""

    status: str
    version: str
    build_date: str
    timestamp: str
    environment: str
    database: DatabaseHealth | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HealthResponse:
        """Create a HealthResponse from API dictionary."""
        db_data = data.get("database")
        return cls(
            status=str(data.get("status", "unknown")),
            version=str(data.get("version", "")),
            build_date=str(data.get("build_date", data.get("buildDate", ""))),
            timestamp=str(data.get("timestamp", "")),
            environment=str(data.get("environment", "production")),
            database=DatabaseHealth.from_dict(db_data) if isinstance(db_data, dict) else None,
        )


@dataclass(frozen=True)
class BestDayInfo:
    """Best day statistics model."""

    date: str
    count: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BestDayInfo:
        """Create BestDayInfo from API dictionary."""
        return cls(
            date=str(data.get("date", "")),
            count=int(data.get("count", 0)),
        )


@dataclass(frozen=True)
class StreakInfo:
    """Detection streak information model."""

    days: int
    start_date: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StreakInfo:
        """Create StreakInfo from API dictionary."""
        return cls(
            days=int(data.get("days", 0)),
            start_date=str(data.get("startDate", data.get("start_date", ""))),
        )


@dataclass(frozen=True)
class DashboardKPIs:
    """Response model for the /api/v2/dashboard/kpis endpoint."""

    lifetime_species: int
    today_detections: int
    best_day: BestDayInfo
    detection_streak: StreakInfo

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DashboardKPIs:
        """Create DashboardKPIs from API dictionary."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data).__name__}")

        if not (
            ("today_detections" in data or "todayDetections" in data)
            and ("lifetime_species" in data or "lifetimeSpecies" in data)
        ):
            raise ValueError("Missing required fields for DashboardKPIs")

        best_day_data = data.get("bestDay", data.get("best_day", {}))
        streak_data = data.get("detectionStreak", data.get("detection_streak", {}))

        best_day = (
            BestDayInfo.from_dict(best_day_data)
            if isinstance(best_day_data, dict)
            else BestDayInfo.from_dict({})
        )
        detection_streak = (
            StreakInfo.from_dict(streak_data)
            if isinstance(streak_data, dict)
            else StreakInfo.from_dict({})
        )

        return cls(
            lifetime_species=int(data.get("lifetimeSpecies", data.get("lifetime_species", 0))),
            today_detections=int(data.get("todayDetections", data.get("today_detections", 0))),
            best_day=best_day,
            detection_streak=detection_streak,
        )


@dataclass(frozen=True)
class AudioSource:
    """Audio source model."""

    id: str
    name: str
    type: str
    state: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AudioSource:
        """Create AudioSource from API dictionary."""
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", data.get("displayName", ""))),
            type=str(data.get("type", "unknown")),
            state=str(data.get("state", "unknown")),
        )


@dataclass(frozen=True)
class BirdImageInfo:
    """Bird image metadata model."""

    url: str
    attribution: str = ""
    license: str = ""
    license_url: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BirdImageInfo:
        """Create BirdImageInfo from API dictionary."""
        return cls(
            url=str(data.get("url", "")),
            attribution=str(data.get("attribution", "")),
            license=str(data.get("license", "")),
            license_url=data.get("licenseUrl", data.get("license_url")),
        )


@dataclass(frozen=True)
class WeatherInfo:
    """Weather context model for detections."""

    weather_icon: str = ""
    weather_main: str | None = None
    description: str | None = None
    temperature: float | None = None
    wind_speed: float | None = None
    wind_gust: float | None = None
    humidity: int | None = None
    units: str | None = None
    moon_phase: float | None = None
    moon_phase_name: str | None = None
    moon_illumination: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WeatherInfo:
        """Create WeatherInfo from API dictionary."""
        temp = data.get("temperature")
        wind = data.get("windSpeed", data.get("wind_speed"))
        gust = data.get("windGust", data.get("wind_gust"))
        hum = data.get("humidity")
        moon_p = data.get("moonPhase", data.get("moon_phase"))
        moon_i = data.get("moonIllumination", data.get("moon_illumination"))

        return cls(
            weather_icon=str(data.get("weatherIcon", data.get("weather_icon", ""))),
            weather_main=data.get("weatherMain", data.get("weather_main")),
            description=data.get("description"),
            temperature=float(temp) if temp is not None else None,
            wind_speed=float(wind) if wind is not None else None,
            wind_gust=float(gust) if gust is not None else None,
            humidity=int(hum) if hum is not None else None,
            units=data.get("units"),
            moon_phase=float(moon_p) if moon_p is not None else None,
            moon_phase_name=data.get("moonPhaseName", data.get("moon_phase_name")),
            moon_illumination=float(moon_i) if moon_i is not None else None,
        )


@dataclass(frozen=True)
class Detection:
    """Bird detection model."""

    id: int
    date: str
    time: str
    scientific_name: str
    common_name: str
    confidence: float
    timestamp: str | None = None
    source_id: str | None = None
    source_name: str | None = None
    species_code: str | None = None
    clip_name: str | None = None
    model_type: str | None = None
    verified: str = "unverified"
    locked: bool = False
    is_new_species: bool = False
    bird_image: BirdImageInfo | None = None
    weather: WeatherInfo | None = None
    raw_data: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Detection:
        """Create Detection from API dictionary."""
        source_data = data.get("source")
        source_id: str | None = None
        source_name: str | None = None

        if isinstance(source_data, dict):
            source_id = source_data.get("id")
            source_name = source_data.get("displayName", source_data.get("name"))
        elif isinstance(source_data, str):
            source_name = source_data
            source_id = data.get("sourceId", data.get("source_id"))
        else:
            source_id = data.get("sourceId", data.get("source_id"))
            source_name = data.get("sourceName", data.get("source_name"))

        image_data = data.get("birdImage", data.get("BirdImage", data.get("bird_image")))
        weather_data = data.get("weather")

        confidence_val = data.get("confidence", data.get("Confidence", 0.0))

        scientific_name = str(
            data.get("scientificName")
            or data.get("ScientificName")
            or data.get("scientific_name")
            or ""
        )
        common_name = str(
            data.get("commonName") or data.get("CommonName") or data.get("common_name") or ""
        )
        bird_image = BirdImageInfo.from_dict(image_data) if isinstance(image_data, dict) else None
        weather = WeatherInfo.from_dict(weather_data) if isinstance(weather_data, dict) else None

        return cls(
            id=int(data.get("id", data.get("detectionId", data.get("ID", 0)))),
            date=str(data.get("date", data.get("Date", ""))),
            time=str(data.get("time", data.get("Time", ""))),
            timestamp=data.get("timestamp", data.get("Timestamp")),
            source_id=source_id,
            source_name=source_name,
            scientific_name=scientific_name,
            common_name=common_name,
            confidence=float(confidence_val),
            species_code=data.get("speciesCode", data.get("SpeciesCode", data.get("species_code"))),
            clip_name=data.get("clipName", data.get("ClipName", data.get("clip_name"))),
            model_type=data.get("modelType", data.get("model_type")),
            verified=str(data.get("verified", "unverified")),
            locked=bool(data.get("locked", False)),
            is_new_species=bool(data.get("isNewSpecies", data.get("is_new_species", False))),
            bird_image=bird_image,
            weather=weather,
            raw_data=data,
        )


@dataclass(frozen=True)
class SpeciesDailySummary:
    """Daily species summary item model."""

    scientific_name: str
    common_name: str
    count: int
    species_code: str | None = None
    hourly_counts: list[int] = field(default_factory=list)
    high_confidence: bool = False
    max_confidence: float = 0.0
    first_heard: str | None = None
    latest_heard: str | None = None
    thumbnail_url: str | None = None
    is_new_species: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpeciesDailySummary:
        """Create SpeciesDailySummary from API dictionary."""
        hourly = data.get("hourly_counts", data.get("hourlyCounts", []))
        return cls(
            scientific_name=str(data.get("scientific_name", data.get("scientificName", ""))),
            common_name=str(data.get("common_name", data.get("commonName", ""))),
            count=int(data.get("count", 0)),
            species_code=data.get("species_code", data.get("speciesCode")),
            hourly_counts=[int(x) for x in hourly] if isinstance(hourly, list) else [],
            high_confidence=bool(data.get("high_confidence", data.get("highConfidence", False))),
            max_confidence=float(data.get("max_confidence", data.get("maxConfidence", 0.0))),
            first_heard=data.get("first_heard", data.get("firstHeard")),
            latest_heard=data.get("latest_heard", data.get("latestHeard")),
            thumbnail_url=data.get("thumbnail_url", data.get("thumbnailUrl")),
            is_new_species=bool(data.get("is_new_species", data.get("isNewSpecies", False))),
        )


@dataclass(frozen=True)
class SpeciesSummary:
    """Overall species summary item model."""

    scientific_name: str
    common_name: str
    count: int
    species_code: str | None = None
    first_heard: str | None = None
    last_heard: str | None = None
    avg_confidence: float = 0.0
    max_confidence: float = 0.0
    thumbnail_url: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpeciesSummary:
        """Create SpeciesSummary from API dictionary."""
        return cls(
            scientific_name=str(data.get("scientific_name", data.get("scientificName", ""))),
            common_name=str(data.get("common_name", data.get("commonName", ""))),
            count=int(data.get("count", 0)),
            species_code=data.get("species_code", data.get("speciesCode")),
            first_heard=data.get("first_heard", data.get("firstHeard")),
            last_heard=data.get("last_heard", data.get("lastHeard")),
            avg_confidence=float(data.get("avg_confidence", data.get("avgConfidence", 0.0))),
            max_confidence=float(data.get("max_confidence", data.get("maxConfidence", 0.0))),
            thumbnail_url=data.get("thumbnail_url", data.get("thumbnailUrl")),
        )


@dataclass(frozen=True)
class SystemInfo:
    """System information model."""

    hostname: str
    platform_version: str
    kernel_version: str
    uptime_seconds: int
    app_uptime_seconds: int
    num_cpu: int
    os_display: str
    architecture: str
    system_model: str | None = None
    time_zone: str | None = None
    cpu_model: str | None = None
    environment: str = "production"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SystemInfo:
        """Create SystemInfo from API dictionary."""
        return cls(
            hostname=str(data.get("hostname", "")),
            platform_version=str(data.get("platform_version", "")),
            kernel_version=str(data.get("kernel_version", "")),
            uptime_seconds=int(data.get("uptime_seconds", 0)),
            app_uptime_seconds=int(data.get("app_uptime_seconds", 0)),
            num_cpu=int(data.get("num_cpu", 0)),
            os_display=str(data.get("os_display", "")),
            architecture=str(data.get("architecture", "")),
            system_model=data.get("system_model"),
            time_zone=data.get("time_zone"),
            cpu_model=data.get("cpu_model"),
            environment=str(data.get("environment", "production")),
        )


@dataclass(frozen=True)
class AudioLevelItem:
    """Individual source audio level measurement."""

    source_id: str
    name: str
    level: float
    clipping: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AudioLevelItem:
        """Create AudioLevelItem from API dictionary."""
        return cls(
            source_id=str(data.get("source", data.get("source_id", ""))),
            name=str(data.get("name", "")),
            level=float(data.get("level", 0.0)),
            clipping=bool(data.get("clipping", False)),
        )


@dataclass(frozen=True)
class AudioLevelEvent:
    """Audio level SSE event model."""

    levels: dict[str, AudioLevelItem]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AudioLevelEvent:
        """Create AudioLevelEvent from API dictionary."""
        raw_levels = data.get("levels", {})
        levels_map: dict[str, AudioLevelItem] = {}
        if isinstance(raw_levels, dict):
            for k, v in raw_levels.items():
                if isinstance(v, dict):
                    levels_map[k] = AudioLevelItem.from_dict(v)
        return cls(levels=levels_map)
