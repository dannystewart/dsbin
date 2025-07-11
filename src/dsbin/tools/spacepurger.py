"""Force macOS to purge cached files by filling disk space.

This script creates temporary files to fill up disk space to a specified target (with safety
margins), triggering macOS to purge cached files like iCloud Drive, system caches, etc.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
from pathlib import Path

from polykit import PolyArgs
from polykit.cli import handle_interrupt
from polykit.text import print_color


class SpacePurger:
    """Manages disk space filling to trigger macOS cache purging."""

    def __init__(self):
        """Initialize SpacePurger with smart defaults."""
        self.safety_margin_bytes: int = int(10.0 * 1024 * 1024 * 1024)
        self.chunk_size_bytes: int = 100 * 1024 * 1024
        self.temp_files: list[Path] = []
        self.temp_dir: str | None = None
        self.total_bytes_written: int = 0
        self.start_free_space: int = 0

    def create_temp_file(self, size_bytes: int, file_num: int) -> str:
        """Create a temporary file of specified size."""
        if not self.temp_dir:
            self.temp_dir = self.get_temp_directory()

        file_path = Path(self.temp_dir) / f"temp_file_{file_num:04d}.dat"

        # Create file with random data to prevent compression
        with file_path.open("wb") as f:
            remaining = size_bytes
            bytes_written_this_file = 0
            while remaining > 0:
                chunk_size = min(self.chunk_size_bytes, remaining)
                # Use os.urandom for truly random data that won't compress well
                f.write(os.urandom(chunk_size))
                remaining -= chunk_size
                bytes_written_this_file += chunk_size

        self.temp_files.append(file_path)
        self.total_bytes_written += size_bytes
        return str(file_path)

    def clear_screen_and_show_header(self, title: str) -> None:
        """Clear screen and show a clean header."""
        print("\033[2J\033[H", end="")  # Clear screen and move cursor to top
        print_color("═" * 50, "cyan")
        print_color(f"  {title}  ", "cyan")
        print_color("═" * 50, "cyan")

    def show_live_stats(self, total: int, used: int, free: int, progress_info: str = "") -> None:
        """Show live updating stats without scrolling."""
        print_color("\nDisk Usage:", "blue")
        print_color(f"   Total: {self.format_gb(total)}", "white")
        print_color(
            f"   Used:  {self.format_gb(used)} ({self.format_percentage(used / total * 100)})",
            "white",
        )
        print_color(
            f"   Free:  {self.format_gb(free)} ({self.format_percentage(free / total * 100)})",
            "white",
        )

        if self.total_bytes_written > 0:
            print_color(f"   Written so far: {self.format_gb(self.total_bytes_written)}", "green")
            if self.start_free_space > 0:
                space_change = self.start_free_space - free
                net_change = space_change - self.total_bytes_written
                if abs(net_change) > 0.1 * 1024 * 1024 * 1024:  # Only show if > 0.1GB
                    print_color(f"   Net change: {self.format_gb(net_change)}", "magenta")

        if progress_info:
            print_color(f"\n{progress_info}", "yellow")

    def show_progress_bar(self, current: int, target: int, width: int = 40) -> str:
        """Create a visual progress bar."""
        if target <= 0:
            return "[" + "=" * width + "]"

        progress = min(1.0, current / target)
        filled = int(progress * width)
        bar = "█" * filled + "░" * (width - filled)
        percentage = progress * 100
        return f"[{bar}] {self.format_percentage(percentage)}"

    def show_fill_header(
        self,
        target_free_bytes: int,
        max_duration_minutes: int,
        space_to_fill_total: int,
        progress_bar: str = "",
    ) -> None:
        """Show the header information for the fill operation."""
        self.clear_screen_and_show_header("Filling Disk")
        print_color(f"Filling until {self.format_gb(target_free_bytes)} free space remains", "blue")
        print_color(f"Maximum duration: {max_duration_minutes} minutes", "blue")
        print_color(f"Total space to be filled: {self.format_gb(space_to_fill_total)}", "yellow")
        if progress_bar:
            print_color(f"\nProgress: {progress_bar}", "green")

    @handle_interrupt(exit_code=0)
    def fill_to_target(self, fill_until_gb: float, max_duration_minutes: int = 30) -> bool:
        """Fill disk space until target free space remains.

        Args:
            fill_until_gb: Fill disk until this much free space remains (GB).
            max_duration_minutes: Maximum time to run before stopping.

        Returns:
            True if target was reached, False otherwise.
        """
        target_free_bytes = int(fill_until_gb * 1024 * 1024 * 1024)
        start_time = time.time()
        max_duration_seconds = max_duration_minutes * 60

        # Ensure target is above safety margin
        if target_free_bytes < self.safety_margin_bytes:
            print_color(
                f"ERROR: Target free space ({self.format_gb(target_free_bytes)}) is below safety margin "
                f"({self.format_gb(self.safety_margin_bytes)})",
                "red",
            )
            return False

        # Store initial state
        total, used, initial_free = self.get_disk_usage()
        self.start_free_space = initial_free
        space_to_fill_total = initial_free - target_free_bytes

        # Show initial header
        self.show_fill_header(target_free_bytes, max_duration_minutes, space_to_fill_total)

        file_counter = 0
        last_update_time = start_time

        try:
            while True:
                # Check elapsed time
                elapsed = time.time() - start_time
                if elapsed > max_duration_seconds:
                    print_color(
                        f"\nReached maximum duration ({max_duration_minutes} minutes)", "yellow"
                    )
                    break

                # Get current disk usage
                total, used, free = self.get_disk_usage()

                # Only update display every 3 seconds to avoid flashing
                current_time = time.time()
                if current_time - last_update_time >= 3.0:
                    # Show current status with progress
                    remaining_to_fill = free - target_free_bytes
                    progress_bar = self.show_progress_bar(
                        space_to_fill_total - remaining_to_fill, space_to_fill_total
                    )

                    # Update display with progress
                    self.show_fill_header(
                        target_free_bytes, max_duration_minutes, space_to_fill_total, progress_bar
                    )
                    self.show_live_stats(total, used, free)
                    last_update_time = current_time

                # Check if we've reached our target
                if free <= target_free_bytes:
                    print_color(
                        f"\nTarget reached! Free space is now {self.format_gb(free)}",
                        "green",
                    )
                    return True

                # Calculate how much space we need to fill
                space_to_fill = free - target_free_bytes

                # Don't fill more than our chunk size at once
                fill_size = min(space_to_fill, self.chunk_size_bytes)

                # Safety check - ensure we don't go below safety margin
                if free - fill_size < self.safety_margin_bytes:
                    print_color(
                        "Safety margin reached. Stopping to prevent system instability.", "red"
                    )
                    print_color(f"Current free space: {self.format_gb(free)}", "red")
                    break

                # Create the temporary file
                self.create_temp_file(fill_size, file_counter)
                file_counter += 1

                # Brief pause to allow system to respond
                time.sleep(1)

        except Exception as e:
            print_color(f"\nError during operation: {e}", "red")
            return False

        return False

    @handle_interrupt(exit_code=0)
    def monitor_space_recovery(self, check_interval_seconds: int = 30, max_wait_minutes: int = 60):
        """Monitor disk space to see if macOS is purging cached files.

        Args:
            check_interval_seconds: How often to check disk space.
            max_wait_minutes: Maximum time to monitor.
        """
        self.clear_screen_and_show_header("Monitoring Space Recovery")
        print_color(f"Monitoring space recovery for up to {max_wait_minutes} minutes...", "green")
        print_color("(Press Ctrl+C to stop monitoring)", "yellow")

        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        _, _, initial_free = self.get_disk_usage()
        max_recovered = 0
        check_count = 0

        print_color(f"Initial free space: {self.format_gb(initial_free)}", "blue")

        while time.time() - start_time < max_wait_seconds:
            time.sleep(check_interval_seconds)
            check_count += 1

            _, _, free = self.get_disk_usage()
            space_recovered = free - initial_free
            max_recovered = max(max_recovered, space_recovered)

            elapsed_minutes = (time.time() - start_time) / 60

            # Create a simple timeline indicator
            timeline = "●" * min(check_count, 20) + "○" * max(0, 20 - check_count)

            self.clear_screen_and_show_header("Monitoring Space Recovery")
            print_color(
                f"Monitoring space recovery for up to {max_wait_minutes} minutes...", "green"
            )
            print_color("(Press Ctrl+C to stop monitoring)", "yellow")
            print_color(f"Check #{check_count:2d} ({elapsed_minutes:.1f}m) [{timeline}]", "cyan")
            self.show_live_stats(_, _, free)

            if space_recovered > 0:
                print_color(f"Recovered: {self.format_gb(space_recovered)} ✨", "green")
                print_color("macOS is purging cached files!", "green")
            elif space_recovered < 0:
                print_color(f"Used: {self.format_gb(-space_recovered)}", "red")
            else:
                print_color("No change detected yet...", "yellow")

        # Final summary
        self.clear_screen_and_show_header("Monitoring Summary")
        print_color("MONITORING SUMMARY", "cyan")
        print_color("═" * 60, "cyan")
        print_color(f"Total monitoring time: {max_wait_minutes} minutes", "blue")
        print_color(f"Total checks performed: {check_count}", "blue")
        print_color(
            f"Maximum space recovered: {self.format_gb(max_recovered)}",
            "green" if max_recovered > 0 else "yellow",
        )

    def cleanup(self):
        """Remove all temporary files and directory."""
        if self.temp_dir is None:
            return

        self.clear_screen_and_show_header("Cleaning Up")
        print_color("\nCleaning up temporary files...", "green")

        files_removed = 0
        bytes_freed = 0
        temp_dir_path = Path(self.temp_dir)

        # Remove all files in the temp directory (not just tracked ones)
        if temp_dir_path.exists():
            try:
                for file_path in temp_dir_path.iterdir():
                    if file_path.is_file():
                        try:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            files_removed += 1
                            bytes_freed += file_size
                        except Exception as e:
                            print_color(f"Error removing {file_path.name}: {e}", "red")

                # Now remove the directory
                temp_dir_path.rmdir()
                print_color(
                    f"Cleanup complete: {files_removed} files, {self.format_gb(bytes_freed)} freed",
                    "green",
                )

            except Exception as e:
                print_color(f"Error during cleanup: {e}", "red")
                # Try to list what's left in the directory for debugging
                try:
                    remaining_files = list(temp_dir_path.iterdir())
                    if remaining_files:
                        print_color(
                            f"{len(remaining_files)} files remain in {self.temp_dir}", "yellow"
                        )
                except Exception:
                    pass

        self.temp_files.clear()
        self.temp_dir = None

    @staticmethod
    def get_disk_usage(path: str = "/") -> tuple[int, int, int]:
        """Get disk usage statistics for the given path."""
        statvfs = os.statvfs(path)
        total = statvfs.f_frsize * statvfs.f_blocks
        free = statvfs.f_frsize * statvfs.f_bavail
        used = total - free
        return total, used, free

    @staticmethod
    def get_temp_directory() -> str:
        """Create a temporary directory for our files."""
        temp_dir = tempfile.mkdtemp(prefix="spacepurger_")
        print_color(f"Created temporary directory: {temp_dir}", "green")
        return temp_dir

    def format_gb(self, bytes_val: int) -> str:
        """Format bytes as GB, hiding .0 for round numbers."""
        gb = bytes_val / (1024 * 1024 * 1024)
        if gb == int(gb):
            return f"{int(gb)} GB"
        return f"{gb:.1f} GB"

    def format_percentage(self, value: float) -> str:
        """Format percentage, hiding .0 for round numbers."""
        if value == int(value):
            return f"{int(value)}%"
        return f"{value:.1f}%"


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = PolyArgs(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    Examples:
    # Reduce free space to 2 GB to trigger aggressive purging (with 10 GB safety margin)
        spacepurger --fill-until 2

    # Quick test - reduce to 1 GB free space with 30-minute limit
        spacepurger --fill-until 1 --max-minutes 30

    # Monitor space recovery after manual cleanup
        spacepurger --monitor-only

    Note: This script REDUCES free space by creating temporary files to trigger
    macOS cache purging. It cannot increase free space beyond what you currently have.
""",
    )
    parser.add_argument(
        "--fill-until",
        "-t",
        type=float,
        default=1,
        help="Fill disk until this much free space remains in GB (default: 1)",
    )
    parser.add_argument(
        "--max-duration",
        "-d",
        type=int,
        default=30,
        help="Maximum duration in minutes (default: 30)",
    )
    parser.add_argument(
        "--monitor-only",
        "-m",
        action="store_true",
        help="Only monitor space recovery, don't create files",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't automatically cleanup temp files (for testing)",
    )
    args = parser.parse_args()

    # Validate arguments
    if args.fill_until < 0.1:
        print_color("ERROR: Target free space must be at least 0.1GB", "red")
        sys.exit(1)

    return args


@handle_interrupt(exit_code=0)
def main():
    """Main function to handle command line arguments and run the space purger."""
    args = parse_args()
    purger = SpacePurger()

    try:
        if args.monitor_only:  # Just monitor space recovery
            purger.monitor_space_recovery()
        else:  # Show initial disk state
            total, used, free = purger.get_disk_usage()
            purger.clear_screen_and_show_header("Initial Disk State")
            purger.show_live_stats(total, used, free, "Initial disk state")

            target_free_bytes = args.fill_until * 1024 * 1024 * 1024

            # Check if target is achievable
            if target_free_bytes > free:
                print_color(
                    f"\nCannot achieve target! You want {purger.format_gb(target_free_bytes)} free "
                    f"but only have {purger.format_gb(free)} free.",
                    "red",
                )
                print_color(
                    "This script reduces free space to trigger macOS cache purging. "
                    "It cannot create more free space than you currently have.",
                    "yellow",
                )
                sys.exit(1)

            # Check if we even need to do anything
            if free <= target_free_bytes + purger.safety_margin_bytes:
                print_color(
                    f"\nAlready close to target free space ({purger.format_gb(target_free_bytes)})!",
                    "green",
                )
                print_color(
                    f"Current free space ({purger.format_gb(free)}) is within safety margin "
                    f"of target ({purger.format_gb(target_free_bytes)} + {purger.format_gb(purger.safety_margin_bytes)} safety).",
                    "blue",
                )
                sys.exit(0)

            # Fill disk space
            success = purger.fill_to_target(args.fill_until, args.max_duration)

            if success:
                print_color("\nSuccessfully reached target free space!", "green")
                print_color("macOS should now start purging cached files...", "green")

                # Monitor for space recovery
                purger.monitor_space_recovery()
            else:
                print_color(
                    "\nDid not reach target, but may have triggered some purging.", "yellow"
                )

    finally:
        if not args.no_cleanup:
            purger.cleanup()
        else:
            print_color(f"\nTemporary files left in: {purger.temp_dir}", "red")
            print_color("Be sure to clean them up manually!", "red")


if __name__ == "__main__":
    main()
