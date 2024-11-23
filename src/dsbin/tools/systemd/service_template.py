from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class SystemdServiceTemplate:
    """Configuration for a systemd service."""

    name: str
    description: str
    command: list[str]
    schedule: str  # e.g., "15min" or "1h"
    boot_delay: str = "5min"
    user: str = "root"
    after_targets: list[str] | None = None

    def generate_service_file(self) -> str:
        """Generate the content for the systemd service file."""
        after = " ".join(self.after_targets) if self.after_targets else "network.target"
        command = " ".join(self.command)

        return f"""[Unit]
Description={self.description}
After={after}

[Service]
Type=oneshot
ExecStart={command}
User={self.user}
Environment=PYENV_ROOT={os.environ.get('PYENV_ROOT', '')}
Environment=PATH={os.environ.get('PATH')}

[Install]
WantedBy=multi-user.target
"""

    def generate_timer_file(self) -> str:
        """Generate the content for the systemd timer file."""
        return f"""[Unit]
Description=Timer for {self.description}

[Timer]
OnBootSec={self.boot_delay}
OnUnitActiveSec={self.schedule}

[Install]
WantedBy=timers.target
"""

    def get_summary(self) -> str:
        """Get a one-line summary of the service."""
        return f"{self.description} (runs every {self.schedule})"
