#!/usr/bin/env python3

"""Control script for the dsbots service."""

from __future__ import annotations

import argparse
import socket
import subprocess
import sys
from pathlib import Path

from ruamel.yaml import YAML

from .syncer import main as sync_instances

from dsutil.log import LocalLogger

logger = LocalLogger.setup_logger()

# Program paths
PROGRAM_PATH = "/home/danny/docker/dsbots"
PROD_ROOT = Path(PROGRAM_PATH)
DEV_ROOT = PROD_ROOT.parent / "dsbots-dev"
ALLOWED_HOSTS = ["web"]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        nargs="?",
        default="logs",
        choices=["start", "restart", "stop", "logs", "sync"],
        help="action to perform (defaults to logs if not specified)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dev", action="store_true", help="perform action on dev instance")
    group.add_argument(
        "--all", action="store_true", help="perform action on both prod and dev instances"
    )
    return parser.parse_args()


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
                print(decoded_output)  # noqa: T201

            return process.returncode == 0, decoded_output
    except subprocess.CalledProcessError as e:
        if show_output:
            print(e.output.decode("utf-8").strip())  # noqa: T201
        return False, e.output.decode("utf-8").strip()


class DockerControl:
    """Control Docker containers."""

    def __init__(self, bots: BotControl) -> None:
        self.bots = bots

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

    def stop_and_remove_containers(self, dev: bool = False) -> None:
        """Stop and remove Docker containers."""
        instance = "dsbots-dev" if dev else "dsbots"
        project_root = DEV_ROOT if dev else PROD_ROOT
        logger.info("Stopping and removing %s...", instance)
        run("docker compose down", cwd=str(project_root))
        logger.info("%s stopped and removed.", instance)

    def prune_docker_resources(self) -> None:
        """Clean up unused Docker resources to free up space."""
        logger.info("Pruning unused Docker resources...")
        run("docker system prune -f", show_output=True)

    def check_nginx(self) -> None:
        """Check if both nginx containers are running."""
        command = 'docker ps --filter "name=nginx" --format "{{.Names}}"'
        _, output = run(command)
        running_containers = set(output.splitlines())

        # Check if containers with these names exist (using 'in' for partial matches)
        missing = []
        if all("nginx-proxy" not in container for container in running_containers):
            missing.append("nginx-proxy")
        if not any(
            "nginx" in container and "proxy" not in container for container in running_containers
        ):
            missing.append("nginx")

        if missing:
            logger.error("Required nginx containers not running: %s", ", ".join(missing))
            sys.exit(1)

    def _fetch_git_commit_hash(self) -> str:
        """Fetch the current Git commit hash."""
        success, output = run("git rev-parse HEAD")
        return output.strip() if success else "unknown"


class BotControl:
    """Control the dsbots service and the script execution flow."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.docker = DockerControl(self)

    def start_dsbots(self, dev: bool = False) -> None:
        """Start the dsbots service."""
        instance = "dsbots-dev" if dev else "dsbots"
        project_root = DEV_ROOT if dev else PROD_ROOT
        logger.info("Starting %s...", instance)

        try:
            subprocess.call("docker compose up -d", shell=True, cwd=str(project_root))
        except KeyboardInterrupt:
            logger.error("Start process interrupted.")

    def ensure_prod_running(self) -> None:
        """Ensure prod instance is running, start if not."""
        command = ["docker", "ps", "--filter", "name=dsbots", "--format", "{{.Status}}"]
        _, output = run(command)
        if "Up" not in output:
            logger.info("Prod instance not running, starting...")
            self.start_dsbots(dev=False)

    def handle_start(self) -> None:
        """Handle 'start' action."""
        if self.args.all:
            self.docker.check_nginx()
            self.update_dev_instance_status(True)
            self.start_dsbots(dev=False)
            self.start_dsbots(dev=True)
            self.follow_logs(dev=True)
        elif self.args.dev:
            self.ensure_prod_running()
            self.update_dev_instance_status(True)
            self.start_dsbots(dev=True)
            self.follow_logs(dev=True)
        else:
            self.docker.check_nginx()
            self.start_dsbots(dev=False)
            self.follow_logs(dev=False)

    def handle_restart(self) -> None:
        """Handle 'restart' action."""
        if not self.docker.build_image(self.args.dev):
            logger.error("Image build failed. Exiting...")
            sys.exit(1)

        if self.args.all:
            self.handle_all()
        else:
            self.docker.stop_and_remove_containers(self.args.dev)
            if self.args.dev:
                self.start_dsbots(dev=True)
            else:
                self.docker.check_nginx()
                self.start_dsbots(dev=False)
            self.follow_logs(self.args.dev)

    def handle_stop(self) -> None:
        """Handle 'stop' action."""
        if self.args.all:
            # Stop dev first, then prod
            self.update_dev_instance_status(False)
            self.docker.stop_and_remove_containers(dev=True)
            self.docker.stop_and_remove_containers(dev=False)
        elif self.args.dev:
            self.update_dev_instance_status(False)
            self.docker.stop_and_remove_containers(dev=True)
            self.follow_logs(dev=False)
        else:
            self.docker.stop_and_remove_containers(dev=False)

    def handle_all(self):
        """Handle 'restart' action for both instances."""
        self.docker.stop_and_remove_containers(dev=False)
        self.docker.check_nginx()
        self.start_dsbots(dev=False)
        self.docker.stop_and_remove_containers(dev=True)
        self.start_dsbots(dev=True)
        self.follow_logs(self.args.dev)

    def follow_logs(self, dev: bool = False) -> None:
        """Follow the logs of the specified instance."""
        instance = "dsbots-dev" if dev else "dsbots"
        try:
            subprocess.call(["docker", "logs", "-f", instance])
        except KeyboardInterrupt:
            logger.info("Ending log stream.")
            sys.exit(0)

    @staticmethod
    def update_dev_instance_status(enabled: bool) -> None:
        """Update the dev instance status in config."""
        config_file = PROD_ROOT / "config" / "private" / "debug.yaml"
        yaml = YAML()
        yaml.preserve_quotes = True

        try:
            with config_file.open() as f:
                data = yaml.load(f) or {}

            data["enable_dev_instance"] = enabled

            with config_file.open("w") as f:
                yaml.dump(data, f)

            logger.debug("Dev instance %s on prod instance.", "enabled" if enabled else "disabled")
        except Exception as e:
            logger.error("Failed to update dev instance status: %s", e)


def main() -> None:
    """Perform the requested action."""
    validate()
    args = parse_args()
    bots = BotControl(args)

    if args.action == "sync":
        sync_instances()
    elif args.action == "start":
        bots.handle_start()
    elif args.action == "restart":
        bots.handle_restart()
    elif args.action == "stop":
        bots.handle_stop()
    else:
        bots.follow_logs(dev=args.dev)


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


if __name__ == "__main__":
    main()
