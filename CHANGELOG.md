# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- `StateMachine.on_transition(callback)` — register a listener fired after every
  successful transition, for logging, metrics or persistence.

## [0.1.0]

### Added
- Declarative transitions with wildcard/multi-source, guards and enter/exit/action callbacks.
- `trigger`, `can`, `triggers` and a `TransitionError` for invalid moves.
