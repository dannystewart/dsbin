complete -c workcalc -d "directory to analyze"
complete -c workcalc -s b -l break-time -d "minutes of inactivity to consider a session break (default: 60)" -f
complete -c workcalc -s m -l min-work -d "minimum minutes to count per work item (default: 15)" -f
complete -c workcalc -l since -d "start date as MM/DD/YYYY or relative (30d, 1w, 1m)"
complete -c workcalc -l start -d "start date in MM/DD/YYYY format"
complete -c workcalc -l end -d "end date in MM/DD/YYYY format"
