#!/usr/bin/env python3

"""Control script for the Prism service."""

from __future__ import annotations

import socket
import subprocess
import sys
from pathlib import Path
from threading import Thread

from dsbase import LocalLogger, configure_traceback

from dsbin.prism.prism_config import Action, PrismConfig
from dsbin.prism.prism_sync import main as sync_instances

configure_traceback()

logger = LocalLogger().get_logger(level="info")

# Program paths
PROGRAM_PATH = "/home/danny/docker/prism"
PROD_ROOT = Path(PROGRAM_PATH)
DEV_ROOT = PROD_ROOT.parent / "prism-dev"
ALLOWED_HOSTS = ["web"]


class PrismController:
    """Control class for Prism's environment and Docker stack."""

    def __init__(self, config: PrismConfig):
        self.config = config

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

    def docker_compose_command(self, action: str, dev: bool = False) -> None:
        """Run a Docker Compose command.

        Args:
            action: The Docker Compose action (up, down, etc.).
            dev: Whether to use dev environment.
        """
        project_root = DEV_ROOT if dev else PROD_ROOT
        command = f"docker compose {action}"

        if action == "up":
            command += " -d"

        logger.debug("Running command in %s: %s", project_root, command)
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
        logger.info("Starting %s...", instance)

        try:
            self.docker_compose_command("up", dev)
        except KeyboardInterrupt:
            logger.error("Start process interrupted.")

    def stop_and_remove_containers(self, dev: bool = False) -> None:
        """Stop and remove Docker containers."""
        instance = "prism-dev" if dev else "prism"
        logger.info("Stopping and removing %s...", instance)
        self.docker_compose_command("down", dev)
        logger.info("%s stopped and removed.", instance)

    def restart_single_instance(self, dev: bool) -> None:
        """Handle restart for a single instance.

        Args:
            dev: Whether this is the dev instance
        """
        instance = "dev" if dev else "prod"
        logger.info("Restarting %s instance...", instance)
        self.stop_and_remove_containers(dev)

        if not dev:  # Only check nginx for prod instance
            self.check_nginx()

        self.start_prism(dev)
        logger.info("%s instance restart completed.", instance.capitalize())

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
    def ensure_telegram_api() -> None:
        """Ensure Telegram Bot API service is running."""
        command = ["docker", "ps", "--filter", "name=telegram-bot-api", "--format", "{{.Status}}"]
        _, output = PrismController.run(command)
        if "Up" not in output:
            logger.info("Starting Telegram Bot API service...")
            subprocess.call("docker compose --profile shared up -d", shell=True, cwd=str(PROD_ROOT))

    def ensure_prod_running(self) -> None:
        """Ensure prod instance is running, start if not."""
        command = ["docker", "ps", "--filter", "name=prism", "--format", "{{.Status}}"]
        _, output = self.run(command)
        if "Up" not in output:
            logger.info("Prod instance not running, starting...")
            self.start_prism(dev=False)

    def handle_start(self) -> None:
        """Handle 'start' action."""
        if self.config.on_all:
            self.check_nginx()
            self.start_prism(dev=False)
            self.start_prism(dev=True)
            self.follow_logs(dev=True)
        elif self.config.on_dev:
            self.ensure_prod_running()
            self.start_prism(dev=True)
            self.follow_logs(dev=True)
        else:
            self.check_nginx()
            self.start_prism(dev=False)
            self.follow_logs(dev=False)

    def handle_restart(self) -> None:
        """Handle 'restart' action."""
        if self.config.on_all:
            if not self.build_image(False) or not self.build_image(True):
                logger.error("Image build failed. Exiting...")
                sys.exit(1)
        elif not self.build_image(self.config.on_dev):
            logger.error("Image build failed. Exiting...")
            sys.exit(1)

        if self.config.on_all:
            self.handle_all()
        else:
            self.stop_and_remove_containers(self.config.on_dev)
            if self.config.on_dev:
                self.start_prism(dev=True)
            else:
                self.check_nginx()
                self.start_prism(dev=False)
            self.follow_logs(self.config.on_dev)

    def handle_stop(self) -> None:
        """Handle 'stop' action."""
        if self.config.on_all:  # Stop dev first, then prod
            self.stop_and_remove_containers(dev=True)
            self.stop_and_remove_containers(dev=False)
        elif self.config.on_dev:
            self.stop_and_remove_containers(dev=True)
            self.follow_logs(dev=False)
        else:
            self.stop_and_remove_containers(dev=False)

    def handle_all(self) -> None:
        """Handle 'restart' action for both instances using threads."""
        # Create threads for both instances
        prod_thread = Thread(target=self.restart_single_instance, args=(False,))
        dev_thread = Thread(target=self.restart_single_instance, args=(True,))

        # Start both threads
        prod_thread.start()
        dev_thread.start()

        # Wait for both threads to complete
        prod_thread.join()
        dev_thread.join()

        logger.info("All instances restarted successfully!")

        # Follow logs after both restarts are complete
        self.follow_logs(self.config.on_dev)

    def follow_logs(self, dev: bool = False) -> None:
        """Follow the logs of the specified instance."""
        instance = "prism-dev" if dev else "prism"
        try:
            subprocess.call(["docker", "logs", "-f", instance])
        except KeyboardInterrupt:
            logger.info("Ending log stream.")
            sys.exit(0)


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

    PrismController.ensure_telegram_api()


def parse_args() -> PrismConfig:
    """Parse command-line arguments in a flexible, command-style way."""
    args = {arg.lower() for arg in sys.argv[1:]}
    return PrismConfig.from_args(args, logger)


def main() -> None:
    """Perform the requested action."""
    validate()
    config = parse_args()
    prism = PrismController(config)

    if config.action is Action.SYNC:
        sync_instances()
    elif config.action is Action.START:
        prism.handle_start()
    elif config.action is Action.RESTART:
        prism.handle_restart()
    elif config.action is Action.STOP:
        prism.handle_stop()
    else:
        prism.follow_logs(dev=config.on_dev)


if __name__ == "__main__":
    main()
