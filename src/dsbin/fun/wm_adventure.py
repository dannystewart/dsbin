from __future__ import annotations

import time

from blessed import Terminal
from polykit.cli import handle_interrupt


@handle_interrupt()
def walking_man_adventure() -> None:
    """A simple text-based adventure game where a player can walk around and interact with items."""
    term = Terminal()

    # Game state
    player_x, player_y = term.width // 2, term.height // 2  # Start in the middle
    player_facing_right = True
    game_running = True

    # Clear the screen and hide cursor
    print(term.clear + term.hide_cursor)

    try:
        with term.cbreak(), term.fullscreen():
            while game_running:
                # Handle input (non-blocking)
                key = term.inkey(timeout=0.05)

                if key == "q":
                    game_running = False
                elif key.name == "KEY_RIGHT":
                    player_x = min(player_x + 1, term.width - 10)  # Prevent going off-screen
                    player_facing_right = True
                elif key.name == "KEY_LEFT":
                    player_x = max(player_x - 1, 0)  # Prevent going off-screen
                    player_facing_right = False
                elif key.name == "KEY_UP":
                    player_y = max(player_y - 1, 1)  # Prevent going off-screen
                elif key.name == "KEY_DOWN":
                    player_y = min(player_y + 1, term.height - 2)  # Prevent going off-screen

                # Create a buffer for double-buffering to reduce flickering
                buffer = []

                # Draw border
                buffer.extend((
                    term.home + term.clear,
                    term.move_xy(0, 0) + "+" + "-" * (term.width - 2) + "+",
                ))
                buffer.extend(
                    term.move_xy(0, y) + "|" + " " * (term.width - 2) + "|"
                    for y in range(1, term.height - 1)
                )
                buffer.append(term.move_xy(0, term.height - 1) + "+" + "-" * (term.width - 2) + "+")

                # Draw title, controls help, and set player character
                player_char = " (>'-')>" if player_facing_right else "<('-'<) "

                buffer.extend([
                    term.move_xy((term.width - 23) // 2, 1)
                    + term.bold
                    + "WALKING MAN ADVENTURE"
                    + term.normal,
                    term.move_xy(2, term.height - 2) + "Controls: Arrow Keys to move, Q to quit",
                ])

                # Add player and items using a single extend call for better performance
                buffer.extend([
                    term.move_xy(player_x, player_y) + term.cyan(player_char),
                    term.move_xy(15, 10) + term.yellow("🌟"),
                    term.move_xy(30, 15) + term.green("🌵"),
                    term.move_xy(50, 8) + term.red("🍎"),
                    term.move_xy(70, 12) + term.magenta("🔮"),
                    term.move_xy(2, 2) + f"Position: ({player_x}, {player_y})",
                ])

                # Render the buffer all at once (reduces flickering)
                print("".join(buffer), end="", flush=True)

                time.sleep(0.01)  # Frame rate

    finally:  # Make sure to restore terminal state if the game crashes
        print(term.normal_cursor + term.normal)


if __name__ == "__main__":
    walking_man_adventure()
