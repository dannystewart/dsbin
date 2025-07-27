complete -c changelogs -s a -l add -d "version to add"
complete -c changelogs -s r -l repo-name -d "repo name for links" -f
complete -c changelogs -s u -l update -d "update release from changelog"
complete -c changelogs -l update-all -d "update all releases" -f
complete -c changelogs -l dry-run -d "dry run" -f
