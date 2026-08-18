#!/usr/bin/env python3

"""
Heuristic English sentence tokenizer.

Index-based scanner inspired by the answer of D Greenberg in
StackOverflow:
https://stackoverflow.com/questions/4576077/python-split-text-on-sentences

The input text is never mutated, only sliced: every sentence returned is
a literal substring of the input, by construction. When a rule is in
doubt, it does not split; a missed boundary is preferred over a
spurious one.
"""

import re
from typing import Final

__all__ = ["tokenize", "tokenize_spans"]

_CANDIDATE_RE: Final[re.Pattern[str]] = re.compile(r"[.!?]")

# A blank line (possibly holding spaces or tabs) always separates
# sentences, punctuation or not. A single newline never does: PDF and
# e-mail line wrapping would shatter sentences otherwise.
_PARAGRAPH_RE: Final[re.Pattern[str]] = re.compile(r"\n[ \t\r]*\n")

# Word token ending right before a candidate mark. Apostrophes are
# word-internal so contractions ("don't") are not mistaken for
# single-letter initials; dots are word-internal so dotted abbreviations
# arrive whole ("U.S.A", "p.m", "e.g"). Letters are Unicode ("José"),
# because English text in the wild carries accented names; the lists
# stay ASCII and English-only.
_TOKEN_BEFORE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?<!['’])(?<![^\W_])"
    r"((?:[^\W\d_]|[°º])+(?:['’.](?:[^\W\d_]|[°º])+)*)\Z"
)
_WORD_RE: Final[re.Pattern[str]] = re.compile(r"[^\W\d_]+")

# Longest listed token is far shorter than this: a fixed lookbehind
# window keeps _token_before O(1) per candidate.
_TOKEN_WINDOW: Final[int] = 24

_TERMINALS: Final[frozenset[str]] = frozenset({".", "!", "?"})
_CLOSERS: Final[frozenset[str]] = frozenset(
    {'"', "”", "'", "’", ")", "]", "»"}
)
_OPENERS: Final[frozenset[str]] = frozenset(
    {'"', "“", "'", "‘", "(", "[", "«"}
)

# Closers that cannot open: safe to absorb even across spaces. The
# straight quote and apostrophe are ambiguous and stay glued-only.
_DETACHED_CLOSERS: Final[frozenset[str]] = frozenset({"”", "’", ")", "]", "»"})
_HSPACE: Final[frozenset[str]] = frozenset({" ", "\t"})

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
# "Fig. 3", "pp. 12", "ca. 1900", "Jan. 15", "N°. 7"). The accepted
# cost runs in the conservative direction: a person named Jan, Jun or
# Dec followed by a digit-starting sentence stays joined.
_NUM_ABBREVS: Final[frozenset[str]] = frozenset(
    {
        "No",
        "Nos",
        "N°",
        "Nº",
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
        "pop",
        # Month abbreviations ("May" is never dotted).
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Sept",
        "Oct",
        "Nov",
        "Dec",
    }
)

# Abbreviations that end a sentence only before a starter word,
# because the capitalized word after them often continues the same
# noun phrase: "Nike Inc. CEO said...", "Natl. Grid stock rose",
# "Fifth Ave. Traffic was heavy". "al" covers "et al.".
_CONDITIONAL_ABBREVS: Final[frozenset[str]] = frozenset(
    {
        # Name and company suffixes.
        "Inc",
        "Ltd",
        "Jr",
        "Sr",
        "Co",
        "Corp",
        "Bros",
        "Esq",
        "al",
        # Institutions, streets and organizational units.
        "Dept",
        "Univ",
        "Assn",
        "Natl",
        "Intl",
        "Bldg",
        "Dist",
        "Mfg",
        "Mgr",
        "Ave",
        "Blvd",
        "Rd",
        "Hwy",
        "Ln",
        "Ct",
    }
)

# Words that reliably begin a new sentence after an ambiguous
# abbreviation. "I", "A" and "An" are excluded: they collide with
# initials ("E. I. du Pont") and with names. Weekdays and months are
# excluded ("5 p.m. Monday" is one phrase), and so are content nouns
# ("Acme Inc. Revenue" can be one noun phrase). Reviewed and rejected:
# "Today" (U.S.A. Today), "No" (ranked the U.S.A. No. 1), "And"
# (Smith Bros. And Co.), plus "So", "Still", "Soon", "Few", "Both"
# and "Most", all real surnames after an initial (W. So, A. T. Still,
# P. Soon-Shiong, W. Few, J. Both, M. Most). Among auxiliaries, "Will"
# (George F. Will), "Can" (Emre Can) and "Do" (the surname Do) are
# rejected for the same reason, and "May" because "5 p.m. May 5" is a
# date. Matched as a whole case-sensitive word, so "Theatre" is not
# "The".
_BASE_STARTERS: Final[frozenset[str]] = frozenset(
    {
        # Pronouns and possessives.
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
        # Demonstratives, articles, existential "There".
        "This",
        "That",
        "These",
        "Those",
        "The",
        "There",
        # Discourse connectives and adverbs.
        "But",
        "However",
        "Wherever",
        "Then",
        "Now",
        "Later",
        "Tomorrow",
        "Yesterday",
        "Eventually",
        "Meanwhile",
        "Afterward",
        "Finally",
        "Suddenly",
        "Instead",
        "Also",
        "Moreover",
        "Furthermore",
        "Nevertheless",
        "Therefore",
        "Thus",
        "Hence",
        "Indeed",
        "Perhaps",
        "Maybe",
        # Interrogatives.
        "When",
        "What",
        "Why",
        "How",
        "Who",
        "Where",
        "Which",
        # Subordinators and sentence-initial prepositions.
        "If",
        "After",
        "Before",
        "While",
        "Since",
        "Although",
        "Though",
        "Because",
        "Unless",
        "Until",
        "During",
        "In",
        "On",
        "At",
        "By",
        "For",
        "From",
        "With",
        # Quantifiers and indefinite pronouns.
        "Many",
        "Some",
        "Several",
        "All",
        "Each",
        "Neither",
        "Either",
        "Another",
        "Everyone",
        "Everybody",
        "Someone",
        "Somebody",
        "Anyone",
        "Nobody",
        "Everything",
        "Nothing",
        "None",
        # Polarity and coordination-initial.
        "Yes",
        "Not",
        "Even",
        "Or",
        # Auxiliaries and modals that open questions.
        "Did",
        "Does",
        "Is",
        "Are",
        "Was",
        "Were",
        "Am",
        "Has",
        "Have",
        "Had",
        "Could",
        "Would",
        "Should",
        "Shall",
        "Must",
    }
)
_STARTERS: Final[frozenset[str]] = _BASE_STARTERS | _TITLES


def _extend_closers(text: str, i: int) -> int:
    """Absorb closing quotes/brackets after a terminal mark.

    Glued closers are always absorbed. A run of spaces or tabs (never
    newlines) followed by an unambiguous closer is absorbed too, so
    "Hello. ”" keeps the detached quote inside its sentence. Straight
    quotes stay glued-only: they are ambiguous between open and close.
    A detached "’" followed by a word character is skipped: that is an
    elision apostrophe ("’Tis", "’90s"), not a closer.
    """
    while i < len(text) and text[i] in _CLOSERS:
        i += 1
    while True:
        j = i
        while j < len(text) and text[j] in _HSPACE:
            j += 1
        if j == len(text) or text[j] not in _DETACHED_CLOSERS:
            return i
        if text[j] == "’" and j + 1 < len(text) and text[j + 1].isalnum():
            return i
        i = j + 1
        while i < len(text) and text[i] in _CLOSERS:
            i += 1


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

    # R1: in a run of terminal punctuation ("?!", "...", ". . .") only
    # the last mark decides. Runs may be spaced (Chicago-style
    # ellipsis): spaces and tabs are looked through, newlines never.
    look = nxt
    while look < len(text) and text[look] in _HSPACE:
        look += 1
    if look < len(text) and text[look] in _TERMINALS:
        return False

    # R2: a dot preceded by another dot (directly or across spaces) is
    # the last dot of an ellipsis run; R1 already deferred the others.
    # The run ends a sentence only before a capitalized word (decided
    # below, after the closer and lowercase checks).
    ellipsis = False
    if text[i] == ".":
        back = i - 1
        while back >= 0 and text[back] in _HSPACE:
            back -= 1
        ellipsis = back >= 0 and text[back] == "."

    # R3: a mark glued to a following word character or slash never
    # splits. Covers decimals (3.14), versions (1.5.2), domains with
    # ANY TLD (example.dev), filenames, e-mails and URL innards
    # ("index.ssf?/story", "./configure"), with no TLD list needed.
    if nxt < len(text) and (text[nxt].isalnum() or text[nxt] == "/"):
        return False

    # R4: absorb closing quotes/brackets; another terminal right after
    # them means an enclosing sentence is still open: defer to it.
    j = _extend_closers(text, nxt)
    if j < len(text) and text[j] in _TERMINALS:
        return False

    # R4b: glued continuation punctuation means the sentence goes on
    # ("Mississauga, Ont.; Kingston", "apples, etc., and more",
    # '"Go home.", she said').
    if j < len(text) and text[j] in ",;:":
        return False

    # R5: peek at the next significant character.
    k = _peek_significant(text, j)
    if k == len(text):
        return True
    if text[k].islower():
        return False
    if ellipsis:
        # "[...]" and "(...)" are editorial omission marks inside a
        # sentence, never sentence ends.
        if nxt < len(text) and text[nxt] in (")", "]"):
            return False
        # A capitalized word after an ellipsis starts a new sentence,
        # except "I": it is always capitalized and carries no signal
        # ("the thing is . . . I didn't mean it" is one sentence).
        # Digits and punctuation join ("It costs... 42 dollars").
        word = _next_word(text, k)
        return word is not None and word != "I"
    if text[i] != ".":
        # "!" and "?" end a sentence only before a capitalized word or
        # a digit; symbol salad ("! =----") reads as decoration.
        return text[k].isupper() or text[k].isdigit()

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
            if token == lowered and lowered in _AMPM:
                # A title right after a clock time is usually the
                # subject of the same clause ("At 5 a.m. Mr. Smith
                # went to the bank"), so only base starters split
                # here; uppercase "P.M." takes the generic path.
                return _next_word(text, k) in _BASE_STARTERS
            if token == lowered:
                return False
            return _splits_before(text, k)
        return True

    # R11: name/company suffixes split only before a starter word.
    if token in _CONDITIONAL_ABBREVS:
        return _splits_before(text, k)

    # R12: an ordinary word before the dot is a sentence boundary.
    return True


def _scan_block(
    text: str, start: int, stop: int, spans: list[tuple[int, int]]
) -> None:
    """Append the sentence spans found in text[start:stop]."""
    for match in _CANDIDATE_RE.finditer(text, start, stop):
        i = match.start()
        if not _is_boundary(text, i):
            continue
        end = _extend_closers(text, i + 1)
        while start < end and text[start].isspace():
            start += 1
        spans.append((start, end))
        start = end
    # Trailing text without terminal punctuation is the last sentence.
    while start < stop and text[start].isspace():
        start += 1
    if start < stop:
        end = stop
        while text[end - 1].isspace():
            end -= 1
        spans.append((start, end))


def tokenize_spans(text: str) -> list[tuple[int, int]]:
    """
    Half-open [start, end) spans of the sentences in text.

    Spans are trimmed of surrounding whitespace, never overlap, and the
    gaps between them contain only whitespace: text[start:end] is each
    sentence verbatim. A blank line always ends a sentence, even
    without terminal punctuation.
    """
    spans: list[tuple[int, int]] = []
    block_start = 0
    for match in _PARAGRAPH_RE.finditer(text):
        _scan_block(text, block_start, match.start(), spans)
        block_start = match.end()
    _scan_block(text, block_start, len(text), spans)
    return spans


def tokenize(text: str) -> list[str]:
    """Split English text into sentences (literal substrings of text)."""
    return [text[a:b] for a, b in tokenize_spans(text)]
