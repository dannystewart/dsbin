# Auto-generated completions for pybumper
complete -c pybumper -d "major, minor, patch, dev, alpha, beta, rc, post; or x.y.z" -f
complete -c pybumper -s f -l force -d "skip confirmation prompt" -f
complete -c pybumper -s m -l message -d "custom commit message" -f
complete -c pybumper -l no-increment -d "do not increment version; just commit, tag, and push" -f
complete -c pybumper -l no-push -d "increment version, commit, and tag; do not push" -f
complete -c pybumper -s i -l increment-only -d "increment version in pyproject.toml only; no git operations" -f
