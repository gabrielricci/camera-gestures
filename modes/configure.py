"""Configure mode — first-time setup for integrations."""

import sys

import integrations
from integrations.hue import get_bridge, list_lights
from integrations import tuya


def _configure_tuya() -> None:
    api_key = input("Tuya IoT Platform API key: ").strip()
    api_secret = input("Tuya IoT Platform API secret: ").strip()
    api_region = input("API region (us/eu/cn) [us]: ").strip() or "us"

    print("\n[tuya] Connecting to Tuya Cloud to fetch device list...")
    cloud = tuya.get_cloud(api_key, api_secret, api_region)
    cloud_devices = tuya.list_devices(cloud)

    print(f"[tuya] Found {len(cloud_devices)} device(s) in cloud account:")
    devices_cfg = {}
    for dev in cloud_devices:
        dev_id = dev.get("id", "")
        name = dev.get("name", "unknown")
        category = dev.get("category", "")
        safe_name = name.lower().replace(" ", "_")
        print(f"  - {name} (id={dev_id}, category={category})")
        entry = {"id": dev_id, "type": category}
        gateway_id = dev.get("gateway_id", "")
        if gateway_id:
            entry["gateway_id"] = gateway_id
        if category == "infrared_ac" and gateway_id:
            print(f"    Fetching IR AC keys for '{name}'...")
            keys_resp = tuya.request_ir_ac_keys(cloud, gateway_id, dev_id)
            ir_result = keys_resp.get("result", {})
            if ir_result:
                entry["category_id"] = ir_result.get("category_id")
                entry["remote_index"] = ir_result.get("remote_index")
                entry["keys"] = [k["key"] for k in ir_result.get("key_list", [])]
        devices_cfg[safe_name] = entry

    integrations.update(
        "tuya",
        enabled=True,
        api_key=api_key,
        api_secret=api_secret,
        api_region=api_region,
        devices=devices_cfg,
    )
    print("\nTuya integration enabled and devices saved.")


def run(integration: str) -> None:
    if integration == "hue":
        bridge = get_bridge()
        integrations.update("hue", enabled=True)
        print("\nLights on this bridge:")
        list_lights(bridge)
        print("\nHue integration enabled and bridge IP saved.")
    elif integration == "tuya":
        _configure_tuya()
    else:
        print(f"Error: unknown integration '{integration}'")
        print("Supported integrations: hue, tuya")
        sys.exit(1)
