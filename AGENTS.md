# AGENTS.md

## Purpose

This repository hosts a modular Python desktop simulation of the solar system.

## Engineering Rules

- Keep simulation internals in SI units (`m`, `kg`, `s`).
- Keep UI logic separate from physics logic.
- Prefer small, single-purpose classes and methods.
- Add PEP 257 / pydoc-compatible docstrings to public modules, classes, and methods.
- Use explicit typing. Avoid optional types unless `None` is an intentional state.

## Testing

- Core components must be unit tested:
  - gravity/acceleration math
  - integration stepping behavior
  - mutable settings behavior
- Run:
  - `pytest`
  - `ruff check .`
  - `mypy src`

## Contribution Flow

1. Create focused changes.
2. Add or update tests with behavior changes.
3. Run local checks before opening a PR.
4. Update `README.md` when setup, controls, or architecture changes.

## Non-Goals

- Avoid introducing heavyweight dependencies unless they bring clear value.
- Avoid mixing rendering math and physics logic into the same class.

