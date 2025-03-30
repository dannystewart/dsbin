#!/usr/bin/env python3

from __future__ import annotations

import re
import sys
import textwrap


def _get_indent_and_stripped(line: str) -> tuple[str, str]:
    """Extract indentation and content from a line."""
    stripped = line.lstrip()
    indent = line[: len(line) - len(stripped)]
    return indent, stripped


def _handle_single_line_docstring(line: str, i: int, result: list[str]) -> int:
    """Handle a single-line docstring."""
    result.append(line)
    return i + 1


def _handle_multi_line_docstring(lines: list[str], i: int, result: list[str]) -> int:
    """Handle a multi-line docstring block."""
    line = lines[i]
    indent, stripped = _get_indent_and_stripped(line)
    quote_type = '"""' if stripped.startswith('"""') else "'''"

    # Start of multi-line docstring
    docstring_lines = [stripped[3:]]  # Remove opening quotes
    i += 1

    # Collect all lines until closing quote
    while i < len(lines) and not lines[i].rstrip().endswith(quote_type):
        docstring_lines.append(lines[i].strip())
        i += 1

    # Add the closing line without the quotes
    if i < len(lines):
        closing_line = lines[i].rstrip()
        if closing_line.endswith(quote_type):
            docstring_lines.append(closing_line[:-3].strip())
        i += 1

    # Join the docstring content and add back the quotes
    joined_content = " ".join(line for line in docstring_lines if line)
    result.append(f"{indent}{quote_type}{joined_content}{quote_type}")
    return i


def _handle_docstring_block(lines: list[str], i: int, result: list[str]) -> int:
    """Handle a docstring block."""
    line = lines[i]
    stripped = line.lstrip()

    quote_type = '"""' if stripped.startswith('"""') else "'''"
    # Check if it's a single-line docstring
    if stripped[3:].endswith(quote_type):
        return _handle_single_line_docstring(line, i, result)
    return _handle_multi_line_docstring(lines, i, result)


def _handle_comment_block(lines: list[str], i: int, result: list[str]) -> int:
    """Handle a comment block."""
    line = lines[i]
    indent, stripped = _get_indent_and_stripped(line)

    # Collect all consecutive comment lines
    comment_lines = [stripped[1:].lstrip()]  # Remove # and leading space
    j = i + 1
    while j < len(lines) and lines[j].lstrip().startswith("#"):
        comment_lines.append(lines[j].lstrip()[1:].lstrip())
        j += 1

    # Join the comment content and add back the #
    joined_content = " ".join(line for line in comment_lines if line)
    result.append(f"{indent}# {joined_content}")
    return j


def _handle_argument_section(line: str, i: int, result: list[str]) -> int:
    """Handle section headers in docstrings."""
    result.append(line)
    return i + 1


def _handle_argument_description(lines: list[str], i: int, result: list[str]) -> int:
    """Handle argument descriptions in docstrings."""
    line = lines[i]
    indent, stripped = _get_indent_and_stripped(line)

    arg_match = re.match(r"^(\s*)([a-zA-Z0-9_]+)(\s*:)(.*)", stripped)
    if arg_match:
        arg_indent = arg_match.group(1)
        arg_name = arg_match.group(2)
        arg_colon = arg_match.group(3)
        arg_desc = arg_match.group(4).lstrip()

        # Collect continuation lines for this argument
        j = i + 1
        while (
            j < len(lines)
            and lines[j].strip()
            and not re.match(r"^\s+[a-zA-Z0-9_]+\s*:", lines[j].lstrip())
        ):
            if not any(
                section in lines[j].lstrip()
                for section in ("Args:", "Returns:", "Raises:", "Yields:", "Examples:")
            ) and not lines[j].lstrip().startswith(("#", "'''", '"""')):
                arg_desc += " " + lines[j].strip()
                j += 1
            else:
                break

        full_indent = indent + arg_indent
        result.append(f"{full_indent}{arg_name}{arg_colon} {arg_desc}")
        return j
    result.append(line)
    return i + 1


def _is_section_header(stripped: str) -> bool:
    """Check if a line is a section header."""
    return any(
        arg_section in stripped
        for arg_section in ("Args:", "Returns:", "Raises:", "Yields:", "Examples:")
    )


def unwrap_text(text: str) -> str:
    """Join lines that are part of the same logical block before re-wrapping."""
    lines = text.splitlines()
    result = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()

        # Handle docstring blocks
        if stripped.startswith(('"""', "'''")):
            i = _handle_docstring_block(lines, i, result)

        # Handle comments
        elif stripped.startswith("#"):
            i = _handle_comment_block(lines, i, result)

        # Handle argument sections in docstrings
        elif _is_section_header(stripped):
            i = _handle_argument_section(line, i, result)

        # Handle argument descriptions
        elif re.match(r"^\s+[a-zA-Z0-9_]+\s*:", stripped):
            i = _handle_argument_description(lines, i, result)

        # Regular text or empty lines
        else:
            result.append(line)
            i += 1

    return "\n".join(result)


def _handle_rewrap_comment_block(
    lines: list[str], i: int, result: list[str], indent: str, width: int
) -> int:
    """Handle comment blocks in the rewrap function."""
    stripped = lines[i].lstrip()
    comment_text = stripped[1:].lstrip()
    comment_block = [comment_text]

    # Look ahead for more comment lines with the same indentation
    j = i + 1
    while (
        j < len(lines)
        and lines[j].lstrip().startswith("#")
        and len(lines[j]) - len(lines[j].lstrip()) == len(indent)
    ):
        comment_block.append(lines[j].lstrip()[1:].lstrip())
        j += 1

    # Join and re-wrap the comment block
    joined_comment = " ".join(line for line in comment_block if line)
    wrapped_comment = textwrap.wrap(joined_comment, width=width - len(indent) - 2)

    if wrapped_comment:
        result.extend(f"{indent}# {w}" for w in wrapped_comment)
    else:
        result.append(f"{indent}#")

    return j


def _handle_rewrap_text_block(
    lines: list[str], i: int, result: list[str], indent: str, width: int
) -> int:
    """Handle regular text blocks in the rewrap function."""
    stripped = lines[i].lstrip()
    text_block = [stripped]
    j = i + 1

    while (
        j < len(lines)
        and len(lines[j]) - len(lines[j].lstrip()) == len(indent)
        and lines[j].strip()
        and not lines[j].lstrip().startswith(("#", "'''", '"""'))
        and not _is_section_header(lines[j].lstrip())
        and not re.match(r"^\s+[a-zA-Z0-9_]+\s*:", lines[j].lstrip())
    ):
        text_block.append(lines[j].strip())
        j += 1

    # Only join and rewrap if we found multiple lines
    if len(text_block) > 1:
        joined_text = " ".join(text_block)
        wrapped_text = textwrap.wrap(joined_text, width=width - len(indent))
        result.extend(f"{indent}{w}" for w in wrapped_text)
        return j
    # Use original wrapping logic for single lines
    result.append(lines[i])
    return i + 1


def rewrap_text(text: str, width: int = 100) -> str:
    """Unwrap and then re-wrap text while preserving structure."""
    # Preserve trailing newline if present
    has_trailing_newline = text.endswith("\n")

    lines = text.splitlines()
    result = []

    i = 0
    while i < len(lines):
        line = lines[i]
        indent, stripped = _get_indent_and_stripped(line)

        # Handle comment blocks - collect consecutive comment lines
        if stripped.startswith("#"):
            i = _handle_rewrap_comment_block(lines, i, result, indent, width)

        # Handle docstring content (without trying to find beginnings/endings)
        elif (
            i > 0
            and not lines[i - 1].lstrip().startswith(("#", "'''", '"""'))
            and stripped
            and not stripped.startswith(("'''", '"""'))
        ):
            i = _handle_rewrap_text_block(lines, i, result, indent, width)

        else:
            # For all other cases, use your original wrapping logic
            result.append(line)
            i += 1

    # Restore trailing newline if it was present
    output = "\n".join(result)
    if has_trailing_newline:
        output += "\n"

    return output


def _handle_wrap_docstring_line(line: str, indent: str, width: int, result: list[str]) -> None:
    """Handle docstring lines in the wrap function."""
    stripped = line.lstrip()
    quote_type = '"""' if stripped.startswith('"""') else "'''"
    content = stripped[3:]

    # If the line also ends with quotes, it's a complete docstring on one line
    if content.endswith(quote_type):
        content = content[:-3]
        wrapped = textwrap.wrap(content, width=width - len(indent) - 6)
        if wrapped:
            result.append(f"{indent}{quote_type}{wrapped[0]}")
            result.extend(f"{indent}{w}" for w in wrapped[1:])
            result[-1] += quote_type
        else:
            result.append(f"{indent}{quote_type}{quote_type}")
    else:
        # Just the opening line of a docstring
        wrapped = textwrap.wrap(content, width=width - len(indent) - 3)
        if wrapped:
            result.append(f"{indent}{quote_type}{wrapped[0]}")
            result.extend(f"{indent}{w}" for w in wrapped[1:])
        else:
            result.append(f"{indent}{quote_type}")


def _handle_wrap_closing_docstring(line: str, indent: str, width: int, result: list[str]) -> None:
    """Handle closing docstring line in the wrap function."""
    stripped = line.lstrip()
    quote_type = '"""' if stripped.endswith('"""') else "'''"
    content = stripped[:-3].rstrip()

    if content:
        wrapped = textwrap.wrap(content, width=width - len(indent) - 3)
        if wrapped:
            result.extend(f"{indent}{w}" for w in wrapped[:-1])
            result.append(f"{indent}{wrapped[-1]}{quote_type}")
        else:
            result.append(f"{indent}{quote_type}")
    else:
        result.append(f"{indent}{quote_type}")


def _handle_wrap_arg_description(line: str, indent: str, width: int, result: list[str]) -> None:
    """Handle argument description in the wrap function."""
    stripped = line.lstrip()
    arg_match = re.match(r"^(\s*)([a-zA-Z0-9_]+)(\s*:)(.*)", stripped)
    if arg_match:
        arg_indent = arg_match.group(1)
        arg_name = arg_match.group(2)
        arg_colon = arg_match.group(3)
        arg_desc = arg_match.group(4).lstrip()

        full_indent = indent + arg_indent

        # Calculate indentation for wrapped lines
        arg_prefix = arg_name + arg_colon + " "
        continuation_indent = " " * len(arg_prefix)

        if arg_desc:
            # Wrap the description with proper indentation
            wrapped_lines = textwrap.wrap(
                arg_desc,
                width=width - len(full_indent) - len(arg_prefix),
                initial_indent="",
                subsequent_indent="",
            )

            if wrapped_lines:
                result.append(f"{full_indent}{arg_prefix}{wrapped_lines[0]}")
                result.extend(f"{full_indent}{continuation_indent}{w}" for w in wrapped_lines[1:])
            else:
                result.append(f"{full_indent}{arg_prefix}")
        else:
            result.append(f"{full_indent}{arg_name}{arg_colon}")


def _handle_wrap_comment(line: str, indent: str, width: int, result: list[str]) -> None:
    """Handle comment in the wrap function."""
    stripped = line.lstrip()
    comment_text = stripped[1:].lstrip()
    wrapped = textwrap.wrap(comment_text, width=width - len(indent) - 2)
    if wrapped:
        result.extend(f"{indent}# {w}" for w in wrapped)
    else:
        result.append(f"{indent}#")


def _handle_wrap_regular_text(
    line: str, prev_line: str, indent: str, width: int, result: list[str]
) -> None:
    """Handle regular text or continuation of arg descriptions."""
    stripped = line.lstrip()
    # Check if this might be a continuation of an argument description
    if prev_line and re.match(r"^\s+[a-zA-Z0-9_]+\s*:", prev_line.lstrip()):
        arg_match = re.match(r"^(\s*)([a-zA-Z0-9_]+)(\s*:)", prev_line.lstrip())
        if arg_match:
            arg_prefix = arg_match.group(2) + arg_match.group(3) + " "
            continuation_indent = " " * len(arg_prefix)
            wrapped = textwrap.wrap(stripped, width=width - len(indent) - len(continuation_indent))
            result.extend(f"{indent}{continuation_indent}{w}" for w in wrapped)
            return

    # Regular text
    wrapped = textwrap.wrap(stripped, width=width - len(indent))
    if wrapped:
        result.extend(f"{indent}{w}" for w in wrapped)
    else:
        result.append(indent)


def wrap_individual_lines(text: str, width: int = 100) -> str:
    """Wrap text based on context."""
    # Preserve trailing newline if present
    has_trailing_newline = text.endswith("\n")

    lines = text.splitlines()
    result = []

    i = 0
    while i < len(lines):
        line = lines[i]
        indent, stripped = _get_indent_and_stripped(line)

        # Handle docstring lines (but don't try to be clever about finding endings)
        if stripped.startswith(('"""', "'''")):
            _handle_wrap_docstring_line(line, indent, width, result)

        # Handle closing docstring line
        elif stripped.endswith(('"""', "'''")):
            _handle_wrap_closing_docstring(line, indent, width, result)

        # Handle lines within a docstring that might have Args sections
        elif _is_section_header(stripped):
            result.append(line)  # Keep section headers as is

        # Handle argument descriptions
        elif re.match(r"^\s+[a-zA-Z0-9_]+\s*:", stripped):
            _handle_wrap_arg_description(line, indent, width, result)

        # Handle comments
        elif stripped.startswith("#"):
            _handle_wrap_comment(line, indent, width, result)

        # Handle regular text or continuation of arg descriptions
        elif stripped:
            prev_line = lines[i - 1] if i > 0 else ""
            _handle_wrap_regular_text(line, prev_line, indent, width, result)

        # Empty line
        else:
            result.append(line)

        i += 1

    # Restore trailing newline if it was present
    output = "\n".join(result)
    if has_trailing_newline:
        output += "\n"

    return output


def wrap_text(text: str, width: int = 100) -> str:
    """Wrap text based on context."""
    # First unwrap the text to join logical blocks
    text = unwrap_text(text)

    # Then apply the original wrapping logic to handle specific formatting
    return wrap_individual_lines(text, width)


if __name__ == "__main__":
    query = sys.argv[1]

    output_text = wrap_text(query)
    sys.stdout.write(output_text)
