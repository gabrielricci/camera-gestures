import yaml

from hooks.console_hook import ConsoleHook
from hooks.hue_hook import HueHook
from hooks.overlay_hook import OverlayHook

HOOK_CLASSES = {
    "ConsoleHook": ConsoleHook,
    "HueHook": HueHook,
    "OverlayHook": OverlayHook,
}


def build_from_yaml(path: str, enabled_integrations: set[str]) -> list:
    with open(path) as f:
        cfg = yaml.safe_load(f)
    hooks = []
    for entry in cfg.get("hooks", []):
        hook_name = entry["hook"]
        integration = entry.get("integration")
        if integration and integration not in enabled_integrations:
            print(f"[hooks] Skipping '{hook_name}': {integration} disabled")
            continue
        hook_cls = HOOK_CLASSES.get(hook_name)
        if hook_cls is None:
            print(f"[hooks] Unknown hook '{hook_name}', skipping")
            continue
        hooks.append(hook_cls(entry.get("params", {})))
    return hooks
