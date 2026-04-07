"""Agnes AI client via ZenMux (OpenAI-compatible API)."""
import json
from openai import OpenAI
from config import settings

IMPACT_CATEGORIES = [
    "DECISION — Decisions made or influenced",
    "BLOCKER_REMOVED — Unblocking others",
    "ALIGNMENT — Syncs, 1:1s, stakeholder alignment",
    "STRUCTURE — Processes, frameworks, documentation",
    "TEAM_DEV — Coaching, hiring, team development",
    "STRATEGIC_ANTICIPATION — Proactive risk/opportunity identification",
    "FIRES_HANDLED — Urgent issues resolved",
]

SYSTEM_PROMPT_TEMPLATE = """You are an AI assistant that analyzes a manager's daily work activity and suggests impact items.

## Your Role
Analyze raw work data (meetings, messages, code sessions) and identify meaningful impact items the manager should log.

## User Context
- Role: {role}
- Team: {team_context}

## Impact Categories
{categories}

## Scope Tags
The user has defined these scope tags to classify work:
{scope_tags}

## Scope Response Types
When work is out-of-scope, classify the response:
- ADVISORY: Provided advice only, didn't take ownership
- TRADEOFF: Took it on but traded something else off
- NO: Declined the request
- ABSORBED: Took it on without tradeoff

## Output Format
Return a JSON array of suggestion objects:
```json
[
  {{
    "category": "DECISION",
    "description": "Decided to postpone the migration to Q3 based on risk assessment",
    "stakeholders": ["Alice", "Bob"],
    "work_type": "strategic",
    "delegation_score": 2,
    "time_estimate": "1h",
    "impact_level": "HIGH",
    "scope_tag": "CORE_ROLE",
    "scope_response": null,
    "escalated_from": null,
    "reasoning": "Based on the calendar event 'Migration Planning' and follow-up Slack thread...",
    "confidence": 0.85
  }}
]
```

Rules:
- time_estimate is REQUIRED (e.g., "30m", "1h", "2h", "4h")
- impact_level is REQUIRED: LOW, MEDIUM, or HIGH
- reasoning must quote specific evidence from the raw data
- confidence is 0.0-1.0 (how sure you are this is a real impact item)
- scope_response is only set when scope_tag is NOT the user's core role tag
- escalated_from is the person who escalated work to the user (if applicable)
- Do not fabricate events — only suggest items supported by the raw data
"""


def get_client() -> OpenAI:
    return OpenAI(
        api_key=settings.zenmux_api_key,
        base_url=settings.zenmux_base_url,
    )


DEMO_SUGGESTIONS = [
    {
        "category": "TEAM_DEV",
        "description": "Recognized Yuki's initiative in handling sponsor escalations independently during the hackathon",
        "stakeholders": ["Yuki"],
        "work_type": "coaching",
        "delegation_score": 3,
        "time_estimate": "15m",
        "impact_level": "MEDIUM",
        "scope_tag": "CORE_ROLE",
        "reasoning": "Slack data shows Yuki resolved 3 sponsor queries without escalating. Coaching investment paying off.",
        "confidence": 0.88,
    },
    {
        "category": "STRATEGIC_ANTICIPATION",
        "description": "Opportunity to package hackathon playbook (checklist + rubric + venue template) for Q3 reuse",
        "stakeholders": ["Operations Team"],
        "work_type": "proactive",
        "delegation_score": 4,
        "time_estimate": "2h",
        "impact_level": "HIGH",
        "scope_tag": "STRATEGIC_INITIATIVE",
        "reasoning": "3 hackathons planned in Q3. Today's learnings (WiFi backup, Windows SSL guide, flexible timeline) are reusable.",
        "confidence": 0.75,
    },
    {
        "category": "ALIGNMENT",
        "description": "Schedule post-hackathon retro with judges to improve scoring rubric for next event",
        "stakeholders": ["Judges Panel"],
        "work_type": "coordination",
        "delegation_score": 2,
        "time_estimate": "30m",
        "impact_level": "MEDIUM",
        "scope_tag": "CORE_ROLE",
        "reasoning": "Calendar shows judging ends at 17:30. Fresh impressions = better feedback. Don't wait until next week.",
        "confidence": 0.82,
    },
]


async def generate_suggestions(
    raw_events_text: str,
    existing_context: str = "",
    scope_tags: str = "CORE_ROLE, ADJACENT_OPS, CROSS_FUNCTIONAL, BAU_OVERHEAD, STRATEGIC_INITIATIVE",
) -> list[dict]:
    """Call Agnes AI to generate impact suggestions. Falls back to demo data if no API key."""
    if not settings.zenmux_api_key:
        return DEMO_SUGGESTIONS

    client = get_client()

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        role=settings.user_role,
        team_context=settings.user_team_context,
        categories="\n".join(f"- {c}" for c in IMPACT_CATEGORIES),
        scope_tags=scope_tags,
    )

    user_message = f"""## Raw Activity Data

{raw_events_text}

## Existing Context
{existing_context if existing_context else "No existing entries or suggestions for this date."}

Generate impact item suggestions based on the raw activity data above. Return ONLY a JSON array."""

    response = client.chat.completions.create(
        model=settings.zenmux_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=4000,
    )

    content = response.choices[0].message.content.strip()

    # Parse JSON (handle code fences)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    return json.loads(content)
