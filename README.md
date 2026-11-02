# statemachine

[![CI](https://github.com/BoogeyCodes/statemachine/actions/workflows/ci.yml/badge.svg)](https://github.com/BoogeyCodes/statemachine/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB)
![No dependencies](https://img.shields.io/badge/dependencies-none-success)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

A small, dependency-free finite state machine for Python. Declare states and the transitions between
them, then fire events; the machine moves state, checking guards and running callbacks along the way.

```python
from statemachine import StateMachine

turnstile = StateMachine(initial="locked")
turnstile.add_transition("coin", "locked", "unlocked")
turnstile.add_transition("push", "unlocked", "locked")

turnstile.trigger("coin")   # "unlocked"
turnstile.trigger("push")   # "locked"
turnstile.trigger("push")   # raises TransitionError: no transition from "locked"
```

## Why

Any workflow with distinct states and rules about how you move between them — an order, a document, a
connection, a game — is a state machine, and writing those rules as scattered `if` statements gets
unmanageable fast. This library lets you declare the states and transitions in one place, with guards
that gate a transition and callbacks that run on it, and it refuses invalid moves instead of silently
allowing them. It is intentionally small and has no dependencies.

## Features

- **Declarative transitions**: `add_transition(trigger, source, dest)`, with `source` as a single
  state, a list, or `"*"` for any state.
- **Guards**: a transition can carry one or more predicates; it only fires if they all pass. Firing
  passes event data (`trigger`, `source`, `dest`, and any keyword arguments) to guards and callbacks.
- **Callbacks**: `on_enter`/`on_exit` per state and `action` per transition, run in the order
  exit → action → enter.
- **Introspection**: `can(trigger)` tests whether a move is allowed now; `triggers()` lists the
  events available from the current state.
- **Safe by default**: an invalid trigger raises `TransitionError` and leaves the state unchanged.

## Usage

```python
from statemachine import StateMachine

# A document workflow with a guard and callbacks.
doc = StateMachine(initial="draft")
doc.add_state("published", on_enter=lambda e: print(f"published by {e.kwargs['user']}"))
doc.add_transition("publish", "draft", "published", guard=lambda e: e.kwargs.get("approved"))
doc.add_transition("archive", "*", "archived")   # archive from any state

doc.can("publish")                 # False — not approved
doc.trigger("publish", approved=True, user="ann")   # "published", prints the message
doc.trigger("archive")             # "archived"
```

Guards and callbacks receive an `EventData` with `.trigger`, `.source`, `.dest`, `.machine` and
`.kwargs`.

## Testing

```bash
pip install -e ".[dev]"
pytest
```

Eight tests covering basic transitions, invalid-move handling, guards, callback ordering, event data,
wildcard and multi-source transitions. CI runs on Python 3.10 through 3.13.

## Project layout

```
src/statemachine/machine.py   the StateMachine, states, transitions and EventData
tests/                        pytest suite
```

## Ideas for later

- Nested/hierarchical states.
- A Graphviz export of the state diagram.
- Async guards and callbacks.

## License

MIT
