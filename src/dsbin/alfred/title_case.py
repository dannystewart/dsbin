#!/usr/bin/env python3

"""
titlecase.py v0.2
Original Perl version by: John Gruber http://daringfireball.net/ 10 May 2008
Python version by Stuart Colville http://muffinresearch.co.uk
License: http://www.opensource.org/licenses/mit-license.php.

This one was modified by Danny Stewart.
"""

import re
import sys
import unittest

SMALL = r"a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs\.?"
PUNCT = "[!\"#$%&'‘()*+,-./:;?@[\\\\\\]_`{|}~]"

SMALL_WORDS = re.compile(rf"^({SMALL})$", re.I)
INLINE_PERIOD = re.compile(r"[a-zA-Z][.][a-zA-Z]")
UC_ELSEWHERE = re.compile(rf"{PUNCT}*?[a-zA-Z]+[A-Z]+?")
CAPFIRST = re.compile(rf"^{PUNCT}*?([A-Za-z])")
SMALL_FIRST = re.compile(rf"^({PUNCT}*)({SMALL})\b", re.I)
SMALL_LAST = re.compile(rf"\b({SMALL}){PUNCT}?$", re.I)
SUBPHRASE = re.compile(rf"([:.;?!][ ])({SMALL})")


def title_case(text: str) -> str:
    """
    Titlecases input text.

    This filter changes all words to Title Caps, and attempts to be clever
    about *un*capitalizing SMALL words like a/an/the in the input.

    The list of "SMALL words" which are not capped comes from
    the New York Times Manual of Style, plus 'vs' and 'v'.

    """

    words = re.split(r"\s", text)
    line = []
    for word in words:
        if INLINE_PERIOD.search(word) or UC_ELSEWHERE.match(word):
            line.append(word)
            continue
        if SMALL_WORDS.match(word):
            line.append(word.lower())
            continue
        line.append(CAPFIRST.sub(lambda m: m.group(0).upper(), word))

    line = " ".join(line)

    line = SMALL_FIRST.sub(lambda m: f"{m.group(1)}{m.group(2).capitalize()}", line)

    line = SMALL_LAST.sub(lambda m: m.group(0).capitalize(), line)

    return SUBPHRASE.sub(lambda m: f"{m.group(1)}{m.group(2).capitalize()}", line)


class TitlecaseTests(unittest.TestCase):
    """Tests to ensure titlecase follows all of the rules."""

    def test_q_and_a(self) -> None:
        """Testing: Q&A With Steve Jobs: 'That's What Happens In Technology'."""
        text = title_case("Q&A with steve jobs: 'that's what happens in technology'")
        result = "Q&A With Steve Jobs: 'That's What Happens in Technology'"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_at_and_t(self) -> None:
        """Testing: What Is AT&T's Problem?."""

        text = title_case("What is AT&T's problem?")
        result = "What Is AT&T's Problem?"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_apple_deal(self) -> None:
        """Testing: Apple Deal With AT&T Falls Through."""

        text = title_case("Apple deal with AT&T falls through")
        result = "Apple Deal With AT&T Falls Through"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_this_v_that(self) -> None:
        """Testing: this v that."""
        text = title_case("this v that")
        result = "This v That"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_this_v_that2(self) -> None:
        """Testing: this v. that."""

        text = title_case("this v. that")
        result = "This v. That"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_this_vs_that(self) -> None:
        """Testing: this vs that."""

        text = title_case("this vs that")
        result = "This vs That"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_this_vs_that2(self) -> None:
        """Testing: this vs. that."""

        text = title_case("this vs. that")
        result = "This vs. That"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_apple_sec(self) -> None:
        """Testing: The SEC's Apple Probe: What You Need to Know."""

        text = title_case("The SEC's Apple Probe: What You Need to Know")
        result = "The SEC's Apple Probe: What You Need to Know"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_small_word_quoted(self) -> None:
        """Testing: 'by the Way, Small word at the start but within quotes.'."""

        text = title_case("'by the Way, small word at the start but within quotes.'")
        result = "'By the Way, Small Word at the Start but Within Quotes.'"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_small_word_end(self) -> None:
        """Testing: Small word at end is nothing to be afraid of."""

        text = title_case("Small word at end is nothing to be afraid of")
        result = "Small Word at End Is Nothing to Be Afraid Of"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_sub_phrase_small_word(self) -> None:
        """Testing: Starting Sub-Phrase With a Small Word: a Trick, Perhaps?."""

        text = title_case("Starting Sub-Phrase With a Small Word: a Trick, Perhaps?")
        result = "Starting Sub-Phrase With a Small Word: A Trick, Perhaps?"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_small_word_quotes(self) -> None:
        """Testing: Sub-Phrase With a Small Word in Quotes: 'a Trick...."""

        text = title_case("Sub-Phrase With a Small Word in Quotes: 'a Trick, Perhaps?'")
        result = "Sub-Phrase With a Small Word in Quotes: 'A Trick, Perhaps?'"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_small_word_double_quotes(self) -> None:
        r"""Testing: Sub-Phrase With a Small Word in Quotes: \"a Trick...."""
        text = title_case('Sub-Phrase With a Small Word in Quotes: "a Trick, Perhaps?"')
        result = 'Sub-Phrase With a Small Word in Quotes: "A Trick, Perhaps?"'
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_nothing_to_be_afraid_of(self) -> None:
        r"""Testing: \"Nothing to Be Afraid of?\" ."""
        text = title_case('"Nothing to Be Afraid of?"')
        result = '"Nothing to Be Afraid Of?"'
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_nothing_to_be_afraid_of2(self) -> None:
        r"""Testing: \"Nothing to Be Afraid Of?\" ."""

        text = title_case('"Nothing to be Afraid Of?"')
        result = '"Nothing to Be Afraid Of?"'
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_a_thing(self) -> None:
        """Testing: a thing."""

        text = title_case("a thing")
        result = "A Thing"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_vapourware(self) -> None:
        """Testing: 2lmc Spool: 'Gruber on OmniFocus and Vapo(u)rware'."""
        text = title_case("2lmc Spool: 'gruber on OmniFocus and vapo(u)rware'")
        result = "2lmc Spool: 'Gruber on OmniFocus and Vapo(u)rware'"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_domains(self) -> None:
        """Testing: this is just an example.com."""
        text = title_case("this is just an example.com")
        result = "This Is Just an example.com"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_domains2(self) -> None:
        """Testing: this is something listed on an del.icio.us."""

        text = title_case("this is something listed on del.icio.us")
        result = "This Is Something Listed on del.icio.us"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_itunes(self) -> None:
        """Testing: iTunes should be unmolested."""

        text = title_case("iTunes should be unmolested")
        result = "iTunes Should Be Unmolested"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_thoughts_on_music(self) -> None:
        """Testing: Reading Between the Lines of Steve Jobs’s...."""

        text = title_case("Reading between the lines of steve jobs’s ‘thoughts on music’")
        result = "Reading Between the Lines of Steve Jobs’s ‘Thoughts on Music’"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_repair_perms(self) -> None:
        """Testing: Seriously, ‘Repair Permissions’ Is Voodoo."""

        text = title_case("seriously, ‘repair permissions’ is voodoo")
        result = "Seriously, ‘Repair Permissions’ Is Voodoo"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )

    def test_generalissimo(self) -> None:
        """Testing: Generalissimo Francisco Franco...."""

        text = title_case(
            "generalissimo francisco franco: still dead; kieren McCarthy: still a jackass"
        )
        result = "Generalissimo Francisco Franco: Still Dead; Kieren McCarthy: Still a Jackass"
        self.assertEqual(
            text,
            result,
            f"{text} should be: {result}",
        )


if __name__ == "__main__":
    if not sys.stdin.isatty():
        for line in sys.stdin:
            print(title_case(line))  # noqa: T201

    else:
        suite = unittest.TestLoader().loadTestsFromTestCase(TitlecaseTests)
        unittest.TextTestRunner(verbosity=2).run(suite)
