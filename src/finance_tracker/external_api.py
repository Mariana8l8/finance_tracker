"""Async HTTP client helpers for laboratory work 8."""

from __future__ import annotations

from typing import Any
import asyncio

import httpx


JsonObject = dict[str, Any]


async def fetch_json_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    attempts: int = 3,
) -> JsonObject:
    """Fetch one JSON document with retry and simple linear backoff."""

    for attempt in range(1, attempts + 1):
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("JSON response must be an object.")
            return data
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError):
            if attempt == attempts:
                raise
            await asyncio.sleep(0.1 * attempt)

    raise RuntimeError("Unexpected retry state.")


async def limited_fetch_json(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    url: str,
    *,
    attempts: int,
) -> JsonObject:
    """Fetch a JSON document while respecting a concurrency limit."""

    async with semaphore:
        return await fetch_json_with_retry(
            client,
            url,
            attempts=attempts,
        )


async def fetch_many_json(
    urls: list[str],
    *,
    timeout_seconds: float = 5.0,
    attempts: int = 3,
    concurrency_limit: int = 3,
) -> list[JsonObject]:
    """Fetch many JSON resources concurrently using Tasks and gather()."""

    semaphore = asyncio.Semaphore(concurrency_limit)
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        tasks = [
            asyncio.create_task(
                limited_fetch_json(
                    client,
                    semaphore,
                    url,
                    attempts=attempts,
                )
            )
            for url in urls
        ]
        return list(await asyncio.gather(*tasks))


async def fetch_many_json_with_timeout(
    urls: list[str],
    *,
    timeout_seconds: float = 5.0,
    attempts: int = 3,
    concurrency_limit: int = 3,
) -> list[JsonObject]:
    """Run a batch fetch with an overall timeout."""

    return await asyncio.wait_for(
        fetch_many_json(
            urls,
            timeout_seconds=timeout_seconds,
            attempts=attempts,
            concurrency_limit=concurrency_limit,
        ),
        timeout=timeout_seconds,
    )
