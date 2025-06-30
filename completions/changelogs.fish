# Auto-generated completions for changelogs
complete -c changelogs -s v -l version -d "version to add (defaults to version from pyproject.toml)" -f
complete -c changelogs -l from-commit-history -d "automatically generate changelog entries from Git commit messages" -f
complete -c changelogs -s r -l repo-name -d "GitHub repo name to use for links (defaults to auto-detect)" -f
complete -c changelogs -s u -l update -d "update a single release with changelog content (defaults to current version)" -f
complete -c changelogs -l update-all -d "update all existing releases based on changelog content" -f
complete -c changelogs -l dry-run -d "print what would be done without making any changes" -f
