# aiobirdnetgo

[![PyPI version](https://img.shields.io/pypi/v/aiobirdnetgo.svg)](https://pypi.org/project/aiobirdnetgo/)
[![Python versions](https://img.shields.io/pypi/pyversions/aiobirdnetgo.svg)](https://pypi.org/project/aiobirdnetgo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Asynchronous Python client library for the [BirdNET-Go](https://github.com/tphakala/birdnet-go) REST API and real-time Server-Sent Events (SSE) streaming.

Designed primarily for integration with **Home Assistant Core** and other Python asyncio applications.

---

## Features

- ⚡ **Asynchronous:** Built entirely on top of `aiohttp` and `asyncio`.
- 🔍 **Type-Safe:** Frozen dataclasses with full typing support (`py.typed`).
- 🐦 **Real-Time Detection Streaming:** Built-in SSE listener with automatic reconnection and heartbeat handling.
- 📊 **Dashboard KPIs & Analytics:** Fetch daily species summaries, lifetime statistics, and detection streaks.
- 🎙️ **Multi-Source Audio:** Discovers and maps audio devices and RTSP stream sources.
- 🎛️ **Engine Control:** Restart analysis engine or reload classifier models remotely.

---

## Installation

```bash
pip install aiobirdnetgo
```

---

## Quickstart

### Basic API Usage & KPIs

```python
import asyncio
from aiobirdnetgo import BirdNetGoClient


async def main():
    async with BirdNetGoClient(host="192.168.1.50", port=8080) as client:
        # Check connectivity
        if await client.ping():
            print("Connected to BirdNET-Go!")

        # Get system health
        health = await client.get_health()
        print(f"Version: {health.version}, Status: {health.status}")

        # Get dashboard headline KPIs
        kpis = await client.get_kpis()
        print(f"Today's detections: {kpis.today_detections}")
        print(f"Lifetime species count: {kpis.lifetime_species}")
        print(f"Current streak: {kpis.detection_streak.days} days")


if __name__ == "__main__":
    asyncio.run(main())
```

---

### Real-Time Detection Streaming (SSE)

```python
import asyncio
from aiobirdnetgo import BirdNetGoClient


async def main():
    async with BirdNetGoClient(host="192.168.1.50", port=8080) as client:
        print("Listening for live bird detections...")

        stream = client.stream_detections()
        async for detection in stream:
            print(f"🐦 Detected: {detection.common_name} ({detection.scientific_name})")
            print(f"   Confidence: {detection.confidence * 100:.1f}%")
            print(f"   Source: {detection.source_name or detection.source_id}")
            if detection.bird_image:
                print(f"   Photo: {client.get_species_image_url(detection.scientific_name)}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

### Managing Audio Sources & Recent Detections

```python
import asyncio
from aiobirdnetgo import BirdNetGoClient


async def main():
    async with BirdNetGoClient(host="192.168.1.50", port=8080) as client:
        # List audio sources (sound cards & RTSP streams)
        sources = await client.get_audio_sources()
        for source in sources:
            print(f"Source: {source.name} (ID: {source.id}, State: {source.state})")

        # Fetch recent detections
        detections = await client.get_recent_detections(limit=10)
        for det in detections:
            print(f"{det.time} - {det.common_name} ({det.confidence * 100:.0f}%)")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Development & Testing

```bash
# Clone the repository
git clone https://github.com/tphakala/aiobirdnetgo.git
cd aiobirdnetgo

# Install dependencies and dev tools
pip install -e ".[dev]"

# Run linter and type checker
ruff check .
mypy src tests

# Run unit tests with coverage
pytest
```
