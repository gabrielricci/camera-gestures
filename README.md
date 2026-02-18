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

| Gesture | Name |
|---------|------|
| Closed fist (pointing up) | `closed_fist` — wake gesture (enters command mode) |
| Index finger | `fingers_extended:index` |
| Index + middle fingers | `fingers_extended:index+middle` |
| Thumb + pinky | `fingers_extended:thumb+pinky` |
| Thumb + index | `fingers_extended:thumb+index` |

Any combination of extended fingers produces a `fingers_extended:` name. Gesture-to-command bindings are defined entirely in `gestures.yaml` — no code changes needed.

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
4. Save the bridge IP and enable the integration in `integrations.yaml`

After pairing, edit `integrations.yaml` to set which lights to use for command-mode feedback:

```yaml
hue:
  enabled: true
  bridge_ip: 192.168.1.100
  office_light_ids: [5, 6]       # light IDs to flash blue during command mode
  command_mode_hue: 46920        # hue value for command mode indicator (blue)
  command_mode_transition: 2     # transition time in units of 100ms
```

### Configure Tuya (optional)

```bash
python main.py configure tuya
```

This will:
1. Prompt for your Tuya IoT Platform API key, secret, and region
2. Fetch all devices registered to your account
3. Auto-discover IR AC keys for infrared AC devices
4. Save device IDs, keys, and credentials to `integrations.yaml`

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

Per-integration settings. Integrations that are `enabled: false` are skipped at startup and their gesture bindings are ignored.

### `gestures.yaml`

Maps gesture names to commands and their parameters. Adding or changing a binding requires no code changes — just edit this file and restart.

```yaml
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

fingers_extended:index+middle:
  command: HueTurnOffLights
  integration: hue
  params:
    light_ids: [5, 6]

fingers_extended:thumb+pinky:
  command: TuyaPressKeyInfraredAC
  integration: tuya
  params:
    device: ar_da_sala
    key: PowerOn

fingers_extended:thumb+index:
  command: TuyaPressKeyInfraredAC
  integration: tuya
  params:
    device: ar_da_sala
    key: PowerOff
```

Each entry requires:
- **`command`** — the command class to instantiate
- **`integration`** — the integration tag; if that integration is disabled, the binding is skipped with a warning
- **`params`** — constructor arguments passed directly to the command class

## Architecture

### Key patterns

- **Hooks** react to lifecycle events (`on_enter_command_mode`, `on_exit_command_mode`, `on_frame`) without modifying core logic
- **Event bus** (`bus.py`) handles cross-cutting concerns — commands emit `lights_changed` so the Hue hook knows which lights to skip when restoring state
- **Service registry** (`context.py`) shares expensive resources (bridge connections, cloud clients) across hooks and commands without passing them through every layer
- **Integrations package** (`integrations/`) isolates all vendor-specific logic — `hue.py` and `tuya.py` own their own initialization and are the only files that know how to connect to their respective services

### Adding a new gesture binding

Edit `gestures.yaml` — no Python changes needed:

```yaml
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

1. Implement `on_enter_command_mode()`, `on_exit_command_mode()`, and `on_frame()`
2. Add it to the hooks list in `modes/start.py`

## License

MIT
