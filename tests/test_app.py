"""Smoke tests for application wiring (requires PySide6)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from solar_sim.app import MainWindow, load_app_icon
from solar_sim.ui_canvas import SimulationCanvas
from solar_sim.ui_controls import ControlPanel


def _qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_load_app_icon_returns_icon_for_packaged_asset() -> None:
    """Saturn SVG should exist and load_app_icon should return a QIcon."""
    assets_dir = Path(__file__).resolve().parent.parent / "src" / "solar_sim" / "assets"
    svg_path = assets_dir / "saturn.svg"
    assert svg_path.is_file()

    icon = load_app_icon()
    assert isinstance(icon, QIcon)
    assert not icon.isNull()


def test_main_window_builds_default_system_and_settings() -> None:
    """MainWindow should construct a default solar system and settings."""
    _ = _qapp()
    window = MainWindow()
    try:
        assert window.settings.projection_mode == "perspective"
        assert len(window.system.bodies) == 10
        names = {b.name for b in window.system.bodies}
        assert names == {
            "Sun",
            "Mercury",
            "Venus",
            "Earth",
            "Moon",
            "Mars",
            "Jupiter",
            "Saturn",
            "Uranus",
            "Neptune",
        }
        assert window.findChild(ControlPanel) is not None
        assert window.findChild(SimulationCanvas) is not None
    finally:
        window.close()
