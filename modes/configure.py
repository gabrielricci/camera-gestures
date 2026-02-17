"""Configure mode — first-time setup for integrations."""

import sys

import integrations
from hue import get_bridge, list_lights


def run(integration: str) -> None:
    if integration == "hue":
        bridge = get_bridge()
        integrations.update("hue", enabled=True)
        print("\nLights on this bridge:")
        list_lights(bridge)
        print("\nHue integration enabled and bridge IP saved.")
    else:
        print(f"Error: unknown integration '{integration}'")
        print("Supported integrations: hue")
        sys.exit(1)
