from enum import Enum, auto


class State(Enum):
    IDLE = auto()
    COMMAND_MODE = auto()
    RUNNING_COMMAND = auto()


class StateMachine:
    def __init__(self):
        self._state = State.IDLE

    @property
    def state(self) -> State:
        return self._state

    def transition_to(self, new_state: State) -> None:
        old = self._state
        self._state = new_state
        print(f"[STATE] {old.name} -> {new_state.name}")
