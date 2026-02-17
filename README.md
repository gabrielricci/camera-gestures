# Camera Gestures

Control your smart home with hand gestures detected through your webcam.

Camera Gestures uses MediaPipe hand tracking to recognize hand poses in real time and map them to actions — currently supporting Philips Hue light control. Hold a closed fist to enter command mode, then make a gesture to trigger a command.

## How it works

1. **Wake gesture** — Hold a closed fist (pointing up) for 1 second to enter command mode
2. **Visual feedback** — Your Hue lights fade to blue to confirm you're in command mode
3. **Command gesture** — Hold a recognized gesture for 1 second to execute the mapped command
4. **Timeout** — If no command is detected within 5 seconds, the system returns to idle and lights restore to their previous state

### State machine

```
IDLE ──[closed fist held 1s]──> COMMAND_MODE ──[gesture held 1s]──> RUNNING_COMMAND ──> IDLE
                                      │
                                      └──[5s timeout]──> IDLE
```

### Recognized gestures

| Gesture | Name | Default action |
|---------|------|----------------|
| Closed fist (pointing up) | `closed_fist` | Wake gesture (enters command mode) |
| Index finger extended | `fingers_extended:index` | Turn on office lights |
| Index + middle fingers | `fingers_extended:index+middle` | Turn off office lights |

Gestures are recognized from finger extension states. Any combination of extended fingers produces a `fingers_extended:` name that can be mapped to a command.

## Setup

### Prerequisites

- Python 3.10+
- A webcam
- (Optional) Philips Hue bridge on the same network

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

### Configure Hue (optional)

Run the configure command to discover your bridge and pair with it:

```bash
python main.py configure hue
```

This will:
1. Auto-discover your Hue bridge IP via the Philips N-UPnP API
2. Prompt you to press the physical button on the bridge
3. List all lights with their IDs
4. Save the bridge IP and enable the integration in `integrations.yaml`

After pairing, edit `integrations.yaml` to set which lights to use:

```yaml
hue:
  enabled: true
  bridge_ip: 192.168.1.100
  office_light_ids: [5, 6] # change it to your light IDs
  command_mode_hue: 46920
  command_mode_transition: 2
```

## Usage

```bash
python main.py start             # Start the gesture listener
python main.py configure hue     # First-time Hue bridge setup
python main.py help              # Show help
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

Per-integration settings. Currently supports Hue:

```yaml
hue:
  enabled: false
  bridge_ip: "0.0.0.0"                # Auto-discovered on first configure
  office_light_ids: [5, 6]            # Light IDs to use for feedback
  command_mode_hue: 46920             # Hue value for command mode (blue)
  command_mode_transition: 2          # Transition time (units of 100ms)
```

### Key patterns

- **Hooks** react to lifecycle events (`on_enter_command_mode`, `on_exit_command_mode`, `on_frame`) without modifying core logic
- **Event bus** (`bus.py`) handles cross-cutting concerns — commands emit `lights_changed` so the Hue hook knows which lights to skip when restoring state
- **Service registry** (`context.py`) shares expensive resources (like the Hue bridge connection) across hooks and commands without passing them through every layer
- **Integrations config** is persisted to YAML so bridge IPs and credentials survive restarts

### Adding a new command

1. Create a class with an `execute()` method in `commands/`
2. Register it in `modes/start.py`:
   ```python
   registry.register("fingers_extended:thumb+pinky", MyCommand())
   ```

### Adding a new hook

1. Implement `on_enter_command_mode()`, `on_exit_command_mode()`, and `on_frame()`
2. Add it to the hooks list in `modes/start.py`

## License

MIT
