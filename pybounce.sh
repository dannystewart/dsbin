#!/bin/zsh
# Run pybounce with environment setup and logging for Hazel

# Set up environment
source /Users/danny/.zshrc

# Export the log file path
export HAZEL_LOG_FILE="/Users/danny/.hazel.log"

# Set the number of log lines to keep
LOG_LINE_LIMIT=500

# Poetry-managed virtual environment
VENV_PYTHON='/Users/danny/Library/Caches/pypoetry/virtualenvs/dsutil-zR9-1144-py3.12/bin/python'
BIN_DIR='/Users/danny/.local/bin'
PYBOUNCE_SCRIPT="$BIN_DIR/pybounce"

# Function to add a timestamp to each log line
log_with_timestamp() {
    while IFS= read -r line; do
        echo "$(date "+%Y-%m-%d %H:%M:%S") $line"
    done
}

# Function to trim the log file to the specified number of lines
trim_log_file() {
    python -c "
with open('$HAZEL_LOG_FILE', 'r') as file:
    lines = file.readlines()

# Limit the log to the last $LOG_LINE_LIMIT lines
trimmed_lines = lines[-$LOG_LINE_LIMIT:]

# Find the index of the first line not starting with 'Uploading'
first_non_uploading_index = next((i for i, line in enumerate(trimmed_lines) if not line.startswith('Uploading')), None)

if first_non_uploading_index is not None:
    trimmed_lines = trimmed_lines[first_non_uploading_index:]

with open('$HAZEL_LOG_FILE', 'w') as file:
    file.writelines(trimmed_lines)
"
}

# Trim log file to the specified number of lines or to the first non-'Uploading' line
trim_log_file

# Log the starting message and environment setup
{
    echo "Using Poetry-managed virtual environment:"
    echo "VENV_PYTHON: $VENV_PYTHON"
    echo "BIN_DIR: $BIN_DIR"
    echo "Starting pybounce script..."
} | log_with_timestamp >> "$HAZEL_LOG_FILE"

# Run the Python script and use 'tee' for real-time logging
{
    $VENV_PYTHON $PYBOUNCE_SCRIPT "$1"
} 2>&1 | tee -a "$HAZEL_LOG_FILE" | log_with_timestamp

# Capture the exit status
exit_status=$?

# Log the finishing message and trim the log file
{
    if [ $exit_status -eq 0 ]; then
        echo "pybounce script finished successfully."
    else
        echo "pybounce script failed with exit status $exit_status."
        # Trigger failure notification
        error_message=$(tail -n 10 "$HAZEL_LOG_FILE") # Get the last 10 lines of the log for the error message
        osascript -e "display notification \"Bounce upload failed with exit status $exit_status. Check the log for details.\" with title \"Upload Failed\""
    fi
} | log_with_timestamp >> "$HAZEL_LOG_FILE"

# Display notification
# osascript -e 'display notification "Bounce uploaded to Telegram" with title "Upload Complete"'

# Trim the log file again after logging everything
trim_log_file

exit $exit_status
