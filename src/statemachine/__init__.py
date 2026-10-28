"""statemachine: a small, dependency-free declarative finite state machine."""

from statemachine.machine import (
    EventData,
    StateMachine,
    TransitionError,
)

__version__ = "0.1.0"
__all__ = ["StateMachine", "EventData", "TransitionError"]
