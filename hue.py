"""Philips Hue bridge communication."""

from __future__ import annotations

import requests
from phue import Bridge

import integrations

NUPNP_URL = "https://discovery.meethue.com/"
_DEFAULT_IP = "0.0.0.0"


def discover_bridge_ip() -> str:
    """Find the bridge IP via Philips N-UPnP discovery."""
    print("[hue] Discovering bridge on local network...")
    resp = requests.get(NUPNP_URL, timeout=10)
    resp.raise_for_status()
    bridges = resp.json()
    if not bridges:
        raise RuntimeError(
            "No Hue bridge found. Make sure the bridge is powered on "
            "and connected to the same network."
        )
    ip = bridges[0]["internalipaddress"]
    print(f"[hue] Found bridge at {ip}")
    return ip


def _resolve_ip() -> str:
    """Return the bridge IP from integrations.yaml, discovering if needed."""
    cfg = integrations.get("hue")
    ip = cfg.get("bridge_ip", _DEFAULT_IP)
    if ip == _DEFAULT_IP:
        ip = discover_bridge_ip()
        integrations.update("hue", bridge_ip=ip)
    return ip


def get_bridge(ip: str | None = None) -> Bridge:
    """Return a connected Bridge instance.

    On the very first call the user must press the physical button on the
    bridge within 30 seconds.  After that, credentials are cached in
    ``~/.phue`` and reconnection is automatic.
    """
    if ip is None:
        ip = _resolve_ip()
    print(
        "[hue] Connecting to bridge... "
        "(press the bridge button NOW if this is the first time)"
    )
    bridge = Bridge(ip)
    bridge.connect()
    print("[hue] Connected!")
    return bridge


def list_lights(bridge: Bridge) -> list[dict]:
    """Print and return every light registered on the bridge."""
    lights = bridge.get_light_objects("id")
    result = []
    for light_id, light in lights.items():
        info = {"id": light_id, "name": light.name, "on": light.on}
        result.append(info)
        status = "ON" if light.on else "OFF"
        print(f"  [{light_id}] {light.name}: {status}")
    return result


def turn_on(bridge: Bridge, lights: list) -> None:
    all_lights = bridge.get_light_objects("id")
    for light_id in lights:
        if light_id in all_lights:
            light = all_lights[light_id]
            light.on = True


def turn_off(bridge: Bridge, lights: list) -> None:
    all_lights = bridge.get_light_objects("id")
    for light_id in lights:
        if light_id in all_lights:
            light = all_lights[light_id]
            light.on = False


def set_color(bridge: Bridge, lights: list, color: object) -> None:
    for light_id in lights:
        bridge.set_light(light_id, color)


def toggle_light(bridge: Bridge, lights: list) -> None:
    all_lights = bridge.get_light_objects("id")
    for light_id in lights:
        if light_id in all_lights:
            light = all_lights[light_id]
            light.on = not light.on


def toggle_all(bridge: Bridge) -> None:
    """Toggle every light: if any are on turn all off, otherwise turn all on."""
    lights = bridge.get_light_objects("id")
    any_on = any(light.on for light in lights.values())
    new_state = not any_on
    for light in lights.values():
        light.on = new_state
    label = "ON" if new_state else "OFF"
    print(f"[hue] All lights turned {label}")
