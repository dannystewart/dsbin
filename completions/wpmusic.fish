complete -c wpmusic -d "the filename of the track to upload"
complete -c wpmusic -l skip-upload -d "convert only, skip uploading (implies --keep-files)" -f
complete -c wpmusic -l keep-files -d "keep converted files after upload" -f
complete -c wpmusic -l append -d "append text to the song title" -f
complete -c wpmusic -l doc -d "show the full documentation and exit" -f
complete -c wpmusic -l history -d "display upload history for all tracks" -f
complete -c wpmusic -l history -d "display upload history for a specific track" -f -a "\"Better Without You\" \"Bring Me To Life\" \"Broken Pieces Shine\" \"Call Me When You're Sober\" \"Everybody's Fool\" \"Going Under\" \"Imaginary\" \"Lithium\" \"Lost In Paradise\" \"My Heart Is Broken\" \"My Last Breath\" \"Snow White Queen\" \"Taking Over Me\" \"The End of the Dream\" \"The Game Is Over\" \"Use My Voice\" \"What You Want\" \"Whisper\" \"Yeah Right\""
complete -c wpmusic -s l -l list -d "number of uploads to list per track (default: 3)" -f
complete -c wpmusic -l force-refresh -d "force refresh of local cache from MySQL server" -f
complete -c wpmusic -l no-cache -d "bypass local cache, always use MySQL server directly" -f
complete -c wpmusic -l check-db -d "test database connection and exit" -f
