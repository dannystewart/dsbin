from __future__ import annotations

from dsbin.systemd.systemd import ServiceConfigBase, SystemdServiceTemplate, service_configs


@service_configs(
    SystemdServiceTemplate(
        name="dockermounter",
        description="Check and fix Docker mount points",
        command=["/home/danny/.pyenv/shims/dockermounter", "--auto"],
        schedule="15min",
        after_targets=["network.target"],
    ),
)
class ServiceConfigs(ServiceConfigBase):
    """Collection of service configurations for dsutil."""
