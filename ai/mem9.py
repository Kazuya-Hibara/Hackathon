"""Mem9 persistent memory client (self-hosted mnemo-server, v1alpha2 API)."""
import httpx
from config import settings


def _base_url() -> str:
    return settings.mem9_base_url.rstrip("/")


def _headers() -> dict:
    return {"X-API-Key": settings.mem9_api_key}


async def store_memory(content: str, tags: list[str] | None = None) -> str | None:
    """Store a memory. Returns memory ID."""
    if not settings.mem9_api_key:
        return None

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_base_url()}/v1alpha2/mem9s/memories",
            headers=_headers(),
            json={"content": content, "tags": tags or []},
            timeout=10.0,
        )
        if response.status_code in (200, 201):
            return response.json().get("id")
        return None


async def search_memory(query: str, limit: int = 5) -> list[dict]:
    """Search memories (hybrid vector + keyword)."""
    if not settings.mem9_api_key:
        return []

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_base_url()}/v1alpha2/mem9s/memories",
            headers=_headers(),
            params={"query": query, "limit": limit},
            timeout=10.0,
        )
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) else data.get("results", data.get("memories", []))
        return []


async def store_feedback(suggestion_id: int, action: str, edits: dict | None = None):
    """Store suggestion feedback for learning."""
    content = f"Suggestion {suggestion_id} was {action}."
    if edits:
        content += f" User edits: {edits}"
    await store_memory(content, tags=["feedback", action])


async def get_learned_preferences() -> str:
    """Retrieve learned preferences to inject into AI prompt."""
    results = await search_memory("user preferences feedback patterns", limit=10)
    if not results:
        return ""
    return "\n".join(r.get("content", "") for r in results)
