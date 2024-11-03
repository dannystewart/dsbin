#!/bin/bash

# Wrapper script to run the Python-based updater with sudo

# Read VENV_PYTHON from .aliases_scripts
ALIASES_FILE="$HOME/.aliases_scripts"
if [ -f "$ALIASES_FILE" ]; then
    VENV_PYTHON=$(grep '^VENV_PYTHON=' "$ALIASES_FILE" | cut -d"'" -f2)
    BIN_DIR=$(grep '^BIN_DIR=' "$ALIASES_FILE" | cut -d"'" -f2)
else
    echo "Error: $ALIASES_FILE not found"
    exit 1
fi

# Check if VENV_PYTHON and BIN_DIR were successfully read
if [ -z "$VENV_PYTHON" ] || [ -z "$BIN_DIR" ]; then
    echo "Error: Could not read VENV_PYTHON or BIN_DIR from $ALIASES_FILE"
    exit 1
fi

# Create a named pipe
PIPE=/tmp/update_sudo_pipe
mkfifo $PIPE

# Cleanup function
cleanup() {
    rm -f $PIPE
    exit
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Function to check if sudo is needed
needs_sudo() {
    "$VENV_PYTHON" "$BIN_DIR/dsupdater/updater.py" --check-sudo
    return $?
}

# Function to refresh sudo timestamp
refresh_sudo() {
    sudo -v
}

# Check if sudo is needed
if needs_sudo; then
    if sudo -n true 2>/dev/null; then
        refresh_sudo
        echo "sudo_available" > $PIPE &
    else
        if refresh_sudo; then
            echo "sudo_available" > $PIPE &
        else
            echo "sudo_unavailable" > $PIPE &
        fi
    fi
else
    echo "sudo_not_needed" > $PIPE &
fi

# Run the updater script
"$VENV_PYTHON" "$BIN_DIR/dsupdater/updater.py" "$@"
