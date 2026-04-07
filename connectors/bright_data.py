"""Bright Data SERP API connector."""
import json
from urllib.parse import quote_plus
import httpx
from datetime import date
from config import settings
from db import execute, execute_insert


async def search_serp(query: str, num_results: int = 5) -> list[dict]:
    """Search via Bright Data SERP API (URL-based request endpoint)."""
    if not settings.brightdata_api_key:
        return []

    search_url = f"https://www.google.com/search?q={quote_plus(query)}&hl=en&num={num_results}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.brightdata.com/request",
            headers={
                "Authorization": f"Bearer {settings.brightdata_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "zone": settings.brightdata_serp_zone,
                "url": search_url,
                "format": "json",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        # Parsed JSON returns "results" array with type=organic items
        results = data.get("results", data.get("organic", []))
        if isinstance(results, list):
            return [r for r in results if r.get("type") == "organic" or "title" in r][:num_results]
        return []


async def sync_bright_data(date_from: date | None = None, date_to: date | None = None) -> int:
    """Sync Bright Data search results as raw events.

    Enriches suggestions by searching for topics found in other connectors' data.
    """
    sql = "SELECT raw_data FROM raw_events WHERE connector_id != 'bright_data'"
    params = []
    if date_from:
        sql += " AND event_date >= %s"
        params.append(date_from)
    if date_to:
        sql += " AND event_date <= %s"
        params.append(date_to)
    sql += " ORDER BY created_at DESC LIMIT 20"

    rows = execute(sql, params)
    if not rows:
        return 0

    topics = set()
    for row in rows:
        data = row["raw_data"]
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, dict):
            for key in ["subject", "title", "summary", "description"]:
                if key in data and data[key]:
                    topics.add(data[key][:100])

    count = 0
    for topic in list(topics)[:5]:
        results = await search_serp(topic)
        for result in results:
            external_id = f"serp_{hash(result.get('url', result.get('link', '')))}"
            try:
                execute_insert(
                    """INSERT INTO raw_events (connector_id, external_id, event_type, event_date, raw_data)
                       VALUES (%s, %s, %s, %s, %s)
                       ON DUPLICATE KEY UPDATE raw_data = VALUES(raw_data)""",
                    ("bright_data", external_id, "search_result",
                     date_from or date.today(),
                     json.dumps(result)),
                )
                count += 1
            except Exception:
                pass

    return count
