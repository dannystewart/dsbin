# Auto-generated completions for impactanalyzer
complete -c impactanalyzer -s b -l base -d "path to the base repository for impact analysis"
complete -c impactanalyzer -s r -l repos -d "paths to package repos to analyze (accepts multiple)"
complete -c impactanalyzer -s e -l exclude -d "paths to package repos to exclude from analysis (accepts multiple)"
complete -c impactanalyzer -s c -l commit -d "git reference to compare against"
complete -c impactanalyzer -s d -l diff -d "show detailed diffs for the specified repository" -f
complete -c impactanalyzer -l diff-repo -d "specify which repository to show diffs for (optional with --diff)"
complete -c impactanalyzer -l staged-only -d "show only staged changes rather than working directory" -f
complete -c impactanalyzer -l hide-untagged -d "hide repositories with no release tags in the output" -f
complete -c impactanalyzer -l include-pyproject -d "consider pyproject.toml changes as well" -f
complete -c impactanalyzer -s v -l verbose -d "show detailed output" -f
