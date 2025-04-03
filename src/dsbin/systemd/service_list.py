from __future__ import annotations

from pathlib import Path

from dsbin.systemd.systemd import ServiceConfigBase, SystemdServiceTemplate, service_configs

COMMAND_PATH = Path.home() / ".pyenv/shims/dockermounter"


@service_configs(
    SystemdServiceTemplate(
        name="dockermounter",
        description="Check and fix Docker mount points",
        command=[str(COMMAND_PATH), "--auto"],
        schedule="15min",
        after_targets=["network.target"],
    ),
)
class ServiceConfigs(ServiceConfigBase):
    """Collection of service configurations for dsbin."""
