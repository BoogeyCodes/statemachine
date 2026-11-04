from __future__ import annotations

import pytest

from statemachine import EventData, StateMachine, TransitionError


def turnstile() -> StateMachine:
    machine = StateMachine(initial="locked")
    machine.add_transition("coin", "locked", "unlocked")
    machine.add_transition("push", "unlocked", "locked")
    return machine


def test_basic_transitions():
    m = turnstile()
    assert m.state == "locked"
    assert m.trigger("coin") == "unlocked"
    assert m.trigger("push") == "locked"


def test_invalid_transition_raises():
    m = turnstile()
    with pytest.raises(TransitionError):
        m.trigger("push")  # cannot push while locked
    assert m.state == "locked"  # state is unchanged on failure


def test_can_and_triggers():
    m = turnstile()
    assert m.can("coin") is True
    assert m.can("push") is False
    assert m.triggers() == ["coin"]
    m.trigger("coin")
    assert m.triggers() == ["push"]


def test_guards_block_transitions():
    m = StateMachine(initial="draft")
    m.add_transition("publish", "draft", "published", guard=lambda e: e.kwargs.get("approved", False))

    assert m.can("publish") is False
    with pytest.raises(TransitionError):
        m.trigger("publish")
    assert m.trigger("publish", approved=True) == "published"


def test_callbacks_fire_in_order():
    log: list[str] = []
    m = StateMachine(initial="a")
    m.add_state("a", on_exit=lambda e: log.append("exit-a"))
    m.add_state("b", on_enter=lambda e: log.append("enter-b"))
    m.add_transition("go", "a", "b", action=lambda e: log.append("action"))

    m.trigger("go")
    assert log == ["exit-a", "action", "enter-b"]


def test_event_data_is_passed():
    captured: list[EventData] = []
    m = StateMachine(initial="a")
    m.add_transition("go", "a", "b", action=captured.append)
    m.trigger("go", user="ann")

    event = captured[0]
    assert event.trigger == "go"
    assert event.source == "a"
    assert event.dest == "b"
    assert event.kwargs == {"user": "ann"}
    assert event.machine is m


def test_wildcard_source():
    m = StateMachine(initial="a")
    m.add_transition("go", "a", "b")
    m.add_transition("reset", "*", "a")  # reset works from any state

    m.trigger("go")
    assert m.state == "b"
    assert m.trigger("reset") == "a"


def test_multiple_sources_and_first_matching_guard_wins():
    m = StateMachine(initial="red")
    m.add_transition("next", "red", "green")
    m.add_transition("next", "green", "yellow")
    m.add_transition("next", "yellow", "red")

    assert [m.trigger("next") for _ in range(3)] == ["green", "yellow", "red"]


def test_on_transition_listener_fires_for_every_move():
    seen = []
    m = StateMachine(initial="red")
    m.add_transition("next", "red", "green")
    m.add_transition("next", "green", "yellow")
    m.on_transition(lambda e: seen.append((e.source, e.dest)))

    m.trigger("next")
    m.trigger("next")
    assert seen == [("red", "green"), ("green", "yellow")]


def test_on_transition_listener_skipped_on_failed_trigger():
    seen = []
    m = StateMachine(initial="a")
    m.add_transition("go", "a", "b")
    m.on_transition(lambda e: seen.append(e.trigger))
    with pytest.raises(TransitionError):
        m.trigger("missing")
    assert seen == []
