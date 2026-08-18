#!/usr/bin/env python3

"""
Property-based fuzzing of the span invariants.

The scanner's guarantees (verbatim slices, ordered non-overlapping
spans trimmed of whitespace, whitespace-only gaps) hold for ANY input,
linguistic or not. That makes them ideal for fuzzing: Hypothesis can
hunt for offset corruption, lost characters and crashes without
knowing what the correct segmentation would be.
"""

from hypothesis import given
from hypothesis import settings
from hypothesis import strategies as st

from tokenizesentences import tokenize
from tokenizesentences import tokenize_spans

# Characters the boundary rules actually react to, plus troublemakers:
# accents, curly quotes, guillemets, PUA, emoji, CRLF.
PUNCTUATION_ALPHABET = (
    "abcdeghinorstuwABDEGHIMNOPSTUW"
    "éñüÉÑÜ"
    "0123459"
    ".!?…"
    "\"'“”‘’«»()[]<>"
    ",;:/&@$%=+-_~°º"
    " \t\n\r"
    "\U0001f600"
)

# Tokens that steer generated text into every rule family.
VOCAB = [
    "Mr.",
    "Dr.",
    "Inc.",
    "Ltd.",
    "et",
    "al.",
    "U.S.A.",
    "Ph.D.",
    "p.m.",
    "a.m.",
    "e.g.",
    "i.e.",
    "etc.",
    "No.",
    "N°.",
    "Jan.",
    "Fig.",
    "pop.",
    "3.14",
    "1.5.2",
    "example.dev",
    "index.ssf?/x",
    "./configure",
    "<stop>",
    "<prd>",
    "don't",
    "’90s",
    "...",
    ". . .",
    "..!",
    "“Hi.”",
    "«Hola.»",
    "(quietly. )",
    "Hello. ”",
    "word.",
    "word",
    "Then",
    "then",
    "I",
    "He",
    "José.",
    "It works!",
    "What?",
    "5.",
    ".",
    "!",
    "?",
    "\n\n",
    ":)",
]


def _check_invariants(text: str) -> None:
    spans = tokenize_spans(text)
    sentences = tokenize(text)
    assert [text[a:b] for a, b in spans] == sentences
    previous = 0
    for start, end in spans:
        assert 0 <= previous <= start < end <= len(text)
        assert not text[start].isspace()
        assert not text[end - 1].isspace()
        assert text[previous:start].strip() == ""
        previous = end
    assert text[previous:].strip() == ""


@given(st.text(max_size=300))
@settings(max_examples=200, deadline=None)
def test_arbitrary_unicode_text(text: str) -> None:
    """Any Unicode input at all: no crash, no invariant violation."""
    _check_invariants(text)


@given(st.text(alphabet=PUNCTUATION_ALPHABET, max_size=400))
@settings(max_examples=200, deadline=None)
def test_punctuation_heavy_text(text: str) -> None:
    """Dense punctuation stresses every boundary rule at once."""
    _check_invariants(text)


@given(st.lists(st.sampled_from(VOCAB), max_size=40))
@settings(max_examples=200, deadline=None)
def test_token_salad(tokens: list[str]) -> None:
    """Realistic-ish word salad built from the rule families."""
    _check_invariants(" ".join(tokens))
