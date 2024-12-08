from __future__ import annotations

import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from dsutil import LocalLogger

if TYPE_CHECKING:
    import argparse


@dataclass
class BotControlConfig:
    """Configuration for instance sync operations."""

    prod_root: Path
    dev_root: Path
    sync_dirs: list[str]
    sync_files: list[str]
    exclude_patterns: list[str]
    allowed_hosts: list[str]
    prod_instance_name: str
    dev_instance_name: str
    instance_name: str = field(init=False)
    project_root: Path = field(init=False)
    dev: bool = False
    all: bool = False
    action: Literal["start", "restart", "stop", "logs", "sync"] | None = None

    def __post_init__(self):
        """Validate and set derived attributes."""
        # Validate paths
        self.prod_root = Path(self.prod_root).resolve()
        self.dev_root = Path(self.dev_root).resolve()

        # Validate hosts
        if not self.allowed_hosts:
            msg = "At least one allowed host must be specified"
            raise ValueError(msg)

        # Convert all hosts to lowercase for consistent comparison
        self.allowed_hosts = [host.lower() for host in self.allowed_hosts]

        # Set derived attributes
        self.project_root = self.dev_root if self.dev else self.prod_root
        self.instance_name = self.dev_instance_name if self.dev else self.prod_instance_name

    def validate_environment(self) -> None:
        """Validate the execution environment."""
        logger = LocalLogger.setup_logger(level="info")

        # Get hostname information
        hostname = socket.gethostname().lower()
        try:
            fqdn = socket.getfqdn().lower()
            # Filter out IPv6 reverse DNS results
            if "ip6.arpa" in fqdn:
                fqdn = hostname
        except Exception:
            fqdn = hostname

        # Get all possible names for this host
        host_names = {hostname, fqdn}
        # Add the first component of the hostname (before any dots)
        host_names.add(hostname.split(".")[0])

        logger.debug("Environment details:")
        logger.debug("  Raw hostname: %s", hostname)
        logger.debug("  Raw FQDN: %s", fqdn)
        logger.debug("  Checked names: %s", sorted(host_names))
        logger.debug("  Allowed hosts: %s", self.allowed_hosts)

        if not any(
            name == allowed or name.startswith(allowed + ".")
            for name in host_names
            for allowed in self.allowed_hosts
        ):
            msg = (
                f"This script can only run on allowed hosts: {', '.join(self.allowed_hosts)}. "
                f"Current hostname: {hostname}."
            )
            raise RuntimeError(msg)

        if not self.prod_root.exists():
            msg = f"Production root does not exist: {self.prod_root}"
            raise RuntimeError(msg)

        if not self.dev_root.exists():
            msg = f"Development root does not exist: {self.dev_root}"
            raise RuntimeError(msg)

    @classmethod
    def create_default(cls, base_path: Path, args: argparse.Namespace) -> BotControlConfig:
        """Create default configuration for dsbots sync."""
        return cls(
            prod_root=base_path / "dsbots",
            dev_root=base_path / "dsbots-dev",
            sync_dirs=["config", "data"],
            sync_files=[
                "src/dsbots/config/ip_whitelist.py",
                "src/dsbots/.env",
            ],
            exclude_patterns=[
                ".gitignore",
                "__pycache__",
                "*.pyc",
            ],
            allowed_hosts=["web"],
            dev=args.dev,
            all=args.all,
            prod_instance_name="dsbots",
            dev_instance_name="dsbots-dev",
            action=args.action,
        )
