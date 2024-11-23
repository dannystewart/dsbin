from __future__ import annotations

from dataclasses import dataclass

from .service_template import SystemdServiceTemplate


@dataclass
class ServiceConfigs:
    """Collection of service configurations for dsutil."""

    dockermounter = SystemdServiceTemplate(
        name="dockermounter",
        description="Check and fix Docker mount points",
        command=["/home/danny/.pyenv/shims/dockermounter", "--auto"],
        schedule="15min",
        after_targets=["network.target"],
    )
