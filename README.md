# Bin Scripts

This is my personal collection of scripts and utilities.

## Tool-Specific Documentation

### dockermounter

To have this run automatically on a schedule, first create `/etc/systemd/system/dockermounter.service`:

```bash
[Unit]
Description=Check and fix Docker mount points
After=network.target

[Service]
Type=oneshot
ExecStart=/home/danny/.pyenv/shims/dockermounter --auto
User=root
Environment=PYENV_ROOT=/home/YOUR_USERNAME/.pyenv
Environment=PATH=/home/YOUR_USERNAME/.pyenv/shims:/home/YOUR_USERNAME/.pyenv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target
```

Then create `/etc/systemd/system/dockermounter.timer`:

```bash
[Unit]
Description=Run Docker mount checker periodically

[Timer]
# Run every 15 minutes
OnBootSec=5min
OnUnitActiveSec=15min

[Install]
WantedBy=timers.target
```

Then install:

```bash
sudo cp dockermounter.py /home/danny/.pyenv/shims/dockermounter
sudo chmod +x /home/danny/.pyenv/shims/dockermounter
```

To do this in an easy one-shot:

```bash
sudo tee /etc/systemd/system/dockermounter.service << 'EOF'
[Unit]
Description=Check and fix Docker mount points
After=network.target

[Service]
Type=oneshot
ExecStart=/home/danny/.pyenv/shims/dockermounter --auto
User=root
Environment=PYENV_ROOT=/home/YOUR_USERNAME/.pyenv
Environment=PATH=/home/YOUR_USERNAME/.pyenv/shims:/home/YOUR_USERNAME/.pyenv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/dockermounter.timer << 'EOF'
[Unit]
Description=Run Docker mount checker periodically

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min

[Install]
WantedBy=timers.target
EOF
```

Then enable and start the timer:

```bash
sudo systemctl daemon-reload
sudo systemctl enable dockermounter.timer
sudo systemctl start dockermounter.timer
```
