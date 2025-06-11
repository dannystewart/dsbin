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

from polykit.cli import PolyArgs, handle_interrupt
from polykit.formatters import print_color


class SpacePurger:
    """Manages disk space filling to trigger macOS cache purging."""

    def __init__(self, safety_margin_gb: float = 5.0, chunk_size_mb: int = 100):
        """Initialize the Space Purger.

        Args:
            safety_margin_gb: Minimum free space to maintain (GB).
            chunk_size_mb: Size of each temporary file chunk (MB).
        """
        self.safety_margin_bytes: int = int(safety_margin_gb * 1024 * 1024 * 1024)
        self.chunk_size_bytes: int = int(chunk_size_mb * 1024 * 1024)
        self.temp_files: list[Path] = []
        self.temp_dir: str | None = None

    def create_temp_file(self, size_bytes: int, file_num: int) -> str:
        """Create a temporary file of specified size."""
        if not self.temp_dir:
            self.temp_dir = self.get_temp_directory()

        file_path = Path(self.temp_dir) / f"temp_file_{file_num:04d}.dat"

        # Create file with random data to prevent compression
        with file_path.open("wb") as f:
            remaining = size_bytes
            while remaining > 0:
                chunk_size = min(self.chunk_size_bytes, remaining)
                # Use os.urandom for truly random data that won't compress well
                f.write(os.urandom(chunk_size))
                remaining -= chunk_size

        self.temp_files.append(file_path)
        return str(file_path)

    @handle_interrupt()
    def fill_to_target(self, target_free_gb: float, max_duration_minutes: int = 30) -> bool:
        """Fill disk space to reach target free space.

        Args:
            target_free_gb: Target free space to maintain (GB).
            max_duration_minutes: Maximum time to run before stopping.

        Returns:
            True if target was reached, False otherwise.
        """
        target_free_bytes = int(target_free_gb * 1024 * 1024 * 1024)
        start_time = time.time()
        max_duration_seconds = max_duration_minutes * 60

        # Ensure target is above safety margin
        if target_free_bytes < self.safety_margin_bytes:
            print_color(
                f"ERROR: Target free space ({target_free_gb:.1f} GB) is below safety margin "
                f"({self.bytes_to_gb(self.safety_margin_bytes):.1f} GB)",
                "red",
            )
            return False

        print_color("\nStarting disk space fill operation...", "green")
        print_color(f"Target free space: {target_free_gb:.1f} GB", "blue")
        print_color(f"Safety margin: {self.bytes_to_gb(self.safety_margin_bytes):.1f} GB", "blue")
        print_color(f"Maximum duration: {max_duration_minutes} minutes", "blue")
        print_color(f"Chunk size: {self.chunk_size_bytes // (1024 * 1024)} MB", "blue")

        file_counter = 0

        try:
            while True:
                # Check elapsed time
                elapsed = time.time() - start_time
                if elapsed > max_duration_seconds:
                    print_color(
                        f"\nReached maximum duration ({max_duration_minutes} minutes)", "green"
                    )
                    break

                # Get current disk usage
                total, used, free = self.get_disk_usage()

                print_color("\nCurrent disk usage:", "green")
                print_color(f"  Total: {self.bytes_to_gb(total):.1f} GB", "blue")
                print_color(f"  Used:  {self.bytes_to_gb(used):.1f} GB", "blue")
                print_color(f"  Free:  {self.bytes_to_gb(free):.1f} GB", "blue")

                # Check if we've reached our target
                if free <= target_free_bytes:
                    print_color(
                        f"\nTarget reached! Free space is now {self.bytes_to_gb(free):.1f} GB",
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
                    print_color(f"Current free space: {self.bytes_to_gb(free):.1f} GB", "red")
                    break

                # Create the temporary file
                print_color(
                    f"Creating temporary file #{file_counter + 1} "
                    f"({self.bytes_to_gb(fill_size):.1f} GB)...",
                    "yellow",
                )

                file_counter += 1

                # Brief pause to allow system to respond
                time.sleep(1)

        except Exception as e:
            print_color(f"\nError during operation: {e}", "red")
            return False

        return False

    @handle_interrupt()
    def monitor_space_recovery(self, check_interval_seconds: int = 30, max_wait_minutes: int = 60):
        """Monitor disk space to see if macOS is purging cached files.

        Args:
            check_interval_seconds: How often to check disk space.
            max_wait_minutes: Maximum time to monitor.
        """
        print_color(f"\nMonitoring space recovery for up to {max_wait_minutes} minutes...", "green")
        print_color("(Press Ctrl+C to stop monitoring)", "green")

        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        _, _, initial_free = self.get_disk_usage()

        print_color(f"Initial state - Free: {self.bytes_to_gb(initial_free):.1f} GB", "blue")

        while time.time() - start_time < max_wait_seconds:
            time.sleep(check_interval_seconds)

            _, _, free = self.get_disk_usage()
            space_recovered = free - initial_free

            print_color(
                f"Free space: {self.bytes_to_gb(free):.1f} GB "
                f"(recovered: {self.bytes_to_gb(space_recovered):.1f} GB)",
                "blue",
            )

            if space_recovered > 0:
                print_color("✓ macOS appears to be purging cached files!", "green")

    def cleanup(self):
        """Remove all temporary files and directory."""
        print_color("\nCleaning up temporary files...", "green")

        for file_path in self.temp_files:
            try:
                file_path.unlink()
                print_color(f"Removed: {file_path}", "green")
            except Exception as e:
                print_color(f"Error removing {file_path}: {e}", "red")

        if self.temp_dir is not None:
            temp_dir_path = Path(self.temp_dir)
            if temp_dir_path.exists():
                try:
                    temp_dir_path.rmdir()
                    print_color(f"Removed temporary directory: {self.temp_dir}", "green")
                except Exception as e:
                    print_color(f"Error removing temp directory: {e}", "red")

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

    @staticmethod
    def bytes_to_gb(bytes_val: int) -> float:
        """Convert bytes to gigabytes."""
        return bytes_val / (1024 * 1024 * 1024)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = PolyArgs(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    Examples:
    # Fill disk to 2 GB free space with 10 GB safety margin
        spacepurger --target-free 2 --safety-margin 10

    # Quick test with 1 GB target and 30-minute limit
        spacepurger --target-free 1 --max-minutes 30

    # Monitor space recovery after manual cleanup
        spacepurger --monitor-only
""",
    )
    parser.add_argument(
        "--target-free",
        "-t",
        type=float,
        default=1,
        help="Target free space in GB (default: 1)",
    )
    parser.add_argument(
        "--safety-margin",
        "-s",
        type=float,
        default=5,
        help="Safety margin in GB to prevent system instability (default: 5)",
    )
    parser.add_argument(
        "--chunk-size",
        "-c",
        type=int,
        default=100,
        help="Size of each temporary file chunk in MB (default: 100)",
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
    if args.target_free < 0.1:
        print("ERROR: Target free space must be at least 0.1GB")
        sys.exit(1)

    if args.safety_margin < 1.0:
        print("ERROR: Safety margin must be at least 1.0GB")
        sys.exit(1)

    if args.target_free < args.safety_margin:
        print("ERROR: Target free space must be greater than safety margin")
        sys.exit(1)

    return args


@handle_interrupt()
def main():
    """Main function to handle command line arguments and run the space purger."""
    args = parse_args()
    purger = SpacePurger(safety_margin_gb=args.safety_margin, chunk_size_mb=args.chunk_size)

    try:
        if args.monitor_only:  # Just monitor space recovery
            purger.monitor_space_recovery()
        else:  # Show initial disk state
            total, used, free = purger.get_disk_usage()
            print_color("\nInitial disk state:", "blue")
            print_color(f"  Total: {purger.bytes_to_gb(total):.1f} GB", "blue")
            print_color(f"  Used:  {purger.bytes_to_gb(used):.1f} GB", "blue")
            print_color(f"  Free:  {purger.bytes_to_gb(free):.1f} GB", "blue")

            # Check if we even need to do anything
            if free <= args.target_free * 1024 * 1024 * 1024:
                print_color(
                    f"\nAlready at or below target free space ({args.target_free} GB)!", "blue"
                )
                sys.exit(0)

            # Fill disk space
            success = purger.fill_to_target(args.target_free, args.max_duration)

            if success:
                print_color("\n✓ Successfully reached target free space!", "green")
                print_color("macOS should now start purging cached files...", "green")

                # Monitor for space recovery
                purger.monitor_space_recovery()
            else:
                print_color(
                    "\n⚠ Did not reach target, but may have triggered some purging.", "yellow"
                )

    finally:
        if not args.no_cleanup:
            purger.cleanup()
        else:
            print_color(f"\nTemporary files left in: {purger.temp_dir}", "red")
            print_color("Remember to clean them up manually!", "red")


if __name__ == "__main__":
    main()
