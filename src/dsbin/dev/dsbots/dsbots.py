#!/usr/bin/env python3

"""Control script for the dsbots service."""

from __future__ import annotations

import argparse
import subprocess
import sys

from ruamel.yaml import YAML

from .config import BotControlConfig
from .syncer import InstanceSync

from dsutil import LocalLogger

logger = LocalLogger.setup_logger()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        nargs="?",
        default="logs",
        choices=["start", "restart", "stop", "logs", "sync", "enable", "disable"],
        help="action to perform (defaults to logs if not specified)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dev",
        action="store_true",
        help="perform action on dev instance",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="perform action on both prod and dev instances",
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

    def __init__(self, config: BotControlConfig) -> None:
        self.config = config

    def build_image(self) -> bool:
        """Build the Docker image."""
        logger.info("Building the Docker image...")

        git_commit_hash = self._fetch_git_commit_hash()
        command = f"GIT_COMMIT_HASH={git_commit_hash} docker compose build"

        try:
            result = subprocess.call(command, shell=True, cwd=str(self.config.project_root))
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
        instance_name = self.config.get_instance(dev)
        logger.info("Stopping and removing %s...", instance_name)
        run("docker compose down", cwd=str(self.config.project_root))
        logger.info("%s stopped and removed.", instance_name)

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

    def __init__(self, config: BotControlConfig) -> None:
        self.config = config
        self.docker = DockerControl(config)

    def start_dsbots(self, dev: bool = False) -> None:
        """Start the dsbots service."""
        instance = self.config.get_instance(dev)
        logger.info("Starting %s...", instance)

        try:
            subprocess.call("docker compose up -d", shell=True, cwd=str(self.config.project_root))
        except KeyboardInterrupt:
            logger.error("Start process interrupted.")

    def ensure_prod_running(self) -> None:
        """Ensure prod instance is running. Start it if not."""
        command = ["docker", "ps", "--filter", "name=dsbots", "--format", "{{.Status}}"]
        _, output = run(command)
        if "Up" not in output:
            logger.info("Prod instance not running, starting...")
            self.start_dsbots(dev=False)

    def handle_start(self) -> None:
        """Handle 'start' action."""
        if self.config.all:
            self.docker.check_nginx()
            self.configure_dev_forwarding(self.config)
            self.start_dsbots(dev=False)  # prod start
            self.start_dsbots(dev=True)  # dev start
            self._follow_logs(dev=True)  # follow dev logs
        elif self.config.dev:
            self.ensure_prod_running()
            self.configure_dev_forwarding(self.config)
            self.start_dsbots(dev=True)  # dev start
            self._follow_logs(dev=True)  # follow dev logs
        else:
            self.docker.check_nginx()
            self.start_dsbots(dev=False)  # prod start
            self._follow_logs(dev=False)  # follow prod logs

    def handle_restart(self) -> None:
        """Handle 'restart' action."""
        if not self.docker.build_image():
            logger.error("Image build failed. Exiting...")
            sys.exit(1)

        if self.config.all:
            self.docker.check_nginx()
            # Stop both instances
            self.docker.stop_and_remove_containers(dev=False)  # prod stop
            self.docker.stop_and_remove_containers(dev=True)  # dev stop
            # Start both instances
            self.start_dsbots(dev=False)  # prod start
            self.start_dsbots(dev=True)  # dev start
            self._follow_logs(dev=True)  # follow dev logs
        elif self.config.dev:
            self.docker.stop_and_remove_containers(dev=True)  # dev stop
            self.start_dsbots(dev=True)  # dev start
            self._follow_logs(dev=True)  # follow dev logs
        else:
            self.docker.stop_and_remove_containers(dev=False)  # prod stop
            self.docker.check_nginx()
            self.start_dsbots(dev=False)  # prod start
            self._follow_logs(dev=False)  # follow prod logs

    def handle_stop(self) -> None:
        """Handle 'stop' action."""
        if self.config.all:
            self.configure_dev_forwarding(self.config)
            self.docker.stop_and_remove_containers(dev=True)  # dev stop
            self.docker.stop_and_remove_containers(dev=False)  # prod stop
        elif self.config.dev:
            self.configure_dev_forwarding(self.config)
            self.docker.stop_and_remove_containers(dev=True)  # dev stop
        else:
            self.docker.stop_and_remove_containers(dev=False)  # prod stop

    def follow_instance_logs(self) -> None:
        """Follow logs based on current configuration."""
        follow_dev = self.config.dev or self.config.all
        self._follow_logs(dev=follow_dev)

    def _follow_logs(self, dev: bool = False) -> None:
        instance = self.config.get_instance(dev)
        try:
            subprocess.call(["docker", "logs", "-f", instance])
        except KeyboardInterrupt:
            logger.info("Ending log stream.")
            sys.exit(0)

    @staticmethod
    def configure_dev_forwarding(config: BotControlConfig) -> None:
        """Update the dev instance status in config."""
        config_file = config.prod_root / "config" / "private" / "debug.yaml"
        yaml = YAML()
        yaml.preserve_quotes = True

        try:
            enabled = config.action == "enable"
            with config_file.open() as f:
                data = yaml.load(f) or {}

            # Ensure the nested structure exists
            if "dev_instance" not in data:
                data["dev_instance"] = {}

            data["dev_instance"]["enable"] = enabled

            with config_file.open("w") as f:
                yaml.dump(data, f)

            logger.debug("Dev instance %s on prod instance.", "enabled" if enabled else "disabled")
        except Exception as e:
            logger.error("Failed to update dev instance status: %s", e)


def main() -> None:
    """Perform the requested action."""
    args = parse_args()
    config = BotControlConfig.from_args(args)

    if args.action in ["enable", "disable"]:
        return BotControl.configure_dev_forwarding(config)

    if args.action == "sync":
        syncer = InstanceSync(config)
        return syncer.sync()

    bots = BotControl(config)
    if args.action == "start":
        bots.handle_start()
    elif args.action == "restart":
        bots.handle_restart()
    elif args.action == "stop":
        bots.handle_stop()
    else:
        bots.follow_instance_logs()


if __name__ == "__main__":
    main()
