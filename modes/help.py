"""Help mode — print usage information."""

HELP_TEXT = """\
Usage: python main.py <mode> [options]

Modes:
  start             Start the gesture listener
  configure <name>  Run first-time setup for an integration
  help              Show this help message

Integrations:
  hue               Discover Philips Hue bridge and list lights
"""


def run() -> None:
    print(HELP_TEXT)
