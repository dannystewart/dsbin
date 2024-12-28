#!/usr/bin/env python3

"""Control script for the Prism service."""

from __future__ import annotations

import argparse
import socket
import subprocess
import sys
from pathlib import Path

from .syncer import main as sync_instances

from dsutil.log import LocalLogger

logger = LocalLogger.setup_logger()

# Program paths
PROGRAM_PATH = "/home/danny/docker/prism"
PROD_ROOT = Path(PROGRAM_PATH)
DEV_ROOT = PROD_ROOT.parent / "prism-dev"
ALLOWED_HOSTS = ["web"]


class PrismController:
    """Control class for Prism's environment and Docker stack."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.on_all = args.all
        self.on_dev = args.dev

    @staticmethod
    def run(
        command: str | list[str], show_output: bool = False, cwd: str | None = None
    ) -> tuple[bool, str]:
        """Execute a shell command and optionally print the output."""
        try:
            with subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd
            ) as process:
                output, _ = process.communicate()
                decoded_output = output.decode("utf-8").strip()

                if show_output:
                    print(decoded_output)

                return process.returncode == 0, decoded_output
        except subprocess.CalledProcessError as e:
            if show_output:
                print(e.output.decode("utf-8").strip())
            return False, e.output.decode("utf-8").strip()

    def docker_compose_command(
        self, action: str, dev: bool = False, exclude_services: list[str] | None = None
    ) -> None:
        """Run a Docker Compose command while optionally excluding specific services.

        Args:
            action: The Docker Compose action (up, down, etc.).
            dev: Whether to use dev environment.
            exclude_services: List of service names to exclude from the command.
        """
        project_root = DEV_ROOT if dev else PROD_ROOT

        if exclude_services and action in ["down", "stop"]:
            # For down/stop, explicitly list services we want to affect
            services = ["prism"]  # Only target the main service
            service_str = " ".join(services)
            command = f"docker compose {action} {service_str}"
        elif exclude_services and action == "up":
            # For up, use the main command so docker-compose will respect dependencies
            command = f"docker compose {action} -d"
        else:
            command = f"docker compose {action}"

        logger.info("Running command: %s in %s", command, project_root)
        try:
            subprocess.call(command, shell=True, cwd=str(project_root))
        except Exception as e:
            logger.error("Docker Compose command failed: %s", str(e))

    def build_image(self, dev: bool = False) -> bool:
        """Build the Docker image."""
        project_root = DEV_ROOT if dev else PROD_ROOT
        logger.info("Building the Docker image...")

        git_commit_hash = self._fetch_git_commit_hash()
        command = f"GIT_COMMIT_HASH={git_commit_hash} docker compose build"

        try:
            result = subprocess.call(command, shell=True, cwd=str(project_root))
            if result == 0:
                logger.info("Docker image built successfully.")
                return True
            logger.error("Failed to build Docker image. Exit code: %d", result)
            return False
        except Exception as e:
            logger.error("An error occurred while building the Docker image: %s", str(e))
            return False

    def _fetch_git_commit_hash(self) -> str:
        """Fetch the current Git commit hash."""
        success, output = self.run("git rev-parse HEAD")
        return output.strip() if success else "unknown"

    def start_prism(self, dev: bool = False) -> None:
        """Start the Prism service."""
        instance = "prism-dev" if dev else "prism"
        project_root = DEV_ROOT if dev else PROD_ROOT
        logger.info("Starting %s...", instance)

        try:
            subprocess.call("docker compose up -d", shell=True, cwd=str(project_root))
        except KeyboardInterrupt:
            logger.error("Start process interrupted.")

    def stop_and_remove_containers(self, dev: bool = False) -> None:
        """Stop and remove Docker containers."""
        instance = "prism-dev" if dev else "prism"
        project_root = DEV_ROOT if dev else PROD_ROOT
        logger.info("Stopping and removing %s...", instance)
        self.run("docker compose down", cwd=str(project_root))
        logger.info("%s stopped and removed.", instance)

    def check_nginx(self) -> None:
        """Check if both Nginx containers are running."""
        command = 'docker ps --filter "name=nginx" --format "{{.Names}}"'
        _, output = self.run(command)
        running_containers = set(output.splitlines())

        missing = []  # Check if containers with these names exist (using 'in' for partial matches)
        if all("nginx-proxy" not in container for container in running_containers):
            missing.append("nginx-proxy")
        if not any(
            "nginx" in container and "proxy" not in container for container in running_containers
        ):
            missing.append("nginx")

        if missing:
            logger.error("Required nginx containers not running: %s", ", ".join(missing))
            sys.exit(1)

    @staticmethod
    def check_telegram_api() -> bool:
        """Check if the Telegram Bot API service is running."""
        command = ["docker", "ps", "--filter", "name=telegram-bot-api", "--format", "{{.Status}}"]
        _, output = PrismController.run(command)
        is_running = "Up" in output
        if not is_running:
            logger.warning("Telegram Bot API service is not running!")
        return is_running

    def ensure_prod_running(self) -> None:
        """Ensure prod instance is running, start if not."""
        command = ["docker", "ps", "--filter", "name=prism", "--format", "{{.Status}}"]
        _, output = self.run(command)
        if "Up" not in output:
            logger.info("Prod instance not running, starting...")
            self.start_prism(dev=False)

    def handle_start(self) -> None:
        """Handle 'start' action."""
        if self.on_all:
            self.check_nginx()
            self.start_prism(dev=False)
            self.start_prism(dev=True)
            self.follow_logs(dev=True)
        elif self.on_dev:
            self.ensure_prod_running()
            self.start_prism(dev=True)
            self.follow_logs(dev=True)
        else:
            self.check_nginx()
            self.start_prism(dev=False)
            self.follow_logs(dev=False)

    def handle_restart(self) -> None:
        """Handle 'restart' action."""
        if not self.build_image(self.on_dev):
            logger.error("Image build failed. Exiting...")
            sys.exit(1)

        if self.on_all:
            self.handle_all()
        else:
            self.stop_and_remove_containers(self.on_dev)
            if self.on_dev:
                self.start_prism(dev=True)
            else:
                self.check_nginx()
                self.start_prism(dev=False)
            self.follow_logs(self.on_dev)

    def handle_stop(self) -> None:
        """Handle 'stop' action."""
        if self.on_all:  # Stop dev first, then prod
            self.stop_and_remove_containers(dev=True)
            self.stop_and_remove_containers(dev=False)
        elif self.on_dev:
            self.stop_and_remove_containers(dev=True)
            self.follow_logs(dev=False)
        else:
            self.stop_and_remove_containers(dev=False)

    def handle_all(self):
        """Handle 'restart' action for both instances."""
        self.stop_and_remove_containers(dev=False)
        self.check_nginx()
        self.start_prism(dev=False)
        self.stop_and_remove_containers(dev=True)
        self.start_prism(dev=True)
        self.follow_logs(self.on_dev)

    def follow_logs(self, dev: bool = False) -> None:
        """Follow the logs of the specified instance."""
        instance = "prism-dev" if dev else "prism"
        try:
            subprocess.call(["docker", "logs", "-f", instance])
        except KeyboardInterrupt:
            logger.info("Ending log stream.")
            sys.exit(0)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments in a flexible, command-style way."""
    # Define valid options
    actions = {"start", "restart", "stop", "logs", "sync"}
    modifiers = {"dev", "all"}

    # Get all args after the script name
    args = {arg.lower() for arg in sys.argv[1:]}

    # Find the action (default to logs if none specified)
    action = next((arg for arg in args if arg in actions), "logs")

    # Check for modifiers
    is_dev = "dev" in args
    is_all = "all" in args

    # Validate combinations
    if is_dev and is_all:
        logger.error("Cannot specify both 'dev' and 'all' at the same time")
        sys.exit(1)

    # Check for unknown arguments
    valid_args = actions | modifiers
    unknown_args = args - valid_args
    if unknown_args:
        logger.error("Unknown arguments: %s", ", ".join(unknown_args))
        sys.exit(1)

    # Create a Namespace object with the parsed arguments
    return argparse.Namespace(action=action, dev=is_dev, all=is_all)


def validate() -> None:
    """Validate the execution environment."""
    hostname = socket.gethostname().lower()
    try:
        fqdn = socket.getfqdn().lower()
        if "ip6.arpa" in fqdn:
            fqdn = hostname
    except Exception:
        fqdn = hostname

    host_names = {hostname, fqdn}
    host_names.add(hostname.split(".")[0])

    allowed_on_host = any(
        name == allowed or name.startswith(allowed + ".")
        for name in host_names
        for allowed in ALLOWED_HOSTS
    )

    if not allowed_on_host:
        logger.error("This script can only run on hosts: %s.", ALLOWED_HOSTS)
        sys.exit(1)

    if not PROD_ROOT.exists() or not DEV_ROOT.exists():
        logger.error("Required paths for prod and dev instances not found.")
        sys.exit(1)

    if not PrismController.check_telegram_api():
        logger.warning("Telegram Bot API service should be running for proper operation.")


def main() -> None:
    """Perform the requested action."""
    validate()
    args = parse_args()
    prism = PrismController(args)

    if args.action == "sync":
        sync_instances()
    elif args.action == "start":
        prism.handle_start()
    elif args.action == "restart":
        prism.handle_restart()
    elif args.action == "stop":
        prism.handle_stop()
    else:
        prism.follow_logs(dev=args.dev)


if __name__ == "__main__":
    main()
