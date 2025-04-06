#!/usr/bin/env python3

"""Create or kill an SSH tunnel on the specified port."""

from __future__ import annotations

import getpass
import subprocess
import sys
from typing import TYPE_CHECKING

from polykit.cli import PolyArgs
from polykit.formatters import print_color
from polykit.log import PolyLog

if TYPE_CHECKING:
    import argparse

logger = PolyLog.get_logger()


def parse_arguments() -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    """Parse command-line arguments."""
    parser = PolyArgs(description="manage an SSH tunnel on a specified port", arg_width=28)
    parser.add_argument("host", type=str, help="the host for the SSH tunnel.", nargs="?")
    parser.add_argument("port", type=int, help="the port number for the SSH tunnel", nargs="?")

    parser.add_argument("-l", "--list", action="store_true", help="list all active SSH tunnels")
    parser.add_argument(
        "--kill", action="store_true", help="kill the SSH tunnel on the specified port"
    )
    parser.add_argument("--kill-all", action="store_true", help="kill all active SSH tunnels")
    parser.add_argument(
        "--local-port", type=int, help="local port number for the SSH tunnel (optional)"
    )
    parser.add_argument(
        "-u",
        "--user",
        type=str,
        default=getpass.getuser(),
        help="username for SSH tunnel (default: current user)",
    )
    return parser, parser.parse_args()


def run(command: str, show_output: bool = False) -> tuple[bool, str]:
    """Execute a shell command and optionally print the output."""
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        decoded_output = output.decode("utf-8")
        if show_output:
            print(decoded_output)
        return True, decoded_output
    except subprocess.CalledProcessError as e:
        decoded_output = e.output.decode("utf-8")
        if show_output:
            print(decoded_output)
        return False, decoded_output


def list_ssh_tunnels() -> None:
    """List currently engaged SSH tunnels with PID, start time, and command."""
    command = "ps aux | grep ssh | grep -v grep"
    success, output = run(command)
    if success:
        if tunnels := [line for line in output.split("\n") if "ssh -fNL" in line]:
            _print_tunnel_list(tunnels)
        else:
            logger.info("No active SSH tunnels found.")
    else:
        logger.error("Failed to list SSH tunnels.")


def _print_tunnel_list(tunnels: list[str]) -> None:
    """Print the list of SSH tunnels with PID, start time, and command."""
    pid_width = 8
    time_width = 13
    cmd_width = 40
    header = f"\n{'PID':<{pid_width}} {'Start Time':<{time_width}} {'Command':<{cmd_width}}"
    print_color(header, "cyan")
    print_color("-" * len(header), "cyan")
    for tunnel in tunnels:
        parts = tunnel.split()
        pid = parts[1]
        start_time = parts[8]
        command = " ".join(parts[10:])
        formatted_line = f"{pid:<{pid_width}} {start_time:<{time_width}} {command:{cmd_width}}"
        print(formatted_line)


def ensure_ssh_tunnel(
    port: int,
    kill: bool = False,
    local_port: int | None = None,
    user: str | None = None,
    host: str | None = None,
) -> None:
    """Check for an SSH tunnel on a specified port and establish or kill it.

    If local_port is specified, it will use that as the local port instead of the default port. User
    and host are also configurable for the SSH connection.

    Args:
        port: The port number for the SSH tunnel.
        kill: Whether to kill the SSH tunnel on the specified port instead of starting one.
        local_port: Local port number for the SSH tunnel.
        user: The username for the SSH tunnel.
        host: The host for the SSH tunnel.
    """
    local_port = local_port or port
    user = user or getpass.getuser()

    logger.info("Checking for existing SSH tunnel on local port %s...", local_port)

    success, output = run(f"lsof -ti:{local_port} -sTCP:LISTEN")
    if success and output.strip():
        ssh_tunnel_pid = output.strip()
        logger.info("Found existing SSH tunnel with PID: %s.", ssh_tunnel_pid)
        if kill:
            run(f"kill -9 {ssh_tunnel_pid}")
            logger.info("Existing SSH tunnel killed.")
        else:
            logger.warning(
                "SSH tunnel is already running on port %s. Use --kill to terminate it.", local_port
            )
    elif kill:
        logger.info("No existing SSH tunnel to kill on port %s.", local_port)
    else:
        logger.info("No existing SSH tunnel found on port %s. Starting now...", local_port)
        success, _ = run(f"ssh -fNL {local_port}:localhost:{port} {user}@{host}")
        if success:
            logger.info("SSH tunnel established.")
        else:
            logger.error("Failed to establish SSH tunnel. Exiting...")


def kill_all_ssh_tunnels() -> None:
    """Kill all active SSH tunnels."""
    logger.info("Killing all active SSH tunnels...")
    success, _ = run(
        "ps aux | grep ssh | grep -v grep | awk '{print $2}' | xargs kill -9", show_output=True
    )
    if success:
        logger.info("All SSH tunnels killed.")
    else:
        logger.error("Failed to kill all SSH tunnels.")


def main() -> None:
    """Perform SSH action based on user input."""
    parser, args = parse_arguments()

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(0)

    if args.list:
        list_ssh_tunnels()
    elif args.kill_all:
        kill_all_ssh_tunnels()
    else:
        if not args.host:
            logger.error("Host is required for SSH tunnel operations.")
        ensure_ssh_tunnel(args.port, args.kill, args.local_port, args.user, args.host)


if __name__ == "__main__":
    main()
