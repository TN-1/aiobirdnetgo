"""Asynchronous client for BirdNET-Go API."""

from __future__ import annotations

import ipaddress
import logging
import urllib.parse
from base64 import b64encode
from typing import Any

from aiohttp import BasicAuth, ClientError, ClientResponseError, ClientSession, ClientTimeout

from .const import (
    DEFAULT_PORT,
    DEFAULT_RECONNECT_INTERVAL,
    DEFAULT_SSE_TIMEOUT,
    DEFAULT_TIMEOUT,
    ENDPOINT_AUDIO_SOURCES,
    ENDPOINT_CONTROL_RELOAD,
    ENDPOINT_CONTROL_RESTART,
    ENDPOINT_DAILY_SPECIES,
    ENDPOINT_DETECTION_STREAM,
    ENDPOINT_DETECTIONS,
    ENDPOINT_HEALTH,
    ENDPOINT_KPIS,
    ENDPOINT_PING,
    ENDPOINT_RECENT_DETECTIONS,
    ENDPOINT_SOUNDLEVEL_STREAM,
    ENDPOINT_SPECIES_SUMMARY,
    ENDPOINT_STREAM_SOURCES,
    ENDPOINT_SYSTEM_INFO,
    MAX_RECONNECT_INTERVAL,
)
from .exceptions import (
    BirdNetGoAuthenticationError,
    BirdNetGoConnectionError,
    BirdNetGoNotFoundError,
    BirdNetGoResponseError,
    BirdNetGoTimeoutError,
)
from .models import (
    AudioSource,
    DashboardKPIs,
    Detection,
    HealthResponse,
    PingResponse,
    SpeciesDailySummary,
    SpeciesSummary,
    SystemInfo,
)
from .stream import AudioLevelStream, DetectionStream

_LOGGER = logging.getLogger(__package__)


class BirdNetGoClient:
    """Asynchronous client for communicating with a BirdNET-Go instance."""

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        use_ssl: bool = False,
        base_path: str = "",
        session: ClientSession | None = None,
        request_timeout: float = DEFAULT_TIMEOUT,
        api_key: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Initialize BirdNetGoClient.

        Args:
            host: Hostname or IP address of the BirdNET-Go server.
            port: Port number (default: 8080).
            use_ssl: Whether to use HTTPS (default: False).
            base_path: URL base path if behind a reverse proxy (e.g., "/birdnet").
            session: Optional existing aiohttp.ClientSession.
            request_timeout: HTTP request timeout in seconds (default: 10.0).
            api_key: Optional API key / Bearer token.
            username: Optional Basic Auth username.
            password: Optional Basic Auth password.
        """
        # Clean host (strip scheme, path, brackets, or trailing slashes if passed)
        clean_host = host.strip()
        if "://" in clean_host:
            parsed = urllib.parse.urlparse(clean_host)
            use_ssl = parsed.scheme.lower() == "https"
            clean_host = parsed.hostname or clean_host
            if parsed.port:
                port = parsed.port

        clean_host = clean_host.strip("[]")
        try:
            ip = ipaddress.ip_address(clean_host)
            clean_host = ip.compressed
        except ValueError:
            clean_host = clean_host.lower()

        self._host = clean_host
        self._port = port
        self._use_ssl = use_ssl
        self._base_path = base_path.rstrip("/")
        self._custom_session = session is not None
        self._session = session
        self._request_timeout = request_timeout
        self._api_key = api_key
        self._username = username
        self._password = password

        # Format host for URL (wrap IPv6 literals in brackets)
        url_host = (
            f"[{self._host}]"
            if ":" in self._host and not self._host.startswith("[")
            else self._host
        )
        scheme = "https" if self._use_ssl else "http"
        self._base_url = f"{scheme}://{url_host}:{self._port}{self._base_path}"

    @property
    def host(self) -> str:
        """Get the configured host."""
        return self._host

    @property
    def port(self) -> int:
        """Get the configured port."""
        return self._port

    @property
    def use_ssl(self) -> bool:
        """Get whether SSL is enabled."""
        return self._use_ssl

    @property
    def base_url(self) -> str:
        """Get the base URL of the BirdNET-Go instance."""
        return self._base_url

    @property
    def detection_stream_endpoint(self) -> str:
        """Get the detection stream endpoint."""
        return ENDPOINT_DETECTION_STREAM

    @property
    def soundlevel_stream_endpoint(self) -> str:
        """Get the sound level stream endpoint."""
        return ENDPOINT_SOUNDLEVEL_STREAM

    @property
    def session(self) -> ClientSession:
        """Get or create the aiohttp ClientSession."""
        if self._session is None or self._session.closed:
            self._session = ClientSession()
            self._custom_session = False
        return self._session

    def get_endpoint_url(self, endpoint: str) -> str:
        """Build full URL for a given API endpoint."""
        clean_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        return f"{self._base_url}{clean_endpoint}"

    def get_headers(self) -> dict[str, str]:
        """Build standard request headers."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "aiobirdnetgo/0.1.5",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        elif self._username and self._password:
            auth_str = f"{self._username}:{self._password}"
            encoded = b64encode(auth_str.encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {encoded}"
        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> Any:
        """Perform an HTTP request with error handling."""
        url = self.get_endpoint_url(endpoint)
        headers = self.get_headers()

        # Filter out None values from params
        clean_params = {k: v for k, v in params.items() if v is not None} if params else None

        auth = None
        if self._username and self._password and "Authorization" not in headers:
            auth = BasicAuth(self._username, self._password)

        try:
            async with self.session.request(
                method=method,
                url=url,
                params=clean_params,
                json=json_data,
                headers=headers,
                auth=auth,
                timeout=ClientTimeout(total=self._request_timeout),
            ) as response:
                if response.status in (401, 403):
                    text = await response.text()
                    raise BirdNetGoAuthenticationError(
                        f"Authentication failed (HTTP {response.status}): {text}"
                    )

                if response.status == 404:
                    raise BirdNetGoNotFoundError(f"Resource not found: {url}")

                if response.status >= 400:
                    text = await response.text()
                    raise BirdNetGoResponseError(response.status, text)

                # Return parsed JSON
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await response.json()
                # Fallback for plain text or unexpected types
                return await response.text()

        except TimeoutError as err:
            raise BirdNetGoTimeoutError(f"Timeout communicating with {url}") from err
        except ClientResponseError as err:
            if err.status in (401, 403):
                raise BirdNetGoAuthenticationError(f"Authentication failed: {err}") from err
            if err.status == 404:
                raise BirdNetGoNotFoundError(f"Resource not found: {url}") from err
            raise BirdNetGoResponseError(err.status, err.message) from err
        except ClientError as err:
            raise BirdNetGoConnectionError(f"Connection error reaching {url}: {err}") from err

    async def ping(self) -> bool:
        """Test connectivity to BirdNET-Go.

        Returns True if the instance is reachable and responds with status ok.
        """
        try:
            resp = await self._request("GET", ENDPOINT_PING)
            return isinstance(resp, dict) and resp.get("status") == "ok"
        except (BirdNetGoConnectionError, BirdNetGoTimeoutError, BirdNetGoAuthenticationError):
            return False

    async def get_ping(self) -> PingResponse:
        """Get the raw ping response."""
        data = await self._request("GET", ENDPOINT_PING)
        return PingResponse.from_dict(data if isinstance(data, dict) else {})

    async def get_health(self) -> HealthResponse:
        """Get server health and database status."""
        data = await self._request("GET", ENDPOINT_HEALTH)
        return HealthResponse.from_dict(data if isinstance(data, dict) else {})

    async def get_kpis(self) -> DashboardKPIs:
        """Get dashboard KPI headline statistics (today detections, streak, species count)."""
        data = await self._request("GET", ENDPOINT_KPIS)
        if not isinstance(data, dict):
            raise BirdNetGoResponseError(
                200, f"Expected JSON object for KPIs, got {type(data).__name__}"
            )
        try:
            return DashboardKPIs.from_dict(data)
        except (TypeError, ValueError) as err:
            raise BirdNetGoResponseError(200, f"Malformed KPI response data: {err}") from err

    async def get_audio_sources(self, streams_only: bool = False) -> list[AudioSource]:
        """Get configured audio sources (microphones, RTSP streams)."""
        endpoint = ENDPOINT_STREAM_SOURCES if streams_only else ENDPOINT_AUDIO_SOURCES
        data = await self._request("GET", endpoint)
        if isinstance(data, dict):
            sources = data.get("sources", [])
            if isinstance(sources, list):
                return [AudioSource.from_dict(s) for s in sources if isinstance(s, dict)]
        return []

    async def get_recent_detections(
        self,
        limit: int = 50,
        source: str | None = None,
    ) -> list[Detection]:
        """Get recent bird detections."""
        params: dict[str, Any] = {"limit": limit}
        if source:
            params["source"] = source
        data = await self._request("GET", ENDPOINT_RECENT_DETECTIONS, params=params)
        if isinstance(data, list):
            return [Detection.from_dict(d) for d in data if isinstance(d, dict)]
        return []

    async def get_detections(
        self,
        date: str | None = None,
        species: str | None = None,
        min_confidence: float | None = None,
        source: str | None = None,
        limit: int = 100,
    ) -> list[Detection]:
        """Query detections with filtering options."""
        params: dict[str, Any] = {
            "limit": limit,
            "date": date,
            "species": species,
            "min_confidence": min_confidence,
            "source": source,
        }
        data = await self._request("GET", ENDPOINT_DETECTIONS, params=params)
        if isinstance(data, list):
            return [Detection.from_dict(d) for d in data if isinstance(d, dict)]
        return []

    async def get_detection(self, detection_id: int) -> Detection:
        """Get a single detection by its ID."""
        data = await self._request("GET", f"{ENDPOINT_DETECTIONS}/{detection_id}")
        return Detection.from_dict(data if isinstance(data, dict) else {})

    async def get_daily_species_summary(
        self,
        date: str | None = None,
        min_confidence: float | None = None,
        limit: int | None = None,
    ) -> list[SpeciesDailySummary]:
        """Get daily species detection summary (counts, first/last heard times)."""
        params: dict[str, Any] = {
            "date": date,
            "min_confidence": min_confidence,
            "limit": limit,
        }
        data = await self._request("GET", ENDPOINT_DAILY_SPECIES, params=params)
        if isinstance(data, list):
            return [SpeciesDailySummary.from_dict(item) for item in data if isinstance(item, dict)]
        return []

    async def get_species_summary(self) -> list[SpeciesSummary]:
        """Get overall lifetime species detection summary."""
        data = await self._request("GET", ENDPOINT_SPECIES_SUMMARY)
        if isinstance(data, list):
            return [SpeciesSummary.from_dict(item) for item in data if isinstance(item, dict)]
        return []

    async def get_system_info(self) -> SystemInfo:
        """Get system information and host resource usage."""
        data = await self._request("GET", ENDPOINT_SYSTEM_INFO)
        return SystemInfo.from_dict(data if isinstance(data, dict) else {})

    async def restart_analysis(self) -> bool:
        """Trigger restart of the BirdNET analysis engine."""
        await self._request("POST", ENDPOINT_CONTROL_RESTART)
        return True

    async def reload_model(self) -> bool:
        """Trigger reload of the BirdNET classifier model."""
        await self._request("POST", ENDPOINT_CONTROL_RELOAD)
        return True

    def get_audio_clip_url(self, detection_id: int) -> str:
        """Get URL for downloading or playing detection audio clip."""
        return self.get_endpoint_url(f"/api/v2/audio/{detection_id}")

    def get_spectrogram_url(self, detection_id: int) -> str:
        """Get URL for viewing detection spectrogram."""
        return self.get_endpoint_url(f"/api/v2/spectrogram/{detection_id}")

    def get_species_image_url(self, scientific_name: str) -> str:
        """Get URL for species thumbnail image proxy."""
        encoded_name = urllib.parse.quote(scientific_name)
        return self.get_endpoint_url(f"/api/v2/media/image/{encoded_name}")

    def stream_detections(
        self,
        auto_reconnect: bool = True,
        reconnect_interval: float = DEFAULT_RECONNECT_INTERVAL,
        max_reconnect_interval: float = MAX_RECONNECT_INTERVAL,
        read_timeout: float = DEFAULT_SSE_TIMEOUT,
    ) -> DetectionStream:
        """Create a real-time Server-Sent Events stream for bird detections."""
        return DetectionStream(
            client=self,
            auto_reconnect=auto_reconnect,
            reconnect_interval=reconnect_interval,
            max_reconnect_interval=max_reconnect_interval,
            read_timeout=read_timeout,
        )

    def stream_audio_levels(
        self,
        auto_reconnect: bool = True,
        reconnect_interval: float = DEFAULT_RECONNECT_INTERVAL,
        max_reconnect_interval: float = MAX_RECONNECT_INTERVAL,
        read_timeout: float = DEFAULT_SSE_TIMEOUT,
    ) -> AudioLevelStream:
        """Create a real-time Server-Sent Events stream for audio levels."""
        return AudioLevelStream(
            client=self,
            auto_reconnect=auto_reconnect,
            reconnect_interval=reconnect_interval,
            max_reconnect_interval=max_reconnect_interval,
            read_timeout=read_timeout,
        )

    async def close(self) -> None:
        """Close the underlying client session if owned."""
        if self._session and not self._custom_session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> BirdNetGoClient:
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        await self.close()
