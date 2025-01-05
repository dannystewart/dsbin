#!/bin/bash

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
    dsupdater --check-sudo
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
dsupdater "$@"
