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
- Planet initialization from JPL Keplerian elements (inclination + eccentricity)
- Newtonian gravity with velocity-Verlet integration
- Live controls on the left panel:
  - Gravity multiplier
  - Start date (used for initial state and restart epoch)
  - Simulation time scaling
  - Show/hide orbit paths
  - Show/hide planet labels
  - Start/Stop simulation
  - Restart simulation
- Orbit trails fade over one full revolution for each planet
- Camera controls on the simulation canvas:
  - Mouse wheel to zoom in/out
  - Middle mouse drag to rotate and tilt around the sun
- A solar-plane grid box that rotates/tilts with camera movement
- View mode toggle:
  - Orthographic
  - Perspective
  - Default: Perspective enabled
- Readable labels even when bodies are visually tiny

## Project Layout

```text
src/solar_sim/
  __main__.py        # CLI entrypoint
  app.py             # Main window composition
  camera.py          # Camera interaction + projection math
  config.py          # Mutable simulation settings
  math2d.py          # Vector math helpers
  math3d.py          # 3D vector math helpers
  physics.py         # Body models + 3D integrator + element-based defaults
  ui_canvas.py       # Simulation rendering widget
  ui_controls.py     # Left-side controls widget
tests/
  test_camera.py
  test_config.py
  test_physics.py
AGENTS.md
README.md
pyproject.toml
```

## Design Notes

- Simulation math uses physical SI units.
- Initial planetary states are derived from JPL approximate orbital element tables.
- Rendering uses `meters_per_pixel` scaling, so the world remains physically meaningful while still viewable on a desktop.
- Time scale is accelerated by default (`864000` simulated seconds per real second) so orbital motion is visible.
