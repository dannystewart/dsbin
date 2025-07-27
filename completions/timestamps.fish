complete -c timestamps -d "file to get or set timestamps for"
complete -c timestamps -s c -l creation -d "creation timestamp to set" -f
complete -c timestamps -s m -l modification -d "modification timestamp to set" -f
complete -c timestamps -l copy -d "copy timestamps from one file to another" -f
complete -c timestamps -l copy-from -d "source file to copy timestamps from"
complete -c timestamps -l copy-to -d "destination file to copy timestamps to"
complete -c timestamps -l src-dir -d "source directory for copying timestamps from"
complete -c timestamps -l dest-dir -d "destination directory for copying timestamps to"
complete -c timestamps -l ctime-to-mtime -d "copy creation time to modification time" -f
complete -c timestamps -l mtime-to-ctime -d "copy modification time to creation time" -f
