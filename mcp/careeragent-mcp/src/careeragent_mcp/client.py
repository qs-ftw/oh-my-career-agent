"""Thin async HTTP client for the CareerAgent FastAPI backend."""

import os
from typing import Any

import httpx


class CareerAgentClient:
    """Async HTTP client wrapping CareerAgent REST API calls."""

    def __init__(self) -> None:
        self.base_url = os.environ.get(
            "CAREERAGENT_API_URL", "http://localhost:8000"
        ).rstrip("/")

    async def get(self, path: str, params: dict | None = None) -> Any:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            resp = await client.get(f"/api{path}", params=params)
            resp.raise_for_status()
            return resp.json()

    async def post(self, path: str, json: dict | None = None) -> Any:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            resp = await client.post(f"/api{path}", json=json)
            resp.raise_for_status()
            # Some endpoints return 204 No Content
            if resp.status_code == 204:
                return None
            return resp.json()

    async def patch(self, path: str, json: dict | None = None) -> Any:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            resp = await client.patch(f"/api{path}", json=json)
            resp.raise_for_status()
            return resp.json()

    async def delete(self, path: str) -> None:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            resp = await client.delete(f"/api{path}")
            resp.raise_for_status()
