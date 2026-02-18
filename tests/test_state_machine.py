from state_machine import State, StateMachine


def test_initial_state_is_idle():
    sm = StateMachine()
    assert sm.state == State.IDLE


def test_transition_changes_state():
    sm = StateMachine()
    sm.transition_to(State.COMMAND_MODE)
    assert sm.state == State.COMMAND_MODE


def test_transition_through_all_states():
    sm = StateMachine()
    sm.transition_to(State.COMMAND_MODE)
    sm.transition_to(State.RUNNING_COMMAND)
    sm.transition_to(State.IDLE)
    assert sm.state == State.IDLE


def test_transition_to_same_state():
    sm = StateMachine()
    sm.transition_to(State.IDLE)
    assert sm.state == State.IDLE
