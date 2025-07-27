"""Generate Fish completions for all scripts in the project."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TypeGuard

import tomlkit


def extract_argparse_info(script_path: str) -> list[dict[str, str | list[str]]]:
    """Extract argparse info from a Python script."""
    try:
        with Path(script_path).open(encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except Exception:
        return []

    args_info = []
    for node in ast.walk(tree):
        if _is_add_argument_call(node):
            arg_info = _extract_argument_details(node)
            if arg_info:
                args_info.append(arg_info)

    return args_info


def _is_add_argument_call(node: ast.AST) -> TypeGuard[ast.Call]:
    """Check if this node is an add_argument method call."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
    )


def _extract_argument_details(node: ast.Call) -> dict[str, str | list[str]]:
    """Extract argument details from an add_argument call."""
    arg_info = {}

    # Get option names from positional args
    _extract_option_names(node, arg_info)

    # Get keyword arguments
    _extract_keyword_args(node, arg_info)

    # Filter out incomplete argument definitions
    if not any(key in arg_info for key in ["long", "short", "positional"]):
        return {}

    return arg_info


def _extract_option_names(node: ast.Call, arg_info: dict[str, str | list[str]]) -> None:
    """Extract short and long option names from positional arguments."""
    for arg in node.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            option = arg.value
            if option.startswith("--"):
                arg_info["long"] = option[2:]
            elif option.startswith("-"):
                arg_info["short"] = option[1:]
            else:  # This is a positional argument
                arg_info["positional"] = option


def _extract_keyword_args(node: ast.Call, arg_info: dict[str, str | list[str]]) -> None:
    """Extract keyword arguments like help, choices, action, required."""
    for keyword in node.keywords:
        if keyword.arg == "help" and isinstance(keyword.value, ast.Constant):
            help_text = str(keyword.value.value)
            arg_info["help"] = _clean_help_text(help_text)
        elif keyword.arg == "choices":
            choices = _extract_choices(keyword.value)
            if choices:
                arg_info["choices"] = choices
        elif keyword.arg == "action" and isinstance(keyword.value, ast.Constant):
            if keyword.value.value in {"store_true", "store_false"}:
                arg_info["no_arg"] = "true"
        elif keyword.arg == "required" and isinstance(keyword.value, ast.Constant):
            if keyword.value.value:
                arg_info["required"] = "true"
        elif keyword.arg == "nargs" and isinstance(keyword.value, ast.Constant):
            # Capture nargs for better understanding of positional args
            arg_info["nargs"] = str(keyword.value.value)


def _clean_help_text(help_text: str) -> str:
    """Clean and normalize help text for Fish completions."""
    # Remove leading/trailing whitespace
    help_text = help_text.strip()

    # Replace multiple whitespace (including newlines) with single spaces
    help_text = " ".join(help_text.split())

    # Remove default values from help text
    if " (default:" in help_text:
        help_text = help_text.split(" (default:")[0].strip()

    # Start with lowercase letter unless it looks like an acronym
    if help_text and help_text[0].isupper() and (len(help_text) < 2 or not help_text[1].isupper()):
        help_text = help_text[0].lower() + help_text[1:]

    # Escape quotes for Fish shell
    help_text = help_text.replace('"', '\\"')

    # Limit length to keep completions readable
    if len(help_text) > 80:
        help_text = help_text[:77] + "..."

    return help_text


def _extract_choices(value_node: ast.expr) -> list[str]:
    """Extract choices from a choices argument."""
    if not isinstance(value_node, ast.List):
        return []

    return [str(choice.value) for choice in value_node.elts if isinstance(choice, ast.Constant)]


def generate_fish_completion(script_name: str, args_info: list[dict[str, str | list[str]]]) -> str:
    """Generate Fish completion file content."""
    lines = [f"# Auto-generated completions for {script_name}"]

    for arg_info in args_info:
        line = f"complete -c {script_name}"
        if arg_info.get("short"):
            line += f" -s {arg_info['short']}"
        if arg_info.get("long"):
            line += f" -l {arg_info['long']}"
        if arg_info.get("choices"):
            choices = arg_info["choices"]
            if isinstance(choices, list):
                line += f' -a "{" ".join(choices)}"'
        if arg_info.get("help"):
            line += f' -d "{arg_info["help"]}"'

        # Determine if this argument should have file completion
        if _should_disable_file_completion(arg_info):
            line += " -f"  # No file completion

        lines.append(line)

    return "\n".join(lines)


def _should_disable_file_completion(arg_info: dict[str, str | list[str]]) -> bool:
    """Determine if file completion should be disabled for this argument."""
    # Always disable for flags (store_true/store_false)
    if arg_info.get("no_arg"):
        return True

    # Don't disable if there are explicit choices (let the choices handle it)
    if arg_info.get("choices"):
        return False

    # Check if this is clearly not a file argument
    help_text = str(arg_info.get("help", "")).lower()
    arg_name = ""

    # Get argument name for analysis
    if arg_info.get("long"):
        arg_name = str(arg_info["long"]).lower()
    elif arg_info.get("short"):
        arg_name = str(arg_info["short"]).lower()
    elif arg_info.get("positional"):
        arg_name = str(arg_info["positional"]).lower()

    # Only disable file completion for arguments we're confident are not files
    obvious_non_file_patterns = [
        # Numeric values
        "amount",
        "count",
        "delay",
        "depth",
        "distance",
        "duration",
        "height",
        "interval",
        "length",
        "level",
        "limit",
        "max",
        "min",
        "number",
        "percentage",
        "port",
        "rate",
        "size",
        "timeout",
        "width",
        # Time/date values (when not clearly file-related)
        "days",
        "hours",
        "minutes",
        "months",
        "seconds",
        "weeks",
        "years",
        # Network/auth
        "email",
        "host",
        "hostname",
        "key",
        "password",
        "token",
        "url",
        "username",
        # Text values
        "description",
        "label",
        "message",
        "name",
        "tag",
        "text",
        "title",
        # Filters/formats (when clearly not about files)
        "format filter",
        "suffix filter",
        "type filter",
    ]

    text_to_check = f"{help_text} {arg_name}"

    # Only disable if we find clear non-file patterns
    return any(pattern in text_to_check for pattern in obvious_non_file_patterns)


def get_all_scripts_from_pyproject() -> dict[str, str]:
    """Get all script entries from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
    try:
        with pyproject_path.open("rb") as f:
            pyproject = tomlkit.parse(f.read())

        scripts = pyproject.get("project", {}).get("scripts", {})
        return dict(scripts.items())
    except Exception as e:
        print(f"Error reading pyproject.toml: {e}")
        return {}


def module_path_to_file_path(module_path: str) -> Path:
    """Convert a module path like 'dsbin.pybumper.main:main' to a file path."""
    module_part = module_path.split(":", 1)[0]  # Remove function name
    parts = module_part.split(".")

    # Start from the src directory relative to this script's location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    file_path = project_root / "src"

    for part in parts:
        file_path /= part

    return file_path.with_suffix(".py")


def process_all_scripts() -> None:
    """Process all scripts from pyproject.toml and generate Fish completions."""
    scripts = get_all_scripts_from_pyproject()

    if not scripts:
        print("No scripts found in pyproject.toml")
        return

    # Set up both output directories
    fish_completions_dir = Path.home() / ".config" / "fish" / "completions"
    fish_completions_dir.mkdir(parents=True, exist_ok=True)

    # Also write to repo completions directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    repo_completions_dir = project_root / "completions"
    repo_completions_dir.mkdir(exist_ok=True)

    print(f"Found {len(scripts)} scripts in pyproject.toml")
    print("Writing completions to:")
    print(f"  🐟 Fish: {fish_completions_dir}")
    print(f"  📁 Repo: {repo_completions_dir}")
    print("=" * 50)

    successful = 0
    failed = 0

    for script_name, module_path in sorted(scripts.items()):
        file_path = module_path_to_file_path(module_path)

        if not file_path.exists():
            print(f"❌ {script_name}: File not found - {file_path}")
            failed += 1
            continue

        args_info = extract_argparse_info(str(file_path))

        if not args_info:
            print(f"⚠️  {script_name}: No arguments found")
            continue

        completion = generate_fish_completion(script_name, args_info)
        print(f"✅ {script_name}: {len(args_info)} arguments")

        # Write to both locations safely
        fish_completion_file = fish_completions_dir / f"{script_name}.fish"
        repo_completion_file = repo_completions_dir / f"{script_name}.fish"

        completion_content = completion + "\n"

        fish_written = _write_completion_safely(
            fish_completion_file, completion_content, script_name
        )
        repo_written = _write_completion_safely(
            repo_completion_file, completion_content, script_name
        )

        if fish_written or repo_written:
            successful += 1
        else:
            print("   Both files appear to be manually modified")

    print("=" * 50)
    print(f"Processed: {successful} successful, {failed} failed")
    print(f"✨ Fish completions installed to: {fish_completions_dir}")
    print(f"📦 Repo completions saved to: {repo_completions_dir}")
    print("💡 Restart your Fish shell to reload completions")


def _derive_script_name(script_path: str) -> str:
    """Derive a script name from the file path with fallbacks."""
    path = Path(script_path)

    # Try parent directory name if it's not generic
    if path.parent.name not in {"dsbin", "src", "scripts", "bin", "tools"}:
        return path.parent.name

    # Use the filename without extension
    stem = path.stem
    if stem and stem != "main":
        return stem

    # Last resort: use the full filename
    return path.name.replace(".py", "") if path.name.endswith(".py") else path.name


def _is_safe_to_overwrite(completion_file: Path) -> bool:
    """Check if a completion file is safe to overwrite (auto-generated)."""
    if not completion_file.exists():
        return True

    try:
        first_line = completion_file.read_text(encoding="utf-8").split("\n")[0]
        return first_line.startswith("# Auto-generated completions")
    except Exception:
        # If we can't read the file, err on the side of caution
        return False


def _write_completion_safely(
    completion_file: Path, completion_content: str, script_name: str
) -> bool:
    """Write completion file only if it's safe to overwrite."""
    if _is_safe_to_overwrite(completion_file):
        completion_file.write_text(completion_content, encoding="utf-8")
        return True
    print(f"⚠️  Skipping {script_name}: Completion file exists and appears to be manually modified")
    print(f"   To regenerate, remove the first line or delete: {completion_file}")
    return False


def main() -> None:
    """Test the completion generator on a script."""
    import sys

    if len(sys.argv) == 1:
        # No arguments - process all scripts
        process_all_scripts()
        return

    if sys.argv[1] == "--all":
        # Explicit --all flag
        process_all_scripts()
        return

    if len(sys.argv) < 2:
        print("Usage: python dsfish.py [<script_path> [command_name]] | [--all]")
        sys.exit(1)

    script_path = sys.argv[1]

    # Validate script path exists
    if not Path(script_path).exists():
        print(f"❌ Error: Script not found - {script_path}")
        sys.exit(1)

    # Use provided command name or derive from script path
    script_name = sys.argv[2] if len(sys.argv) > 2 else _derive_script_name(script_path)

    # Validate script name
    if not script_name or not script_name.strip():
        print(f"❌ Error: Could not determine script name for {script_path}")
        print("💡 Please provide a script name: dsfish <script_path> <command_name>")
        sys.exit(1)

    print(f"Analyzing {script_path}...")
    args_info = extract_argparse_info(script_path)

    print(f"Found {len(args_info)} arguments:")
    for arg in args_info:
        print(f"  {arg}")

    if args_info:
        # For single script testing, only write to Fish config directory
        fish_completions_dir = Path.home() / ".config" / "fish" / "completions"
        fish_completions_dir.mkdir(parents=True, exist_ok=True)

        completion = generate_fish_completion(script_name, args_info)
        completion_file = fish_completions_dir / f"{script_name}.fish"
        completion_content = completion + "\n"

        if _write_completion_safely(completion_file, completion_content, script_name):
            print(f"\n✅ Fish completion installed for '{script_name}'")
            print(f"📁 Location: {completion_file}")
        else:
            print(f"\n⚠️  Fish completion NOT updated for '{script_name}'")
    else:
        print(f"\n⚠️  No arguments found in {script_path} - no completion generated")

    # Always show the generated completion for reference
    if args_info:
        print(f"\nGenerated Fish completion for '{script_name}':")
        print("=" * 50)
        completion = generate_fish_completion(script_name, args_info)
        print(completion)


if __name__ == "__main__":
    main()
