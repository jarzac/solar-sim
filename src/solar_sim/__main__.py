"""CLI entrypoint for the solar simulation app."""

from __future__ import annotations

import sys

from solar_sim.app import run


def main() -> int:
    """Run app and return the GUI event loop status code."""
    return run()


if __name__ == "__main__":
    sys.exit(main())
