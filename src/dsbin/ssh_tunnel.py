#!/usr/bin/env python3

"""Create or kill an SSH tunnel on the specified port."""

import argparse
import getpass
import os
import subprocess
import sys
import time

from dotenv import load_dotenv

from dsutil.text import error, info, print_colored, progress, warning

load_dotenv()

DEFAULT_SQLITE_HOST = os.getenv("DEFAULT_SQLITE_HOST")
DEFAULT_SQLITE_PORT = os.getenv("DEFAULT_SQLITE_PORT")
DEFAULT_SQLITE_PATH = os.getenv("DEFAULT_SQLITE_PATH")
DEFAULT_SQLITE_FILE = os.getenv("DEFAULT_SQLITE_FILE")


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
            info("No active SSH tunnels found.")
    else:
        error("Failed to list SSH tunnels.")


def _print_tunnel_list(tunnels: list[str]) -> None:
    """Print the list of SSH tunnels with PID, start time, and command."""
    pid_width = 8
    time_width = 13
    cmd_width = 40
    header = f"\n{'PID':<{pid_width}} {'Start Time':<{time_width}} {'Command':<{cmd_width}}"
    print_colored(header, "cyan")
    print_colored("-" * len(header), "cyan")
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
    """
    Check for an SSH tunnel on a specified port and establish or kill it. If local_port is
    specified, it will use that as the local port instead of the default port. User and host are
    also configurable for the SSH connection.

    Args:
        port: The port number for the SSH tunnel.
        kill: Whether to kill the SSH tunnel on the specified port instead of starting one.
        local_port: Local port number for the SSH tunnel.
        user: The username for the SSH tunnel.
        host: The host for the SSH tunnel.
    """
    local_port = local_port or port
    user = user or getpass.getuser()

    info(f"Checking for existing SSH tunnel on local port {local_port}...")

    success, output = run(f"lsof -ti:{local_port} -sTCP:LISTEN")
    if success and output.strip():
        ssh_tunnel_pid = output.strip()
        info(f"Found existing SSH tunnel with PID: {ssh_tunnel_pid}.")
        if kill:
            run(f"kill -9 {ssh_tunnel_pid}")
            progress("Existing SSH tunnel killed.")
        else:
            warning(f"SSH tunnel is already running on port {local_port}. Use --kill to terminate it.")
    elif kill:
        info(f"No existing SSH tunnel to kill on port {local_port}.")
    else:
        progress(f"No existing SSH tunnel found on port {local_port}. Starting now...")
        success, _ = run(f"ssh -fNL {local_port}:localhost:{port} {user}@{host}")
        if success:
            progress("SSH tunnel established.")
        else:
            error("Failed to establish SSH tunnel. Exiting...")


def kill_all_ssh_tunnels() -> None:
    """Kill all active SSH tunnels."""
    info("Killing all active SSH tunnels...")
    success, _ = run("ps aux | grep ssh | grep -v grep | awk '{print $2}' | xargs kill -9", show_output=True)
    if success:
        progress("All SSH tunnels killed.")
    else:
        error("Failed to kill all SSH tunnels.")


def start_sqlite_web(
    port: int, local_port: int, user: str, host: str, db_path: str, sqlite_web_path: str
) -> None:
    """
    Start SQLite Web on the remote machine and create an SSH tunnel.

    Args:
        port: The remote port number for SQLite Web.
        local_port: Local port number for the SSH tunnel.
        user: The username for the SSH connection.
        host: The host for the SSH connection.
        db_path: The path to the SQLite database on the remote machine.
        sqlite_web_path: The path to the sqlite_web executable on the remote machine.
    """
    info("Starting SQLite Web on remote machine...")
    run(
        f"ssh -f {user}@{host} '{sqlite_web_path} {db_path} --host 127.0.0.1 --port {port} >/dev/null 2>&1 &'"
    )

    info("Creating SSH tunnel...")
    run(f"ssh -fNT -L {local_port}:localhost:{port} {user}@{host}")

    time.sleep(2)  # Wait for the tunnel to establish

    info(f"SQLite Web is now running. Access it at http://localhost:{local_port}")
    progress("Press Ctrl+C to stop the SSH tunnel and exit.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        info("Stopping SQLite Web and closing SSH tunnel...")
        ensure_ssh_tunnel(port, kill=True, local_port=local_port, user=user, host=host)
        progress("SQLite Web stopped and SSH tunnel closed.")


def parse_arguments() -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Manage an SSH tunnel on a specified port.")
    parser.add_argument("port", type=int, help="The port number for the SSH tunnel.", nargs="?")
    parser.add_argument("--local-port", type=int, help="Optional local port number for the SSH tunnel.")
    parser.add_argument(
        "--user",
        type=str,
        default=getpass.getuser(),
        help="The username for the SSH tunnel (default: current user).",
    )
    parser.add_argument("host", type=str, help="The host for the SSH tunnel.", nargs="?")
    parser.add_argument("--list", action="store_true", help="List all active SSH tunnels.")
    parser.add_argument("--kill", action="store_true", help="Kill the SSH tunnel on the specified port.")
    parser.add_argument("--kill-all", action="store_true", help="Kill all active SSH tunnels.")
    parser.add_argument("--sqlite-web", action="store_true", help="Start SQLite Web with an SSH tunnel")
    parser.add_argument("--db-path", type=str, help="Path to the SQLite database on the remote machine")
    parser.add_argument(
        "--sqlite-web-path",
        type=str,
        default=DEFAULT_SQLITE_PATH,
        help="Path to the sqlite_web executable on the remote machine",
    )
    return parser, parser.parse_args()


def main():
    """Perform SSH action based on user input."""
    parser, args = parse_arguments()

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(0)

    if args.list:
        list_ssh_tunnels()
    elif args.kill_all:
        kill_all_ssh_tunnels()
    elif args.sqlite_web:
        host = args.host or DEFAULT_SQLITE_HOST
        port = args.port or DEFAULT_SQLITE_PORT
        sqlite_web_path = args.sqlite_web_path or DEFAULT_SQLITE_PATH
        db_path = args.db_path or DEFAULT_SQLITE_FILE

        if not host:
            error(
                "Host is required for SQLite Web. Provide it as an argument or set DEFAULT_SQLITE_HOST in your environment."
            )
        if not db_path:
            error(
                "Database path is required for SQLite Web. Provide it with --db-path or set DEFAULT_SQLITE_FILE in your environment."
            )

        start_sqlite_web(port, args.local_port or port, args.user, host, db_path, sqlite_web_path)
    else:
        if not args.host:
            error("Host is required for SSH tunnel operations.")
        ensure_ssh_tunnel(args.port, args.kill, args.local_port, args.user, args.host)


if __name__ == "__main__":
    main()
