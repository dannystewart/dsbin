#!/usr/bin/env python3
from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from polykit.cli import PolyArgs, handle_interrupt
from polykit.log import PolyLog
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.formatted_text import HTML

from .pypi_classifiers import PYPI_CLASSIFIERS

logger = PolyLog.get_logger(simple=True)


@dataclass
class PyProjectConfig:
    """Dataclass to hold the configuration for pyproject.toml."""

    name: str
    version: str = "0.1.0"
    description: str = ""
    authors: list[str] = field(default_factory=list)
    readme: str = "README.md"
    requires_python: str = ">=3.12"
    license: str | None = None
    homepage: str | None = None
    repository: str | None = None
    documentation: str | None = None
    keywords: list[str] = field(default_factory=list)
    classifiers: list[str] = field(default_factory=list)
    dependencies: dict[str, str] = field(default_factory=dict)
    dev_dependencies: dict[str, str] = field(default_factory=dict)

    def to_toml_dict(self) -> dict[str, Any]:
        """Convert the config to a dictionary suitable for TOML serialization."""
        poetry_dict = {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "authors": self.authors,
            "readme": self.readme,
            "requires-python": self.requires_python,
            "dependencies": dict(self.dependencies),
        }

        # Add optional fields if they exist
        if self.license:
            poetry_dict["license"] = self.license

        # Add URLs
        urls = {}
        if self.homepage:
            urls["homepage"] = self.homepage
        if self.repository:
            urls["repository"] = self.repository
        if self.documentation:
            urls["documentation"] = self.documentation
        if urls:
            poetry_dict["urls"] = urls

        if self.keywords:
            poetry_dict["keywords"] = self.keywords
        if self.classifiers:
            poetry_dict["classifiers"] = self.classifiers

        # Create dev dependencies group
        dev_deps = dict(self.dev_dependencies)
        if dev_deps:
            poetry_dict["group"] = {"dev": {"dependencies": dev_deps}}

        # Build the full structure
        return {
            "tool": {"poetry": poetry_dict},
            "build-system": {
                "requires": ["poetry-core>=1.0.0"],
                "build-backend": "poetry.core.masonry.api",
            },
        }


def load_pyproject(file_path: Path) -> PyProjectConfig | None:
    """Load an existing pyproject.toml file into a PyProjectConfig object."""
    if not file_path.exists():
        return None

    try:
        data = tomllib.loads(file_path.read_text())

        poetry_data = data.get("tool", {}).get("poetry", {})
        if not poetry_data:
            logger.warning("No poetry configuration found in %s", file_path)
            return None

        # Extract URLs
        urls = poetry_data.get("urls", {})

        # Extract dependencies
        dependencies = poetry_data.get("dependencies", {})
        dev_group = poetry_data.get("group", {}).get("dev", {})
        dev_dependencies = dev_group.get("dependencies", {}) if dev_group else {}

        return PyProjectConfig(
            name=poetry_data.get("name", ""),
            version=poetry_data.get("version", "0.1.0"),
            description=poetry_data.get("description", ""),
            authors=poetry_data.get("authors", []),
            readme=poetry_data.get("readme", "README.md"),
            requires_python=poetry_data.get("requires-python", ">=3.12"),
            license=poetry_data.get("license"),
            homepage=urls.get("homepage"),
            repository=urls.get("repository"),
            documentation=urls.get("documentation"),
            keywords=poetry_data.get("keywords", []),
            classifiers=poetry_data.get("classifiers", []),
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
        )
    except Exception as e:
        logger.error("Error loading pyproject.toml: %s", str(e))
        return None


def select_classifiers(existing_classifiers: list[str] | None = None) -> list[str]:
    """Interactive classifier selection with fuzzy matching."""
    existing_classifiers = existing_classifiers or []
    selected_classifiers = existing_classifiers.copy()

    print("\nClassifier Selection (type to filter, Enter to select, empty line to finish)")
    print("Currently selected classifiers:")
    for clf in selected_classifiers:
        print(f"  - {clf}")

    while True:
        completer = FuzzyWordCompleter(PYPI_CLASSIFIERS)
        user_input = prompt(
            HTML("<b>Add classifier</b> (empty line to finish): "), completer=completer
        ).strip()

        if not user_input:
            break

        if user_input in PYPI_CLASSIFIERS and user_input not in selected_classifiers:
            selected_classifiers.append(user_input)
            print(f"Added: {user_input}")
        elif user_input not in PYPI_CLASSIFIERS:
            print("Classifier not found in common list. Add anyway? (y/n)")
            if input().lower() == "y":
                selected_classifiers.append(user_input)
                print(f"Added custom classifier: {user_input}")

    return selected_classifiers


def interactive_config(existing_config: PyProjectConfig | None = None) -> PyProjectConfig:
    """Interactive configuration builder for pyproject.toml."""
    if existing_config:
        logger.info("Editing existing configuration for %s", existing_config.name)
        config = existing_config
    else:
        name = prompt("Project name: ").strip()
        config = PyProjectConfig(name=name)

    # Basic information
    config.version = prompt("Version [0.1.0]: ", default=config.version).strip()
    config.description = prompt("Description: ", default=config.description).strip()

    # Authors
    authors_str = prompt(
        "Authors (comma separated, format: 'Name <email>'): ", default=", ".join(config.authors)
    ).strip()
    if authors_str:
        config.authors = [author.strip() for author in authors_str.split(",")]

    # Python version
    config.requires_python = prompt(
        "Required Python version [>=3.12]: ", default=config.requires_python
    ).strip()

    # License
    config.license = prompt("License [MIT]: ", default=config.license or "MIT").strip()

    # URLs
    config.homepage = prompt("Homepage URL: ", default=config.homepage or "").strip()
    config.repository = prompt("Repository URL: ", default=config.repository or "").strip()
    config.documentation = prompt("Documentation URL: ", default=config.documentation or "").strip()

    # Keywords
    keywords_str = prompt(
        "Keywords (comma separated): ", default=", ".join(config.keywords)
    ).strip()
    if keywords_str:
        config.keywords = [kw.strip() for kw in keywords_str.split(",")]

    # Classifiers
    config.classifiers = select_classifiers(config.classifiers)

    # Dependencies
    print("\nDependencies can be added with 'poetry add'")

    return config


def save_pyproject(config: PyProjectConfig, file_path: Path) -> None:
    """Save the configuration to a pyproject.toml file."""
    toml_dict = config.to_toml_dict()

    try:
        import tomli_w

        toml_bytes = tomli_w.dumps(toml_dict).encode("utf-8")
        file_path.write_bytes(toml_bytes)
        logger.info("Successfully saved configuration to %s", file_path)
    except Exception as e:
        logger.error("Error saving pyproject.toml: %s", str(e))


@handle_interrupt()
def main():
    """Main function to run the interactive pyproject.toml generator."""
    logger.warning("This tool is unfinished and still under development. Use at your own risk.")

    parser = PolyArgs(description="Enhanced pyproject.toml generator")
    parser.add_argument(
        "--file",
        "-f",
        default="pyproject.toml",
        help="path to pyproject.toml file (default: pyproject.toml)",
    )
    parser.add_argument(
        "--add", action="store_true", help="add to or modify an existing pyproject.toml file"
    )

    args = parser.parse_args()

    file_path = Path(args.file)
    existing_config = None

    if file_path.exists() and args.add:
        existing_config = load_pyproject(file_path)
        if not existing_config:
            logger.error("Could not load existing pyproject.toml file")
            sys.exit(1)
    elif file_path.exists() and not args.add:
        logger.warning("%s already exists. Use --add to modify it or remove it first.", file_path)
        sys.exit(1)

    config = interactive_config(existing_config)
    save_pyproject(config, file_path)

    logger.info("Next steps:")
    logger.info("  1. Add dependencies: poetry add pkg1 pkg2 pkg3")
    logger.info("  2. Add dev dependencies: poetry add --group dev pytest black")
    logger.info("  3. Initialize git repository (if needed): git init")


if __name__ == "__main__":
    main()
