"""Tests for Nanit card semantic sensor override support."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "frontend" / "src"
BUNDLE = ROOT / "custom_components" / "nanit" / "frontend" / "nanit-card.js"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_card_config_exposes_temperature_and_humidity_override_fields() -> None:
    """The card config contract should expose semantic sensor entity overrides."""
    types = _read(SRC_DIR / "types.ts")

    assert "temperature_entity_id?: string;" in types
    assert "humidity_entity_id?: string;" in types


def test_sensor_overlay_prefers_semantic_override_entities() -> None:
    """The overlay renderer should prefer semantic config overrides over discovered entities."""
    card = _read(SRC_DIR / "nanit-card.ts")

    assert "this._config.temperature_entity_id || entities.temperature" in card
    assert "this._config.humidity_entity_id || entities.humidity" in card
    assert "_renderSensorOverlays(entities" in card


def test_visual_editor_includes_semantic_override_entity_pickers() -> None:
    """The visual editor should expose optional semantic override pickers."""
    editor = _read(SRC_DIR / "nanit-card-editor.ts")

    assert '"temperature_entity_id"' in editor
    assert '"humidity_entity_id"' in editor
    assert "Temperature Entity Override" in editor
    assert "Humidity Entity Override" in editor


def test_card_remounts_stalled_stream_via_liveness_watchdog() -> None:
    """The card should continuously watch the video and remount it when it stalls.

    Recovery must keep working *after* the initial load — HA leaves the <video>
    element mounted when the RTMPS feed dies, so the card polls currentTime and
    remounts <ha-camera-stream> (bumping the epoch) whenever it stops advancing.
    """
    card = _read(SRC_DIR / "nanit-card.ts")

    assert "_checkStreamHealth" in card
    assert "video.currentTime" in card
    assert "setInterval" in card
    assert "this._streamEpoch += 1" in card
    assert "keyed(`${entities.camera}-${this._streamEpoch}`" in card


def test_liveness_watchdog_reaches_nested_player_video() -> None:
    """The watchdog must find the <video> nested inside HA's player child.

    HA renders the HLS/WebRTC <video> inside ha-hls-player / ha-web-rtc-player,
    one shadow root deeper than ha-camera-stream, so a single-level querySelector
    misses it. The card must drill through the nested player.
    """
    card = _read(SRC_DIR / "nanit-card.ts")

    assert "_findStreamVideo" in card
    assert "ha-hls-player, ha-web-rtc-player" in card


def test_liveness_watchdog_never_loops_on_a_never_started_stream() -> None:
    """A feed that has never produced a frame must be treated as loading, not stalled.

    Only a *previously-live* feed (one that advanced then froze) may trigger a
    remount, and remounts must be bounded so a mis-read or outage can't loop.
    """
    card = _read(SRC_DIR / "nanit-card.ts")

    assert "_sawProgress" in card
    assert "if (!this._sawProgress || video.paused) return;" in card
    assert "MAX_STREAM_RELOADS" in card
    assert "_reloadCooldownUntil" in card


def test_bundled_card_contains_semantic_override_support() -> None:
    """The shipped bundle should include the override logic after frontend build."""
    bundle = _read(BUNDLE)

    assert "temperature_entity_id" in bundle
    assert "humidity_entity_id" in bundle


def test_bundled_card_contains_stalled_stream_remount_support() -> None:
    """The shipped bundle should include stalled-stream remount recovery."""
    bundle = _read(BUNDLE)

    assert "data-stream-epoch" in bundle
    assert "_streamEpoch" in bundle
