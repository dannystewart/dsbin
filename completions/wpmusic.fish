# Subcommands
complete --command wpmusic -x -n __fish_use_subcommand -a "upload" -d "convert files for upload"
complete --command wpmusic -x -n __fish_use_subcommand -a "convert" -d "convert files without uploading"
complete --command wpmusic -x -n __fish_use_subcommand -a "history" -d "show upload history by track"

# Upload subcommand
complete -c wpmusic -n "__fish_seen_subcommand_from upload" -d "audio files to upload" -x -a "(__fish_complete_suffix .wav .mp3 .flac .m4a .aac .ogg)"
complete -c wpmusic -n "__fish_seen_subcommand_from upload" -l keep-files -d "keep converted files after upload" -f
complete -c wpmusic -n "__fish_seen_subcommand_from upload" -l append -d "append text to the song title" -f

# Convert subcommand
complete -c wpmusic -n "__fish_seen_subcommand_from convert" -d "audio files to convert" -x -a "(__fish_complete_suffix .wav .mp3 .flac .m4a .aac .ogg)"
complete -c wpmusic -n "__fish_seen_subcommand_from convert" -l append -d "append text to the song title" -f

# History subcommand
complete -c wpmusic -n "__fish_seen_subcommand_from history" -d "optional track name to filter history" -f -a "'Better Without You' 'Bring Me To Life' 'Broken Pieces Shine' 'Call Me When You'\''re Sober' 'Everybody'\''s Fool' 'Going Under' 'Imaginary' 'Lithium' 'Lost In Paradise' 'My Heart Is Broken' 'My Last Breath' 'Snow White Queen' 'Taking Over Me' 'The End of the Dream' 'The Game Is Over' 'Use My Voice' 'What You Want' 'Whisper' 'Yeah Right'"
complete -c wpmusic -n "__fish_seen_subcommand_from history" -s u -l uploads-per-track -d "uploads to show per track" -f
complete -c wpmusic -n "__fish_seen_subcommand_from history" -l no-cache -d "bypass local cache and use MySQL server directly" -f
complete -c wpmusic -n "__fish_seen_subcommand_from history" -l refresh-cache -d "refresh local cache from MySQL server" -f
complete -c wpmusic -n "__fish_seen_subcommand_from history" -l test-db-connection -d "test database connection and exit" -f
