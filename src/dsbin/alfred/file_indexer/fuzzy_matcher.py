from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config_handler import Config


class FuzzyMatcher:
    """
    Class to generate multiple match strings for advanced fuzzy matching.

    Fuzzy Matching Parameters:

    - min_length: The minimum length of substrings to generate for matching. Smaller values increase
      matching flexibility but may introduce more false positives. (Default: 3)

    - max_length: The maximum length of substrings to generate for general matching throughout the
      filename. Larger values allow for more precise matches but increase processing time and memory
      usage. (Default: 6)

    - start_max: The maximum length of substrings to generate from the start of the filename. This
      allows for longer matches at the beginning of filenames, which can be particularly useful for
      files with long, descriptive names. (Default: 8)

    These parameters work together to balance between matching flexibility and performance.
    Additionally, they can all be set to 0 to bypass fuzzy matching entirely.
    """

    def __init__(self, config: Config):
        self.config = config
        self.min_length = config.min_length
        self.max_length = config.max_length
        self.start_max = config.start_max
        self.bypass_fuzzy = self.min_length == 0 and self.max_length == 0 and self.start_max == 0

    def generate_match_strings(self, filename: str) -> str:
        """Generate multiple match strings for advanced fuzzy matching."""
        if self.bypass_fuzzy:
            return filename.lower()  # Return just the lowercase filename when bypassing

        basic_matches, substring_matches, complex_matches = self._generate_matches(filename)

        match_strings = set()
        match_strings.update(basic_matches)
        match_strings.update(substring_matches)
        match_strings.update(complex_matches)

        return " ".join(match_strings)

    def _generate_matches(self, filename: str) -> tuple[set[str], set[str], set[str]]:
        name_without_ext = os.path.splitext(filename)[0]
        clean_name = name_without_ext.replace("_", " ").replace("-", " ").lower()
        words = clean_name.split()
        full_name = "".join(words)

        basic_matches = self._generate_basic_matches(words, name_without_ext)
        substring_matches = self._generate_substring_matches(full_name)
        complex_matches = self._generate_complex_matches(full_name, words)

        return basic_matches, substring_matches, complex_matches

    def _generate_basic_matches(self, words: list[str], name_without_ext: str) -> set[str]:
        """Generate basic match strings."""
        match_strings = set()
        full_name = "".join(words)
        match_strings.add(full_name)
        match_strings.add(name_without_ext.lower())
        match_strings.update(words)
        acronym = "".join(word[0] for word in words)
        match_strings.add(acronym)
        return match_strings

    def _generate_substring_matches(self, full_name: str) -> set[str]:
        """Generate substring matches."""
        match_strings = set()
        for length in range(self.min_length, self.max_length + 1):
            for i in range(len(full_name) - length + 1):
                match_strings.add(full_name[i : i + length])
        for i in range(self.max_length + 1, min(self.start_max + 1, len(full_name) + 1)):
            match_strings.add(full_name[:i])
        return match_strings

    def _generate_complex_matches(self, full_name: str, words: list[str]) -> set[str]:
        """Generate more complex match combinations."""
        match_strings = set()

        # Combinations of n letters + m letters from later in the name
        for n in range(3, self.max_length):
            for i in range(len(full_name) - n):
                for m in range(1, self.max_length - n + 1):
                    for j in range(i + n, len(full_name) - m + 1):
                        match_strings.add(full_name[i : i + n] + full_name[j : j + m])

        # Combinations of first n letters of each word + m letters from any following word
        for i, word in enumerate(words):
            for n in range(2, min(len(word) + 1, self.max_length)):
                for j in range(i + 1, len(words)):
                    for m in range(1, min(len(words[j]) + 1, self.max_length - n + 1)):
                        match_strings.add(word[:n] + words[j][:m])

        return match_strings
