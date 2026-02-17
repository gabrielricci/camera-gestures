"""Camera-based gesture control system.

Usage:
    python main.py start             Start the gesture listener
    python main.py configure hue     Discover Hue bridge and list lights
    python main.py help              Show this help message
"""

import sys

from modes import help as help_mode, start, configure


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] == "help":
        help_mode.run()
        return

    mode = args[0]

    if mode == "start":
        start.run()
    elif mode == "configure":
        if len(args) < 2:
            print("Error: 'configure' requires an integration name")
            print("Usage: python main.py configure <name>")
            print("Supported integrations: hue")
            sys.exit(1)
        configure.run(args[1])
    else:
        print(f"Error: unknown mode '{mode}'")
        help_mode.run()
        sys.exit(1)


if __name__ == "__main__":
    main()
