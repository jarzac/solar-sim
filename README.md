# Solar System Simulation (Python + PySide6)

Desktop N-body solar system simulator: Newtonian gravity and velocity–Verlet integration in SI units, with a Qt UI for runtime controls and a 2D projected view (orthographic or perspective).

The installable package name is **`solar-system-sim`** (import path **`solar_sim`**).

## Tech stack

- Python 3.12+
- PySide6 (Qt 6)
- pytest, ruff, mypy (via optional dev dependencies)

The project is written for a desktop environment (see `pyproject.toml`); CI runs tests on Linux without a display.

## Quick start

### 1. Python environment

Use any Python 3.12+ environment. Example with pyenv:

```bash
pyenv install -l
pyenv install <latest-stable-version>
pyenv virtualenv <latest-stable-version> solar-sim
pyenv local solar-sim
```

### 2. Install dependencies

From the repository root:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 3. Run the app

Either:

```bash
python -m solar_sim
```

or use the console script defined in `pyproject.toml`:

```bash
solar-sim
```

### 4. Tests and checks

Same commands as CI (`.github/workflows/ci.yml`) and `AGENTS.md`:

```bash
ruff check .
mypy src
pytest
```

If `pytest` is not on your `PATH`, use `python -m pytest`.

## Features

- **Default model**: Sun plus the eight major planets (Mercury–Neptune). Bodies use masses and radii at physical scale.
- **Initial conditions**: Heliocentric positions and velocities from time-evolved Keplerian elements. Coefficients follow the JPL document *Keplerian Elements for Approximate Positions of the Major Planets* (ecliptic/equinox of J2000). The embedded table is labeled in code as a DE440 **approximation**; the JPL sheet notes usability roughly **1800 AD–2050 AD** (see `physics.py` and the linked source comment).
- **Dynamics**: Pairwise Newtonian gravity with an adjustable multiplier; **velocity–Verlet** integration (`SolarSystem.step`).
- **UI** (`ControlPanel`): gravity multiplier (0–10); **start date** (calendar); **sim seconds per real second** (1–5,000,000; default `864_000`); checkboxes for orbit paths, planet labels, and perspective view; **Stop**/**Start**; **Restart** (rebuilds state from the current start date and settings).
- **Start date behavior**: Changing the start date updates settings immediately; **Restart** applies it by re-seeding bodies at the new epoch. The on-screen clock shows **start date + simulated elapsed time** in UTC.
- **Rendering** (`SimulationCanvas`): optional fading trails (sampled along the simulation; fade horizon tied to each body’s Keplerian period estimate), a solar-plane grid, body disks, and optional labels (Sun is never labeled). The view is **centered on the instantaneous center of mass** of all bodies (not fixed on the Sun). A small panel shows the simulation date/time.

## Camera and input (canvas)

- **Mouse wheel**: zoom (non-touchpad devices).
- **Middle mouse drag**: orbit (yaw/pitch) the camera.
- **Trackpad** (where Qt delivers the events): two-finger pan can orbit; pinch maps to zoom via native zoom gestures; some platforms also emit a **rotate** native gesture, which adjusts yaw. After a native pan/zoom/rotate gesture, matching **wheel** events from the touchpad may be ignored briefly (`0.08` s) to avoid duplicate motion.
- **Alt + scroll** (e.g. Option on macOS): treat scroll as **zoom** even on a trackpad.

Projection mode is toggled in the control panel (**Perspective view** checked → perspective; unchecked → orthographic). Implementation: `camera.py` (`CameraState.project_to_screen`).

## Repository layout

```text
.github/workflows/ci.yml   # CI: ruff, mypy, pytest
src/solar_sim/
  __main__.py                # CLI entry; delegates to app.run
  app.py                     # MainWindow, settings, system wiring
  camera.py                  # CameraState; zoom, orbit, projection
  config.py                  # SimulationSettings
  math2d.py / math3d.py      # Vector helpers
  physics.py                 # Bodies, SolarSystem, default ephemeris seeding
  ui_canvas.py               # Simulation canvas: draw, input, clock
  ui_controls.py             # Control panel and signals
  assets/saturn.svg          # Window icon (optional)
tests/
  test_camera.py
  test_config.py
  test_physics.py
  test_ui_canvas.py
AGENTS.md                    # Contributor engineering rules
AUDIT.md                     # Technical notes / audit snapshot
README.md
pyproject.toml
```

## Architecture (high level)

- **`app.MainWindow`** owns **`SimulationSettings`**, a **`SolarSystem`** from `create_default_solar_system(epoch)`, **`ControlPanel`**, and **`SimulationCanvas`**. Signals update settings and canvas run state; restart replaces the `SolarSystem` and resets the canvas.
- **`SolarSystem`** holds `CelestialBody` instances and advances them with `step`. Accelerations are mutual Newtonian gravity; the Sun is a normal massive body (not kinematically locked).
- **`SimulationCanvas`** runs a timer (~16 ms), steps the system when not paused, and paints. World positions are shifted by the system center of mass before projection so the barycenter stays near the viewport center.
- **Rendering scale** uses `settings.meters_per_pixel` with zoom from `CameraState` (`effective_meters_per_pixel`).

For coding conventions and review expectations, see **`AGENTS.md`**.

## Limitations and approximations (as implemented)

- **Ephemeris**: Initial state comes from the JPL *approximate* Keplerian element recipe, not a full numeric ephemeris (e.g. DE440 integration). Outside the documented validity window of that table, accuracy is not guaranteed.
- **Catalog**: Default system is Sun + eight planets; no moons, dwarf planets, or small bodies.
- **Visualization**: Bodies are drawn as colored circles with optional trails; this is not a 3D mesh or texture scene.
- **Perspective** is a simple screen-space scaling model (`camera.py`), not a full graphics-pipeline camera.
