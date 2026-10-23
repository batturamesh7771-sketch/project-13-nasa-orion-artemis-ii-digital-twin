#!/usr/bin/env python3
"""Validate structure of the AIM 1 Gate 1 engineering pack (standard library only)."""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

def load_json(relative: str):
    path = ROOT / relative
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)

def main() -> int:
    try:
        registry = load_json("data/aim1_source_registry.json")
        events = load_json("data/aim1_launch_event_reference.json")
        assets = load_json("data/aim1_asset_manifest.json")
        schema = load_json("schemas/aim1_to_aim2_state.schema.json")
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: could not load pack JSON: {exc}")
        return 1

    source_ids = {item.get("id") for item in registry.get("sources", [])}
    errors = []
    if not source_ids or None in source_ids:
        errors.append("source registry contains a source with a missing id")
    referenced = set()
    for collection in (events.get("countdown_and_launch", []), events.get("ascent_events", [])):
        for event in collection:
            referenced.update(event.get("source_ids", []))
    referenced.update(events.get("mission_epoch", {}).get("source_ids", []))
    referenced.update(events.get("tli_reference", {}).get("source_ids", []))
    missing = sorted(referenced - source_ids)
    if missing:
        errors.append(f"event source IDs absent from registry: {missing}")

    required_ascent_ids = [e["event_id"] for e in events.get("ascent_events", [])]
    if len(required_ascent_ids) != len(set(required_ascent_ids)):
        errors.append("duplicate event_id in ascent event list")

    for key in ("countdown_and_launch", "ascent_events"):
        for event in events.get(key, []):
            if not event.get("event") or not event.get("event_id"):
                errors.append(f"event in {key} missing event_id/event")
            if event.get("met_s") is not None and not isinstance(event["met_s"], (int, float)):
                errors.append(f"event {event.get('event_id')} has nonnumeric met_s")

    required_schema_fields = schema.get("required", [])
    for field in ("epoch_utc", "reference_frame", "position_m", "velocity_m_s", "mass_kg", "provenance", "model_quality"):
        if field not in required_schema_fields:
            errors.append(f"handoff schema missing required field {field}")

    if not assets.get("assets") or not assets.get("assembly_scene_sequence"):
        errors.append("asset manifest lacks assets or scene sequence")

    if errors:
        print("AIM 1 Gate 1 pack validation: FAIL")
        for error in errors:
            print(f" - {error}")
        return 1

    print("AIM 1 Gate 1 pack validation: PASS")
    print(f"Sources: {len(source_ids)}")
    print(f"Countdown/launch events: {len(events.get('countdown_and_launch', []))}")
    print(f"Ascent/orbit events: {len(events.get('ascent_events', []))}")
    print(f"Asset entries: {len(assets.get('assets', []))}")
    print("Note: this checks pack structure only, not the scientific validity of the flight model.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
