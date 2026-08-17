#!/usr/bin/env python3

"""
Heuristic English sentence tokenizer.

Index-based scanner inspired by the answer of D Greenberg in
StackOverflow:
https://stackoverflow.com/questions/4576077/python-split-text-on-sentences

The input text is never mutated, only sliced: every sentence returned is
a literal substring of the input, by construction. When a rule is in
doubt, it does not split — a missed boundary is preferred over a
spurious one.
"""

import re
from typing import Final

__all__ = ["tokenize", "tokenize_spans"]

_CANDIDATE_RE: Final[re.Pattern[str]] = re.compile(r"[.!?]")

# Word token ending right before a candidate mark. Apostrophes are
# word-internal so contractions ("don't") are not mistaken for
# single-letter initials; dots are word-internal so dotted abbreviations
# arrive whole ("U.S.A", "p.m", "e.g").
_TOKEN_BEFORE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?<!['’0-9A-Za-z])([A-Za-z]+(?:['’.][A-Za-z]+)*)\Z"
)
_WORD_RE: Final[re.Pattern[str]] = re.compile(r"[A-Za-z]+")

# Longest listed token is far shorter than this: a fixed lookbehind
# window keeps _token_before O(1) per candidate.
_TOKEN_WINDOW: Final[int] = 24

_TERMINALS: Final[frozenset[str]] = frozenset({".", "!", "?"})
_CLOSERS: Final[frozenset[str]] = frozenset({'"', "”", "'", "’", ")", "]"})
_OPENERS: Final[frozenset[str]] = frozenset({'"', "“", "'", "‘", "(", "["})

# Titles precede a proper name; a dot after them never ends a sentence.
# Case-sensitive on purpose: "col." the noun is not "Col." the rank.
_TITLES: Final[frozenset[str]] = frozenset(
    {
        "Mr",
        "Mrs",
        "Ms",
        "Mx",
        "Dr",
        "Prof",
        "Rev",
        "Fr",
        "Hon",
        "Pres",
        "Sen",
        "Rep",
        "Gov",
        "Gen",
        "Adm",
        "Cmdr",
        "Col",
        "Maj",
        "Capt",
        "Cpt",
        "Lt",
        "Sgt",
        "Cpl",
        "Pvt",
        "Brig",
        "Det",
        "St",
        "Mt",
        "Ft",
    }
)

# Latin connectives that point forward; they cannot close a sentence.
# "etc" is deliberately absent: "etc." does end sentences, and the
# lowercase-next rule already keeps "etc. and bananas" together.
_FORWARD_DOTTED: Final[frozenset[str]] = frozenset({"e.g", "i.e"})
_FORWARD_PLAIN: Final[frozenset[str]] = frozenset({"cf", "vs", "viz"})

_AMPM: Final[frozenset[str]] = frozenset({"a.m", "p.m"})

# Abbreviations that bind to a number right after them ("No. 5",
# "Fig. 3", "pp. 12", "ca. 1900").
_NUM_ABBREVS: Final[frozenset[str]] = frozenset(
    {
        "No",
        "Nos",
        "Fig",
        "Figs",
        "Eq",
        "Eqs",
        "Ch",
        "Sec",
        "Art",
        "Vol",
        "Vols",
        "Op",
        "pp",
        "ca",
        "approx",
        "est",
    }
)

# Name/company suffixes: sentence-final only before a starter word,
# because "Nike Inc. CEO said..." is one noun phrase. "al" covers
# "et al.".
_CONDITIONAL_ABBREVS: Final[frozenset[str]] = frozenset(
    {
        "Inc",
        "Ltd",
        "Jr",
        "Sr",
        "Co",
        "Corp",
        "Bros",
        "Esq",
        "al",
    }
)

# Words that reliably begin a new sentence after an ambiguous
# abbreviation. "I", "A" and "An" are excluded: they collide with
# initials ("E. I. du Pont") and with names. Matched as a whole
# case-sensitive word, so "Theatre" is not "The".
_BASE_STARTERS: Final[frozenset[str]] = frozenset(
    {
        "He",
        "She",
        "It",
        "They",
        "We",
        "You",
        "His",
        "Her",
        "Its",
        "Their",
        "Our",
        "My",
        "Your",
        "This",
        "That",
        "These",
        "Those",
        "The",
        "There",
        "But",
        "However",
        "Wherever",
    }
)
_STARTERS: Final[frozenset[str]] = _BASE_STARTERS | _TITLES


def _extend_closers(text: str, i: int) -> int:
    """Absorb closing quotes/brackets glued after a terminal mark."""
    while i < len(text) and text[i] in _CLOSERS:
        i += 1
    return i


def _peek_significant(text: str, i: int) -> int:
    """Index of the next character that is not whitespace or an opener."""
    while i < len(text) and (text[i].isspace() or text[i] in _OPENERS):
        i += 1
    return i


def _token_before(text: str, i: int) -> str | None:
    """Word token (dots/apostrophes internal) ending right at i."""
    window = text[max(0, i - _TOKEN_WINDOW) : i]
    match = _TOKEN_BEFORE_RE.search(window)
    if match is None:
        return None
    return match.group(1)


def _next_word(text: str, i: int) -> str | None:
    """Alphabetic word starting exactly at i, if any."""
    match = _WORD_RE.match(text, i)
    if match is None:
        return None
    return match.group(0)


def _splits_before(text: str, k: int) -> bool:
    """Whether the word at k is a safe sentence starter."""
    return _next_word(text, k) in _STARTERS


def _is_boundary(text: str, i: int) -> bool:
    """Decide whether the terminal mark at i ends a sentence."""
    nxt = i + 1

    # R1: in a run of terminal punctuation ("?!", "...") only the last
    # mark decides.
    if nxt < len(text) and text[nxt] in _TERMINALS:
        return False

    # R2: no dot of an ellipsis is a boundary (parity with 0.3).
    if text[i] == "." and i > 0 and text[i - 1] == ".":
        return False

    # R3: a mark glued to a following word character never splits.
    # Covers decimals (3.14), versions (1.5.2), domains with ANY TLD
    # (example.dev), filenames and e-mails — no TLD list needed.
    if nxt < len(text) and text[nxt].isalnum():
        return False

    # R4: absorb closing quotes/brackets; another terminal right after
    # them means an enclosing sentence is still open — defer to it.
    j = _extend_closers(text, nxt)
    if j < len(text) and text[j] in _TERMINALS:
        return False

    # R5: peek at the next significant character.
    k = _peek_significant(text, j)
    if k == len(text):
        return True
    if text[k].islower():
        return False
    if text[i] != ".":
        return True

    token = _token_before(text, i)
    if token is None:
        # Digits, closers or nothing before the dot: plain boundary.
        return True

    # R6: titles never end a sentence.
    if token in _TITLES:
        return False

    lowered = token.lower()

    # R7: forward-pointing latinisms never end a sentence.
    if lowered in _FORWARD_DOTTED or lowered in _FORWARD_PLAIN:
        return False

    # R8: numeric abbreviations bind to the number that follows.
    if token in _NUM_ABBREVS and text[k].isdigit():
        return False

    # R9: single-letter initials split only before a starter word.
    if len(token) == 1:
        return _splits_before(text, k)

    # R10: dotted tokens. Pure acronyms ("U.S.A", "a.m") split only
    # before a starter; rare all-lowercase ones ("f.o.b") never do.
    # Tokens with a multi-letter segment ("acme.co", "Ph.D") behave
    # like ordinary words.
    if "." in token:
        if all(len(part) == 1 for part in token.split(".")):
            if token == lowered and lowered not in _AMPM:
                return False
            return _splits_before(text, k)
        return True

    # R11: name/company suffixes split only before a starter word.
    if token in _CONDITIONAL_ABBREVS:
        return _splits_before(text, k)

    # R12: an ordinary word before the dot — sentence boundary.
    return True


def tokenize_spans(text: str) -> list[tuple[int, int]]:
    """
    Half-open [start, end) spans of the sentences in text.

    Spans are trimmed of surrounding whitespace, never overlap, and the
    gaps between them contain only whitespace: text[start:end] is each
    sentence verbatim.
    """
    spans: list[tuple[int, int]] = []
    start = 0
    for match in _CANDIDATE_RE.finditer(text):
        i = match.start()
        if not _is_boundary(text, i):
            continue
        end = _extend_closers(text, i + 1)
        while start < end and text[start].isspace():
            start += 1
        spans.append((start, end))
        start = end
    # Trailing text without terminal punctuation is the last sentence.
    while start < len(text) and text[start].isspace():
        start += 1
    if start < len(text):
        end = len(text)
        while text[end - 1].isspace():
            end -= 1
        spans.append((start, end))
    return spans


def tokenize(text: str) -> list[str]:
    """Split English text into sentences (literal substrings of text)."""
    return [text[a:b] for a, b in tokenize_spans(text)]
