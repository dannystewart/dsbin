#!/usr/bin/env python3

"""Compare two lists and output common/unique elements.

Takes two lists of elements and outputs common elements and elements unique to each list.
It can ignore case sensitivity when comparing, and supports titles for each list.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import inquirer
from polykit.cli import handle_interrupt
from polykit.core import polykit_setup
from polykit.formatters import color, print_color

polykit_setup()


def process_lists(
    ignore_case: bool,
    list1: list[str],
    list2: list[str],
    title1: str = "first",
    title2: str = "second",
    comma_separated: bool = False,
    output_file: str | None = None,
) -> None:
    """Process two lists and compare them based on the specified case sensitivity.

    If case sensitivity is enabled, also display a message indicating how many additional elements
    would match if case sensitivity were ignored.

    Args:
        ignore_case: Whether the comparison should be case-insensitive.
        list1: The first list.
        list2: The second list.
        title1: The title for the first list. Defaults to None.
        title2: The title for the second list. Defaults to None.
        comma_separated: Whether to print results comma-separated. Defaults to False.
        output_file: The file to write the results to. Defaults to None.
    """
    set1, set2 = (
        (set(map(str.lower, list1)), set(map(str.lower, list2)))
        if ignore_case
        else (set(list1), set(list2))
    )
    common_elements = sorted(set1 & set2, key=lambda s: s.casefold() if ignore_case else s)
    unique_in_set1 = sorted(set1 - set2, key=lambda s: s.casefold() if ignore_case else s)
    unique_in_set2 = sorted(set2 - set1, key=lambda s: s.casefold() if ignore_case else s)

    output_lines = []
    print_results("Common elements", common_elements, ignore_case, comma_separated, output_lines)
    print_results(
        f"Unique in {title1} list", unique_in_set1, ignore_case, comma_separated, output_lines
    )
    print_results(
        f"Unique in {title2} list", unique_in_set2, ignore_case, comma_separated, output_lines
    )

    if not ignore_case:
        additional_matches = count_case_insensitive_matches(list1, list2, common_elements)
        if additional_matches > 0:
            note = f"\nNote: {additional_matches} additional elements would match if case sensitivity were ignored."
            print_color(note, "yellow")
            if output_file:
                output_lines.extend(("", note))

    if output_file:
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("\n".join(output_lines))
            print_color(f"\nResults saved to {output_path}.", "green")
        except OSError as e:
            print_color(f"\nError writing to file {output_path}: {e}", "red")
        except Exception as e:
            print_color(f"\nUnexpected error: {e}", "red")


def count_case_insensitive_matches(
    list1: list[str],
    list2: list[str],
    common_elements: list[str],
) -> int:
    """Count the number of matches between two lists.

    Counts regardless of case (excluding common elements). Used for reporting what the difference
    would be if case sensitivity were ignored, in case it affects the results.

    Args:
        list1: The first list.
        list2: The second list.
        common_elements: The list of common elements.

    Returns:
        The number of additional matches.
    """
    combined_unique = set(list1) | set(list2) - set(common_elements)
    case_folded = {x.lower() for x in combined_unique}
    return len(combined_unique) - len(case_folded)


def input_until_sentinel(sentinel: str = ".") -> list[str]:
    """Take user input until a sentinel value is entered. Store each input line in a list.

    Args:
        sentinel: The sentinel value to stop taking input. Defaults to '.' (period).

    Returns:
        list: The list of input lines.
    """
    lines = []
    while True:
        line = input().strip()
        if line == sentinel:
            break
        lines.append(line)
    return lines


def print_results(
    header: str,
    elements_list: list[str],
    case_insensitive: bool,
    comma_separated: bool = False,
    output_lines: list[str] | None = None,
) -> None:
    """Print the results of a list of elements with an optional header.

    Args:
        header: The header to print.
        elements_list: The list of elements to print.
        case_insensitive: Whether the comparison was case-insensitive.
        comma_separated: Whether to print results comma-separated. Defaults to False.
        output_lines: List to append output lines to for file writing. Defaults to None.
    """
    count = len(elements_list)
    case_notice = "" if case_insensitive else " case-sensitive"
    header_text = f"\n{header} ({count}{case_notice}):"
    if comma_separated:
        elements = ", ".join(elements_list) if elements_list else "None"
    else:
        elements = "\n".join(elements_list) if elements_list else "None"

    print_color(header_text, "yellow")
    print_color(elements, "blue")

    if output_lines is not None and output_lines:
        # If this isn't the first section, add a blank line before the header
        output_lines.extend(("", header_text.strip(), elements))
    elif output_lines:
        output_lines.extend((header_text.strip(), elements))


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-c",
        "--case",
        action="store_true",
        help="show menu for selecting case mode",
    )
    parser.add_argument(
        "--no-titles",
        action="store_true",
        help="skip asking for list titles",
    )
    parser.add_argument(
        "--comma-separated",
        action="store_true",
        help="print results comma-separated",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="save results to the specified file",
    )
    return parser.parse_args()


@handle_interrupt()
def main() -> None:
    """Compare two lists."""
    ignore_case = True
    title1, title2 = "first", "second"
    args = parse_arguments()

    if args.case:
        case_ins_str = "Case-insensitive ('Apple' and 'apple' are the same)"
        case_sen_str = "Case-sensitive ('Apple' and 'apple' are different)"

        case_sensitivity_question = [
            inquirer.List(
                "case_mode",
                message="Select mode",
                choices=[case_ins_str, case_sen_str],
            ),
        ]
        answers = inquirer.prompt(case_sensitivity_question)
        if answers:
            ignore_case = answers["case_mode"] == case_ins_str

    skip_titles = False
    if not args.no_titles:
        if title1_in := input(
            color("Enter a title for the first list (or press Enter to skip): ", "green")
        ):
            title1 = title1_in
        else:
            skip_titles = True  # Skip second title if first title was skipped

        if not skip_titles and (
            title2_in := input(
                color("Enter a title for the second list (or press Enter to skip): ", "green")
            )
        ):
            title2 = title2_in

    print_color(f"Paste the {title1} list (type '.' and press Enter to finish):", "green")
    list1 = input_until_sentinel()

    print_color(f"\nPaste the {title2} list (type '.' and press Enter to finish):", "green")
    list2 = input_until_sentinel()

    process_lists(ignore_case, list1, list2, title1, title2, args.comma_separated, args.output)


if __name__ == "__main__":
    main()
