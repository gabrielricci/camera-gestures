class FallbackCommand:
    """Handles any gesture that doesn't have a dedicated command."""

    def __init__(self, gesture_description: str):
        self.name = "fallback"
        self._description = gesture_description

    def execute(self) -> None:
        print(f"Gesture detected: {self._description}")
