#!/usr/bin/env python3

"""Update README.md with the latest script list from lsbin."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import tomlkit
from logician import Logician
from polykit import polykit_setup

polykit_setup()

logger = Logician.get_logger()

# Constants for README generation
README_PATH: Path = Path("README.md")
README_TITLE: str = "# DSBin"
START_MARKER: str = "## Script List"
END_MARKER: str = "## License"

INTRO_TEXT: str = (
    "This is my personal collection of Python scripts, built up over many years of solving problems "
    "most people don't care about (or don't *know* they care about… until they discover my scripts).\n\n"
)

# Categories for organizing scripts
CATEGORIES: dict[str, list[tuple[str, str]]] = {
    "Meta Scripts": [],
    "File Management": [],
    "Text Processing Scripts": [],
    "Media Scripts": [],
    "Music Scripts": [],
    "Mac Scripts": [],
    "Logic Pro Scripts": [],
    "System Tools": [],
    "Development Scripts": [],
}

# Map script modules to categories
MODULE_TO_CATEGORY: dict[str, str] = {
    "dsbin.lsbin": "Meta Scripts",
    "dsbin.dsver": "Meta Scripts",
    "dsbin.files": "File Management",
    "dsbin.workcalc": "File Management",
    "dsbin.text": "Text Processing Scripts",
    "dsbin.media": "Media Scripts",
    "dsbin.music": "Music Scripts",
    "dsbin.pybounce": "Music Scripts",
    "dsbin.wpmusic": "Music Scripts",
    "dsbin.mac": "Mac Scripts",
    "dsbin.logic": "Logic Pro Scripts",
    "dsbin.tools": "System Tools",
    "dsbin.updater": "System Tools",
    "dsbin.dev": "Development Scripts",
    "dsbin.pybumper": "Development Scripts",
    "dsbin.configs": "Development Scripts",
}


def get_script_descriptions() -> dict[str, str]:
    """Run lsbin and parse its output to get script descriptions.

    Raises:
        subprocess.CalledProcessError: If lsbin fails to run.
    """
    try:
        result = subprocess.run(
            ["python", "-m", "dsbin.lsbin"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse the output to extract script names and descriptions
        descriptions = {}
        lines = result.stdout.strip().split("\n")

        # Skip header lines
        in_content = False
        for line in lines:
            if "Script Name" in line and "Description" in line:
                in_content = True
                continue

            if not in_content or not line.strip():
                continue

            # Extract script name and description
            match = re.match(r"([\w-]+(?:,\s*[\w-]+)*)\s+(.+)$", line)
            if match:
                scripts, desc = match.groups()
                # Handle multiple scripts (aliases) separated by commas
                for script in [s.strip() for s in scripts.split(",")]:
                    descriptions[script] = desc.strip()

        return descriptions
    except subprocess.CalledProcessError as e:
        logger.error("Failed to run lsbin: %s", e)
        logger.error("stderr: %s", e.stderr)
        raise


def get_categorized_scripts() -> dict[str, list[tuple[str, str]]]:
    """Parse pyproject.toml to get scripts organized by category.

    Returns:
        Dictionary mapping category names to lists of (script_name, module_path) tuples.
    """
    try:
        with Path("pyproject.toml").open("rb") as f:
            pyproject = tomlkit.parse(f.read())

        # Get all scripts
        scripts = pyproject.get("project", {}).get("scripts", {})

        # Assign scripts to categories
        for script_name, module_path in scripts.items():
            category = None
            for prefix, cat in MODULE_TO_CATEGORY.items():
                if module_path.startswith(prefix):
                    category = cat
                    break

            if category:
                CATEGORIES[category].append((str(script_name), str(module_path)))
            else:
                logger.warning(
                    "Could not determine category for script: %s (%s)", script_name, module_path
                )

        return CATEGORIES

    except Exception as e:
        logger.error("Failed to parse pyproject.toml: %s", e)
        raise


def generate_readme_content(
    categories: dict[str, list[tuple[str, str]]], descriptions: dict[str, str]
) -> str:
    """Generate formatted README content with categorized scripts and descriptions.

    Args:
        categories: Dictionary mapping category names to lists of (script_name, module_path) tuples.
        descriptions: Dictionary mapping script names to their descriptions.

    Returns:
        Formatted README content.
    """
    content = [""]

    # Add each category and its scripts
    for category, scripts in categories.items():
        if not scripts:
            continue

        content.append(f"### {category}\n")

        # Group scripts by description
        desc_to_scripts: dict[str, list[str]] = {}
        for script_name, _ in sorted(scripts):
            desc = descriptions.get(script_name, "*(No description available)*")
            desc_to_scripts.setdefault(desc, []).append(script_name)

        # Add each group of scripts with their shared description
        for desc, script_names in desc_to_scripts.items():
            if len(script_names) > 1:
                # Combine multiple scripts with same description
                script_str = ", ".join(f"**{name}**" for name in sorted(script_names))
                content.append(f"- {script_str}: {desc}")
            else:
                # Single script
                content.append(f"- **{script_names[0]}**: {desc}")

        content.append("")

    return "\n".join(content)


def update_readme(readme_path: Path, new_content: str) -> bool:
    """Update the README with new content between markers.

    Args:
        readme_path: Path to the README file.
        new_content: New content to insert.

    Returns:
        True if the README was modified, False otherwise.
    """
    if not readme_path.exists():
        logger.error("README not found: %s", readme_path)
        return False

    content = readme_path.read_text(encoding="utf-8")

    # Check for start marker
    if START_MARKER in content:
        # If both markers exist, replace content between them
        if END_MARKER in content:
            parts = content.split(START_MARKER, 1)
            before_start = parts[0]

            after_start = parts[1].split(END_MARKER, 1)
            after_end = after_start[1] if len(after_start) > 1 else ""

            new_full_content = (
                f"{before_start}{START_MARKER}\n{new_content.rstrip()}\n\n{END_MARKER}{after_end}"
            )
        else:
            # Start marker exists but no end marker
            parts = content.split(START_MARKER, 1)
            new_full_content = f"{parts[0]}{START_MARKER}\n{new_content.rstrip()}"
    # No start marker, check for end marker only
    elif END_MARKER in content:
        parts = content.split(END_MARKER, 1)
        new_full_content = f"{new_content.rstrip()}\n\n{END_MARKER}{parts[1]}"
    else:
        # If neither marker exists, replace the entire content
        new_full_content = new_content

    # Only write if content changed
    if new_full_content != content:
        logger.info("Updating README with latest script list.")
        readme_path.write_text(new_full_content, encoding="utf-8")
        return True

    logger.info("README already contains the latest script list.")
    return False


def update_init_file(content: str) -> bool:
    """Update the __init__.py file with the same content as the README.

    Args:
        content: The formatted content to write to the file.

    Returns:
        True if the file was modified, False otherwise.
    """
    init_path = Path("src/dsbin/__init__.py")

    if not init_path.exists():
        logger.error("__init__.py not found: %s", init_path)
        return False

    # Read the current content
    current_content = init_path.read_text(encoding="utf-8")

    # Format for Python docstring
    docstring_content = f'"""{INTRO_TEXT}{START_MARKER}\n\n{content}\n"""  # noqa: D415, W505\n'

    # Check if there's already a docstring
    docstring_pattern = r'^""".*?""".*?\n'

    if re.match(docstring_pattern, current_content, re.DOTALL):
        # Replace existing docstring
        new_content = re.sub(docstring_pattern, docstring_content, current_content, flags=re.DOTALL)
    else:
        # Add docstring at the beginning
        new_content = docstring_content + current_content

    # Only write if content changed
    if new_content != current_content:
        logger.info("Updating __init__.py with latest script list.")
        init_path.write_text(new_content, encoding="utf-8")
        return True

    logger.info("__init__.py already contains the latest script list.")
    return False


def main() -> int:
    """Update README and __init__.py with categorized script list."""
    try:
        # Get script descriptions from lsbin
        descriptions = get_script_descriptions()

        # Get categorized scripts from pyproject.toml
        categories = get_categorized_scripts()

        # Generate new content
        new_content = generate_readme_content(categories, descriptions)

        # Update README
        readme_updated = update_readme(README_PATH, new_content)

        # Update __init__.py
        init_updated = update_init_file(new_content.replace(README_TITLE, "").strip())

        if readme_updated or init_updated:
            # Add the files to git staging if they were modified
            files_to_add = []
            if readme_updated:
                files_to_add.append("README.md")
            if init_updated:
                files_to_add.append("src/dsbin/__init__.py")

            if files_to_add:
                subprocess.run(["git", "add", *files_to_add], check=True)
                logger.info("Updated files added to git staging.")

        return 0
    except Exception as e:
        logger.error("Failed to update files: %s", str(e))
        return 1


if __name__ == "__main__":
    main()
