# Format options
complete -c alacrity -l m4a -f -d "convert files to ALAC"
complete -c alacrity -l flac -f -d "convert files to FLAC"
complete -c alacrity -l wav -f -d "convert files to WAV"
complete -c alacrity -l aiff -f -d "convert files to AIFF"

# Operation modes
complete -c alacrity -l undo -f -d "convert M4A back to WAV"
complete -c alacrity -l preserve-depth -f -d "preserve 24-bit depth"

# File completion for paths argument
complete -c alacrity -f -a "(__fish_complete_suffix .aiff .aif .wav .m4a .flac)" -d "file"
complete -c alacrity -f -a "(__fish_complete_directories)" -d "directory"
