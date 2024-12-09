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
    group.add_argument(
        "--dev",
        nargs="?",
        const=True,  # When --dev is specified without a value
        choices=["enable", "disable"],  # When --dev is given a value
        help="perform action on dev instance, or enable/disable dev instance",
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
        self.logger = LocalLogger.setup_logger()

    def build_image(self) -> bool:
        """Build the Docker image."""
        self.logger.info("Building the Docker image...")

        git_commit_hash = self._fetch_git_commit_hash()
        command = f"GIT_COMMIT_HASH={git_commit_hash} docker compose build"

        try:
            result = subprocess.call(command, shell=True, cwd=str(self.config.project_root))
            if result == 0:
                self.logger.info("Docker image built successfully.")
                return True
            self.logger.error("Failed to build Docker image. Exit code: %d", result)
            return False
        except Exception as e:
            self.logger.error("An error occurred while building the Docker image: %s", str(e))
            return False

    def stop_and_remove_containers(self) -> None:
        """Stop and remove Docker containers."""
        self.logger.info("Stopping and removing %s...", self.config.instance_name)
        run("docker compose down", cwd=str(self.config.project_root))
        self.logger.info("%s stopped and removed.", self.config.instance_name)

    def prune_docker_resources(self) -> None:
        """Clean up unused Docker resources to free up space."""
        self.logger.info("Pruning unused Docker resources...")
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
            self.logger.error("Required nginx containers not running: %s", ", ".join(missing))
            sys.exit(1)

    def _fetch_git_commit_hash(self) -> str:
        """Fetch the current Git commit hash."""
        success, output = run("git rev-parse HEAD")
        return output.strip() if success else "unknown"


class BotControl:
    """Control the dsbots service and the script execution flow."""

    def __init__(self, config: BotControlConfig) -> None:
        self.config = config
        self.docker = DockerControl(self)
        self.logger = LocalLogger.setup_logger()

    def start_dsbots(self, dev: bool = False) -> None:
        """Start the dsbots service."""
        instance = "dsbots-dev" if dev else "dsbots"
        self.logger.info("Starting %s...", instance)

        try:
            subprocess.call("docker compose up -d", shell=True, cwd=str(self.config.project_root))
        except KeyboardInterrupt:
            self.logger.error("Start process interrupted.")

    def ensure_prod_running(self) -> None:
        """Ensure prod instance is running, start if not."""
        command = ["docker", "ps", "--filter", "name=dsbots", "--format", "{{.Status}}"]
        _, output = run(command)
        if "Up" not in output:
            self.logger.info("Prod instance not running, starting...")
            self.start_dsbots(dev=False)

    def handle_start(self) -> None:
        """Handle 'start' action."""
        if self.config.all:
            self.docker.check_nginx()
            self.update_dev_instance_status(True)
            self.start_dsbots(dev=False)
            self.start_dsbots(dev=True)
            self.follow_logs(dev=True)
        elif self.config.dev:
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
        if not self.docker.build_image():
            self.logger.error("Image build failed. Exiting...")
            sys.exit(1)

        if self.config.all:
            self.handle_all()
        else:
            self.docker.stop_and_remove_containers(self.config.dev)
            if self.config.dev:
                self.start_dsbots(dev=True)
            else:
                self.docker.check_nginx()
                self.start_dsbots(dev=False)
            self.follow_logs(self.config.dev)

    def handle_stop(self) -> None:
        """Handle 'stop' action."""
        if self.config.all:
            # Stop dev first, then prod
            self.update_dev_instance_status(False)
            self.docker.stop_and_remove_containers(dev=True)
            self.docker.stop_and_remove_containers(dev=False)
        elif self.config.dev:
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
        self.follow_logs(self.config.dev)

    def follow_logs(self, dev: bool = False) -> None:
        """Follow the logs of the specified instance."""
        instance = "dsbots-dev" if dev else "dsbots"
        try:
            subprocess.call(["docker", "logs", "-f", instance])
        except KeyboardInterrupt:
            self.logger.info("Ending log stream.")
            sys.exit(0)

    def update_dev_instance_status(self, enabled: bool) -> None:
        """Update the dev instance status in config."""
        config_file = self.config.prod_root / "config" / "private" / "debug.yaml"
        yaml = YAML()
        yaml.preserve_quotes = True

        try:
            with config_file.open() as f:
                data = yaml.load(f) or {}

            # Ensure the nested structure exists
            if "dev_instance" not in data:
                data["dev_instance"] = {}

            data["dev_instance"]["enable"] = enabled

            with config_file.open("w") as f:
                yaml.dump(data, f)

            self.logger.debug(
                "Dev instance %s on prod instance.", "enabled" if enabled else "disabled"
            )
        except Exception as e:
            self.logger.error("Failed to update dev instance status: %s", e)


def main() -> None:
    """Perform the requested action."""
    args = parse_args()
    config = BotControlConfig.from_args(args)

    try:
        config.validate_environment()
    except (RuntimeError, ValueError) as e:
        logger = LocalLogger.setup_logger()
        logger.error(str(e))
        sys.exit(1)

    bots = BotControl(config)

    if isinstance(args.dev, str):
        enabled = args.dev == "enable"
        bots.update_dev_instance_status(enabled)
        return
    if args.action == "sync":
        syncer = InstanceSync(config)
        syncer.sync()
    elif args.action == "start":
        bots.handle_start()
    elif args.action == "restart":
        bots.handle_restart()
    elif args.action == "stop":
        bots.handle_stop()
    else:
        bots.follow_logs(dev=bool(args.dev))


if __name__ == "__main__":
    main()
