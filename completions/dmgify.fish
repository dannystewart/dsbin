# Auto-generated completions for dmgify
complete -c dmgify -d "folders to process (defaults to current directory)"
complete -c dmgify -s o -l output -d "output filename (without extension)"
complete -c dmgify -l logic -d "handle as Logic project (exclude Bounces, Movie Files, Stems)" -f
complete -c dmgify -s p -l preserve-folder -d "preserve top-level folder at root (flattens by default)" -f
complete -c dmgify -s e -l exclude -d "comma-separated list of folders to exclude" -f
complete -c dmgify -s f -l force -d "overwrite existing files" -f
