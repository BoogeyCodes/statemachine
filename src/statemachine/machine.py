"""A declarative finite state machine.

Define states and the transitions between them; fire an event with :meth:`StateMachine.trigger`
and the machine moves to the destination state, running any guards and callbacks along the way.
Everything is explicit and dependency-free.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

Callback = Callable[["EventData"], None]
Guard = Callable[["EventData"], bool]

WILDCARD = "*"


class TransitionError(Exception):
    """Raised when a triggered event has no valid transition from the current state."""


@dataclass(frozen=True)
class EventData:
    """Context passed to guards and callbacks for a single transition."""

    trigger: str
    source: str
    dest: str
    machine: StateMachine
    kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class _State:
    name: str
    on_enter: list[Callback] = field(default_factory=list)
    on_exit: list[Callback] = field(default_factory=list)


@dataclass
class _Transition:
    trigger: str
    sources: frozenset[str]
    dest: str
    guards: list[Guard]
    actions: list[Callback]

    def matches(self, current: str) -> bool:
        return WILDCARD in self.sources or current in self.sources


class StateMachine:
    def __init__(self, initial: str) -> None:
        self._states: dict[str, _State] = {}
        self._transitions: list[_Transition] = []
        self._listeners: list[Callback] = []
        self._state = initial
        self.add_state(initial)

    @property
    def state(self) -> str:
        return self._state

    def on_transition(self, callback: Callback) -> StateMachine:
        """Register a callback fired after every successful transition, with the EventData.

        Unlike per-state ``on_enter``/``on_exit`` or per-transition actions, a listener sees
        *every* move — handy for logging, metrics or persisting the machine's state.
        """
        self._listeners.append(callback)
        return self

    # -- declaration ---------------------------------------------------------

    def add_state(
        self, name: str, *, on_enter: Callback | None = None, on_exit: Callback | None = None
    ) -> StateMachine:
        state = self._states.setdefault(name, _State(name))
        if on_enter:
            state.on_enter.append(on_enter)
        if on_exit:
            state.on_exit.append(on_exit)
        return self

    def add_transition(
        self,
        trigger: str,
        source: str | Iterable[str],
        dest: str,
        *,
        guard: Guard | Iterable[Guard] | None = None,
        action: Callback | Iterable[Callback] | None = None,
    ) -> StateMachine:
        sources = frozenset([source] if isinstance(source, str) else source)
        for name in sources | {dest}:
            if name != WILDCARD:
                self.add_state(name)
        self._transitions.append(
            _Transition(trigger, sources, dest, _as_list(guard), _as_list(action))
        )
        return self

    # -- runtime -------------------------------------------------------------

    def triggers(self) -> list[str]:
        """Triggers that have at least one transition whose source matches the current state."""
        seen: list[str] = []
        for t in self._transitions:
            if t.matches(self._state) and t.trigger not in seen:
                seen.append(t.trigger)
        return seen

    def can(self, trigger: str, **kwargs: Any) -> bool:
        """Whether firing ``trigger`` now would succeed (source matches and guards pass)."""
        return self._resolve(trigger, kwargs) is not None

    def trigger(self, trigger: str, **kwargs: Any) -> str:
        """Fire an event. Returns the new state, or raises :class:`TransitionError`."""
        resolved = self._resolve(trigger, kwargs)
        if resolved is None:
            raise TransitionError(
                f"no transition for trigger {trigger!r} from state {self._state!r}"
            )

        transition, event = resolved
        for callback in self._states[self._state].on_exit:
            callback(event)
        for callback in transition.actions:
            callback(event)
        self._state = transition.dest
        for callback in self._states[self._state].on_enter:
            callback(event)
        for listener in self._listeners:
            listener(event)
        return self._state

    def _resolve(self, trigger: str, kwargs: dict[str, Any]) -> tuple[_Transition, EventData] | None:
        for transition in self._transitions:
            if transition.trigger != trigger or not transition.matches(self._state):
                continue
            event = EventData(trigger, self._state, transition.dest, self, kwargs)
            if all(guard(event) for guard in transition.guards):
                return transition, event
        return None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if callable(value):
        return [value]
    return list(value)
