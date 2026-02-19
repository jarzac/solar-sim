# Solar System Simulation (Python + macOS Desktop)

A modular desktop app that simulates a solar system at real physical scale (SI units), with live runtime controls for gravity, time scale, orbit paths, and planet labels.

## Tech Stack

- Python 3.12+ (managed with `pyenv` and `pyenv-virtualenv`)
- PySide6 (Qt desktop UI for macOS)
- pytest (unit testing)
- ruff (linting)
- mypy (strict static typing)

## Quick Start

### 1. Install latest Python via pyenv

```bash
pyenv install -l
pyenv install <latest-stable-version>
pyenv virtualenv <latest-stable-version> solar-sim
pyenv local solar-sim
```

### 2. Install project dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 3. Run the app

```bash
python -m solar_sim
```

### 4. Run tests and checks

```bash
pytest
ruff check .
mypy src
```

## Features

- Real-scale physical values for solar-system bodies (mass, distance, radius)
- Newtonian gravity with velocity-Verlet integration
- Live controls on the left panel:
  - Gravity multiplier
  - Simulation time scaling
  - Show/hide orbit paths
  - Show/hide planet labels
- Readable labels even when bodies are visually tiny

## Project Layout

```text
src/solar_sim/
  __main__.py        # CLI entrypoint
  app.py             # Main window composition
  config.py          # Mutable simulation settings
  math2d.py          # Vector math helpers
  physics.py         # Body models + integrator + defaults
  ui_canvas.py       # Simulation rendering widget
  ui_controls.py     # Left-side controls widget
tests/
  test_config.py
  test_physics.py
AGENTS.md
README.md
pyproject.toml
```

## Design Notes

- Simulation math uses physical SI units.
- Rendering uses `meters_per_pixel` scaling, so the world remains physically meaningful while still viewable on a desktop.
- Time scale is accelerated by default (`86400` simulated seconds per real second) so orbital motion is visible.

