"""Tuya device communication via tinytuya Cloud API."""

from __future__ import annotations

import tinytuya

import context
import integrations


def init() -> None:
    """Connect to Tuya Cloud and register it in context."""
    cfg = integrations.get("tuya")
    cloud = get_cloud(
        cfg["api_key"],
        cfg["api_secret"],
        cfg.get("api_region", "us"),
    )
    context.register("tuya_cloud", cloud)
    print("[tuya] Connected to Tuya Cloud")


def get_cloud(api_key: str, api_secret: str, api_region: str = "us") -> tinytuya.Cloud:
    """Return a connected tinytuya Cloud instance."""
    cloud = tinytuya.Cloud(
        apiRegion=api_region,
        apiKey=api_key,
        apiSecret=api_secret,
    )
    return cloud


def list_devices(cloud: tinytuya.Cloud) -> list[dict]:
    """Fetch all devices from the Tuya Cloud account."""
    return cloud.getdevices()


def request_ir_ac_keys(cloud: tinytuya.Cloud, gateway_id: str, device_id: str) -> dict:
    """Fetch IR AC keys directly by IDs, without relying on saved integrations config.

    Use this during initial configuration, before devices have been persisted.
    For runtime use after configuration, prefer get_ir_ac_keys() which resolves
    IDs from the saved integrations config by device name.
    """
    return cloud.cloudrequest(
        f"/v2.0/infrareds/{gateway_id}/remotes/{device_id}/keys", "GET"
    )


def get_ir_ac_keys(cloud: tinytuya.Cloud, device_name: str) -> dict:
    """Fetch IR AC keys for a named device using the saved integrations config.

    Use this at runtime after configuration is complete. For use during
    initial setup before devices are saved, use request_ir_ac_keys() instead.
    """
    device = integrations.get("tuya").get("devices", {}).get(device_name, None)
    if not device:
        print(f"[tuya] Device {device_name} does not exist!")
        return {}

    if device.get("type") == "infrared_ac":
        gateway_id = device["gateway_id"]
        device_id = device["id"]

        return cloud.cloudrequest(
            f"/v2.0/infrareds/{gateway_id}/remotes/{device_id}/keys", "GET"
        )

    else:
        return {}


def press_key_ir_ac(cloud: tinytuya.Cloud, device_name: str, key: str) -> bool:
    """Send a key press to an infrared AC device via Cloud API."""
    device = integrations.get("tuya").get("devices", {}).get(device_name, None)
    if not device:
        print(f"[tuya] Device {device_name} does not exist!")
        return False

    if device.get("type") == "infrared_ac":
        gateway_id = device["gateway_id"]
        device_id = device["id"]

        result = cloud.cloudrequest(
            f"/v2.0/infrareds/{gateway_id}/remotes/{device_id}/command",
            "POST",
            {"key": key, "categoryId": device["category_id"], "remoteIndex": device["remote_index"]},
        )

        print(f"[tuya] Device {device_name} key '{key}' sent: {result}")
        return True
    else:
        print(f"[tuya] Device {device_name} is NOT an infrared AC")
        return False


def send_ir_command(cloud: tinytuya.Cloud, device_name: str, ir_code: str) -> None:
    """Send a learned IR code via an IR blaster device."""
    device = integrations.get("tuya").get("devices", {}).get(device_name, None)
    if not device:
        print(f"[tuya] Device {device_name} does not exist!")
        return

    commands = {"commands": [{"code": "201", "value": ir_code}]}
    result = cloud.sendcommand(device["id"], commands)
    print(f"[tuya] IR command sent: {result}")


def get_status(cloud: tinytuya.Cloud, device_name: str) -> dict:
    """Return the current device state from Cloud."""
    device = integrations.get("tuya").get("devices", {}).get(device_name, None)
    if not device:
        print(f"[tuya] Device {device_name} does not exist!")
        return {}

    return cloud.getstatus(device["id"])
