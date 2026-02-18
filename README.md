# Camera Gestures

Control your smart home with hand gestures detected through your webcam.

Camera Gestures uses MediaPipe hand tracking to recognize hand poses in real time and map them to actions — supporting Philips Hue lights and Tuya infrared AC devices. Hold a closed fist to enter command mode, then make a gesture to trigger a command.

## How it works

1. **Wake gesture** — Hold a closed fist (pointing up) for 1 second to enter command mode
2. **Visual feedback** — Your Hue lights fade to blue to confirm you're in command mode
3. **Command gesture** — Hold a recognized gesture for 1 second to execute the mapped command
4. **Timeout** — If no command is detected within 5 seconds, the system returns to idle and lights restore to their previous state

### State machine

```
IDLE ──[closed fist held X seconds]──> COMMAND_MODE ──[gesture held X seconds]──> RUNNING_COMMAND ──> IDLE
                                      │
                                      └──[X seconds timeout]──> IDLE
```

All timeout values are set in `config.yaml`.

### Recognized gestures

Gestures are identified by which fingers are extended. A closed fist is the wake gesture that enters command mode. Any combination of extended fingers produces a bindable name, for example:

- `fingers_extended:index` — index finger only
- `fingers_extended:thumb+pinky` — thumb and pinky

Gesture-to-command bindings are defined entirely in `gestures.yaml` — no code changes needed.

## Setup

### Prerequisites

- Python 3.10+
- A webcam
- (Optional) Philips Hue bridge on the same network
- (Optional) Tuya IoT Platform account with infrared AC devices

### Installation

```bash
git clone https://github.com/gabrielricci/camera-gestures.git
cd camera-gestures
pip install -r requirements.txt
```

Download the MediaPipe hand landmark model:

```bash
wget -q https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

Copy the sample gesture bindings and adjust to your needs:

```bash
cp gestures.yaml.sample gestures.yaml
```

### Configure Hue (optional)

```bash
python main.py configure hue
```

This will:
1. Auto-discover your Hue bridge IP via the Philips N-UPnP API
2. Prompt you to press the physical button on the bridge
3. List all lights with their IDs
4. Save the bridge IP, device list, and enable the integration in `integrations.yaml`

To refresh the device list after adding new lights, run the command again.

### Configure Tuya (optional)

```bash
python main.py configure tuya
```

This will:
1. Prompt for your Tuya IoT Platform API key, secret, and region
2. Fetch all devices registered to your account
3. Auto-discover IR AC keys for infrared AC devices
4. Save device IDs, keys, and credentials to `integrations.yaml`

To refresh the device list, run the command again.

## Usage

```bash
python main.py start              # Start the gesture listener
python main.py configure hue      # First-time Hue bridge setup
python main.py configure tuya     # First-time Tuya setup
python main.py help               # Show help
```

Press `q` in the OpenCV window to quit, or `Ctrl+C` if GUI is disabled.

## Configuration

### `config.yaml`

General application settings:

```yaml
camera_index: 0                        # Camera device index
frame_width: 640                       # Capture resolution
frame_height: 480
gui_enabled: true                      # Show the OpenCV preview window

wake_hold_seconds: 1.0                 # How long to hold the wake gesture
command_hold_seconds: 1.0              # How long to hold a command gesture
command_timeout_seconds: 5.0           # Command mode timeout
command_debounce_seconds: 2.0          # Minimum time between commands

mediapipe_max_hands: 1
mediapipe_min_detection_confidence: 0.7
mediapipe_min_tracking_confidence: 0.5
```

### `integrations.yaml`

Managed automatically by the `configure` commands — do not edit by hand. You can inspect it to see which devices were discovered and re-run `configure` to refresh the list.

### `gestures.yaml`

The main configuration file. Contains two root keys: `hooks` and `gestures`. Adding or changing a binding requires no code changes — just edit this file and restart.

```yaml
hooks:
  - hook: ConsoleHook

  - hook: HueHook
    integration: hue
    params:
      light_ids: [5, 6]   # lights to control during command mode
      hue: 46920           # hue value for command mode indicator (blue)
      sat: 254             # saturation
      bri: 100             # brightness
      transition: 2        # transition time in units of 100ms

  - hook: OverlayHook     # draws a green border on the preview window

gestures:
  fingers_extended:index:
    command: HueTurnOnLights
    integration: hue
    params:
      light_ids: [5, 6]
      color:
        hue: 14922
        sat: 144
        bri: 254
        transitiontime: 20

  fingers_extended:thumb+pinky:
    command: TuyaPressKeyInfraredAC
    integration: tuya
    params:
      device: ar_da_sala
      key: PowerOn
```

Both sections support an `integration` field — entries whose integration is disabled are skipped with a printed warning. The `params` dict is passed as-is to the command or hook constructor; no strict schema is enforced.

## Architecture

### Key patterns

- **Hooks** react to lifecycle events (`on_enter_command_mode`, `on_exit_command_mode`, `on_frame`) without modifying core logic
- **Event bus** (`bus.py`) handles cross-cutting concerns — commands emit `lights_changed` so the Hue hook knows which lights to skip when restoring state
- **Service registry** (`context.py`) shares expensive resources (bridge connections, cloud clients) across hooks and commands without passing them through every layer
- **Integrations package** (`integrations/`) isolates all vendor-specific logic — `hue.py` and `tuya.py` own their own initialization and are the only files that know how to connect to their respective services

### Adding a new gesture binding

Edit the `gestures:` section of `gestures.yaml` — no Python changes needed:

```yaml
gestures:
  fingers_extended:thumb+middle:
    command: HueTurnOnLights
    integration: hue
    params:
      light_ids: [3]
```

### Adding a new command

1. Create a class with an `execute()` method in `commands/`
2. Register it in `commands/registry.py`'s `COMMAND_CLASSES` dict
3. Reference it by name in `gestures.yaml`

### Adding a new hook

1. Create a class with `__init__(self, params: dict)`, `on_enter_command_mode()`, `on_exit_command_mode()`, and `on_frame()` in `hooks/`
2. Register it in `hooks/__init__.py`'s `HOOK_CLASSES` dict
3. Add it to the `hooks:` section of `gestures.yaml`

## Roadmap

- **Multi-hand recognition** — detect and act on gestures from both hands simultaneously, enabling two-handed combos as distinct bindings
- **Dynamic/motion gestures** — recognize movement patterns over time (e.g. rotating a closed fist clockwise to raise volume, like the BMW X5 iDrive wheel) rather than only static poses
- **Left/right hand differentiation** — treat the same gesture differently depending on which hand performs it, effectively doubling the available binding space

## License

MIT
