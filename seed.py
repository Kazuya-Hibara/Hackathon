"""Seed demo data for TEAMZ Tokyo manager."""
import json
from datetime import date, timedelta
from db import init_db, execute, execute_insert

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
TWO_DAYS_AGO = TODAY - timedelta(days=2)


def seed():
    init_db()

    # Clear existing demo data
    for table in ["entries", "suggestions", "raw_events", "daily_meta", "connector_config"]:
        execute(f"DELETE FROM {table}")

    print("Seeding demo data for TEAMZ Tokyo manager...")

    # ── Connector config ──
    for cid in ["slack", "gcal", "bright_data", "claude_code"]:
        execute(
            "INSERT INTO connector_config (connector_id, enabled, last_sync) VALUES (%s, 1, NOW())",
            (cid,),
        )

    # ── Daily Meta ──
    daily_meta = [
        (TODAY, "M", "STRATEGIC", "Hackathon day! High energy, lots of moving parts."),
        (YESTERDAY, "H", "REACTIVE", "Pre-hackathon chaos. 14 sponsors calling about booth setup."),
        (TWO_DAYS_AGO, "L", "STRATEGIC", "Calm before the storm. Finalized judging criteria."),
    ]
    for d, load, energy, summary in daily_meta:
        execute(
            "INSERT INTO daily_meta (date, cognitive_load, energy, summary) VALUES (%s, %s, %s, %s)",
            (d, load, energy, summary),
        )

    # ── Entries (logged impact items) ──
    entries = [
        # Today
        (TODAY, "DECISION", "Decided to extend hackathon deadline by 30min after 3 teams requested more time",
         ["Yuki", "Sponsors"], "strategic", 1, "30m", "HIGH", "CORE_ROLE", None, None,
         "Sometimes the best management move is knowing when to flex the rules"),
        (TODAY, "ALIGNMENT", "Morning sync with all 7 sponsor reps — confirmed API keys, booth layout, and judging slots",
         ["Zeabur", "Agnes AI", "TiDB", "Bright Data", "Mem9", "Nosana", "QoderWork"],
         "coordination", 3, "1h", "HIGH", "CORE_ROLE", None, None, None),
        (TODAY, "FIRES_HANDLED", "WiFi went down in Hall B during hackathon kickoff. Coordinated with venue IT, got backup hotspot running in 8 minutes",
         ["Venue IT", "Participants"], "reactive", 1, "15m", "HIGH", "CORE_ROLE", None, None,
         "Personal record for WiFi crisis resolution. Previous best: 12 minutes at ETH Tokyo."),
        (TODAY, "BLOCKER_REMOVED", "Team 'Crypto Cats' couldn't connect to TiDB — walked them through SSL cert setup on Windows",
         ["Team Crypto Cats"], "support", 2, "20m", "MEDIUM", "ADJACENT_OPS", "ADVISORY", "Yuki",
         "Note to self: add Windows SSL guide to next hackathon starter kit"),

        # Yesterday
        (YESTERDAY, "STRUCTURE", "Created sponsor integration checklist template — 7 sponsors × 4 touchpoints = 28 items tracked",
         ["Operations Team"], "proactive", 4, "2h", "HIGH", "CORE_ROLE", None, None,
         "This template will save ~3h per hackathon going forward"),
        (YESTERDAY, "ALIGNMENT", "1:1 with Tanaka-san (VP) about Q3 event roadmap. Secured budget for 2 more hackathons",
         ["Tanaka-san"], "strategic", 1, "45m", "HIGH", "CORE_ROLE", None, None, None),
        (YESTERDAY, "FIRES_HANDLED", "Discovered catering order was for 100 people, not 200. Emergency call to vendor, upgraded order with 2h to spare",
         ["Catering Vendor", "Yuki"], "reactive", 1, "30m", "HIGH", "BAU_OVERHEAD", "ABSORBED", None,
         "The hero we needed. Also, always triple-check headcount."),
        (YESTERDAY, "TEAM_DEV", "Coached Yuki on sponsor relationship management — she handled 3 sponsor calls independently after",
         ["Yuki"], "coaching", 2, "1h", "MEDIUM", "CORE_ROLE", None, None, None),
        (YESTERDAY, "STRATEGIC_ANTICIPATION", "Noticed 60% of registered teams are solo developers — adjusted judging criteria to not penalize team size",
         None, "proactive", 1, "30m", "MEDIUM", "CORE_ROLE", None, None,
         "Data-driven decision. Last hackathon, solo devs scored 15% lower on average."),

        # Two days ago
        (TWO_DAYS_AGO, "DECISION", "Selected Happo-en as venue over 3 alternatives — best WiFi infrastructure and garden vibes for networking",
         ["Venue Committee"], "strategic", 1, "1h", "HIGH", "CORE_ROLE", None, None,
         "Gardens > fluorescent-lit conference rooms for creative energy"),
        (TWO_DAYS_AGO, "STRUCTURE", "Drafted judging rubric: 25% MVP completion, 25% Innovation, 25% Real-world relevance, 25% Sponsor tech usage",
         ["Judges Panel"], "proactive", 3, "1.5h", "HIGH", "CORE_ROLE", None, None, None),
        (TWO_DAYS_AGO, "ALIGNMENT", "Cross-team standup with marketing, ops, and partnerships. Aligned on social media coverage plan",
         ["Marketing", "Ops", "Partnerships"], "coordination", 2, "30m", "MEDIUM", "CORE_ROLE", None, None, None),
    ]

    for e in entries:
        d, cat, desc, stakeholders, wt, deleg, time, impact, scope, scope_resp, esc_from, notes = e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9], e[10], e[11]
        execute_insert(
            """INSERT INTO entries (date, category, description, stakeholders, work_type,
               delegation_score, time_estimate, impact_level, scope_tag, scope_response,
               escalated_from, notes, source)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'manual')""",
            (d, cat, desc, json.dumps(stakeholders) if stakeholders else None,
             wt, deleg, time, impact, scope, scope_resp, esc_from, notes),
        )

    # ── Raw Events (simulated connector data) ──
    raw_events = [
        # Slack messages
        ("slack", "slack_001", "message", TODAY,
         {"channel": "#hackathon-ops", "from": "Yuki", "text": "WiFi is down in Hall B! Teams are panicking 😱", "ts": "10:15"}),
        ("slack", "slack_002", "message", TODAY,
         {"channel": "#hackathon-ops", "from": "Manager", "text": "On it. Contacting venue IT now. ETA 10 min.", "ts": "10:16"}),
        ("slack", "slack_003", "message", TODAY,
         {"channel": "#sponsors", "from": "TiDB Rep", "text": "Teams are having SSL issues connecting to Cloud Zero from Windows. Can someone help?", "ts": "11:30"}),
        ("slack", "slack_004", "message", TODAY,
         {"channel": "#general", "from": "Team Crypto Cats", "text": "Amazing hackathon! Best organized event we've been to in Tokyo 🎉", "ts": "16:00"}),
        ("slack", "slack_005", "message", YESTERDAY,
         {"channel": "#hackathon-ops", "from": "Yuki", "text": "Catering headcount is wrong — shows 100 but we have 200 registered!", "ts": "14:00"}),
        ("slack", "slack_006", "message", YESTERDAY,
         {"channel": "#leadership", "from": "Tanaka-san", "text": "Great prep work on the hackathon. Let's discuss Q3 roadmap tomorrow.", "ts": "17:00"}),

        # Calendar events
        ("gcal", "gcal_001", "event", TODAY,
         {"subject": "TEAMZ AI Hackathon — Main Event", "start": "13:00", "end": "18:00",
          "attendees": ["All participants", "Sponsors", "Judges"], "location": "Happo-en, Minato City"}),
        ("gcal", "gcal_002", "event", TODAY,
         {"subject": "Morning Sponsor Sync", "start": "09:00", "end": "10:00",
          "attendees": ["Zeabur", "Agnes AI", "TiDB", "Bright Data", "Mem9", "Nosana", "QoderWork"]}),
        ("gcal", "gcal_003", "event", YESTERDAY,
         {"subject": "1:1 with Tanaka-san — Q3 Planning", "start": "15:00", "end": "15:45",
          "attendees": ["Tanaka-san"], "notes": "Discuss budget for 2 additional hackathons"}),
        ("gcal", "gcal_004", "event", YESTERDAY,
         {"subject": "Cross-team Standup", "start": "10:00", "end": "10:30",
          "attendees": ["Marketing", "Ops", "Partnerships"]}),

        # Bright Data search results (pre-cached)
        ("bright_data", "serp_001", "search_result", TODAY,
         {"title": "How to Run a Successful AI Hackathon in 2026", "url": "https://example.com/ai-hackathon-guide",
          "snippet": "Key factors: clear judging criteria, reliable WiFi, sponsor integration, and flexible timelines."}),
        ("bright_data", "serp_002", "search_result", TODAY,
         {"title": "TEAMZ Summit Tokyo — Web3 Meets AI", "url": "https://example.com/teamz-summit",
          "snippet": "TEAMZ's flagship event draws 2000+ attendees and 50+ sponsors annually."}),
    ]

    for connector, ext_id, etype, edate, data in raw_events:
        execute_insert(
            """INSERT INTO raw_events (connector_id, external_id, event_type, event_date, raw_data, processed)
               VALUES (%s, %s, %s, %s, %s, 1)""",
            (connector, ext_id, etype, edate, json.dumps(data)),
        )

    # ── Suggestions (AI-generated, pending review) ──
    suggestions = [
        (TODAY, "TEAM_DEV", "Recognized Yuki's growth in sponsor management — she independently handled 3 sponsor escalations today",
         ["Yuki"], "coaching", 3, "15m", "MEDIUM", "CORE_ROLE", None, None,
         "Slack data shows Yuki resolved 3 sponsor DMs without escalating. This is a coaching win from yesterday's 1:1.", 0.88),
        (TODAY, "STRATEGIC_ANTICIPATION", "Identified opportunity to create 'Hackathon-in-a-Box' template from today's learnings for Q3 events",
         None, "proactive", 4, "N/A", "HIGH", "STRATEGIC_INITIATIVE", None, None,
         "The sponsor checklist + judging rubric + venue requirements could be packaged. 3 hackathons planned in Q3.", 0.75),
        (TODAY, "ALIGNMENT", "Post-hackathon debrief with judges — collect feedback on scoring rubric effectiveness",
         ["Judges Panel"], "coordination", 2, "30m", "MEDIUM", "CORE_ROLE", None, None,
         "Calendar shows judging ends at 17:30. A 30-min debrief while impressions are fresh would be valuable.", 0.82),
        (TODAY, "BLOCKER_REMOVED", "Created quick-start guide for Windows users connecting to TiDB Cloud Zero (SSL cert setup)",
         ["Future Participants"], "proactive", 4, "30m", "MEDIUM", "ADJACENT_OPS", "TRADEOFF", None,
         "3 teams hit this issue today. A 30-min doc now saves hours at next hackathon.", 0.70),
    ]

    for s in suggestions:
        d, cat, desc, stakeholders, wt, deleg, time, impact, scope, scope_resp, esc_from, reasoning, conf = s
        execute_insert(
            """INSERT INTO suggestions
               (date, status, suggested_category, suggested_description, suggested_stakeholders,
                suggested_work_type, suggested_delegation_score, suggested_time_estimate,
                suggested_impact_level, suggested_scope_tag, suggested_scope_response,
                suggested_escalated_from, reasoning, confidence)
               VALUES (%s, 'pending', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (d, cat, desc, json.dumps(stakeholders) if stakeholders else None,
             wt, deleg, time, impact, scope, scope_resp, esc_from, reasoning, conf),
        )

    print(f"✓ Seeded {len(entries)} entries, {len(raw_events)} raw events, {len(suggestions)} suggestions")
    print(f"✓ Dates: {TWO_DAYS_AGO} → {TODAY}")
    print("✓ Demo data ready! Start the app with: python main.py")


if __name__ == "__main__":
    seed()
