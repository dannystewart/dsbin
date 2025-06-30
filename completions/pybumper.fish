# Auto-generated completions for pybumper
complete -c pybumper -d "major, minor, patch, dev, alpha, beta, rc, post; or x.y.z"
complete -c pybumper -s f -l force -d "skip confirmation prompt"
complete -c pybumper -s m -l message -d "custom commit message (default: 'chore(version): bump to x.y.z')"
complete -c pybumper -l no-increment -d "do not increment version; just commit, tag, and push"
complete -c pybumper -l no-push -d "increment version, commit, and tag; do not push"
