import numpy as np


class ConsoleHook:
    def on_enter_command_mode(self) -> None:
        pass

    def on_exit_command_mode(self) -> None:
        pass

    def on_frame(self, frame: np.ndarray, in_command_mode: bool) -> None:
        pass
