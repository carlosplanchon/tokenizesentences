#!/usr/bin/env python3

"""
Regression corpus for the tokenizesentences scanner.

Each parametrized group freezes one family of boundary rules. The
engine's global posture is conservative: when in doubt it joins, so a
missed boundary is always preferred over a spurious split. Cases marked
in comments as "documented cost" pin that tradeoff on purpose.
"""

import pytest

from tokenizesentences import tokenize
from tokenizesentences import tokenize_spans

# --- Group 1: the README example, verbatim -------------------------------

README_TEXT = (
    "Mr. John Johnson Jr. was born in the U.S.A but earned his Ph.D. in "
    "Israel before joining Nike Inc. as an engineer. He also worked at "
    "craigslist.org as a business analyst."
)
README_SENTENCES = [
    (
        "Mr. John Johnson Jr. was born in the U.S.A but earned his Ph.D. "
        "in Israel before joining Nike Inc. as an engineer."
    ),
    "He also worked at craigslist.org as a business analyst.",
]


def test_readme_example() -> None:
    """The historical README example is the library's contract."""
    assert tokenize(README_TEXT) == README_SENTENCES


# --- Group 2: titles never end a sentence --------------------------------

TITLE_CASES = [
    ("Mr. Vance arrived. He spoke.", ["Mr. Vance arrived.", "He spoke."]),
    ("Mrs. Vance arrived. He spoke.", ["Mrs. Vance arrived.", "He spoke."]),
    ("Ms. Vance arrived. He spoke.", ["Ms. Vance arrived.", "He spoke."]),
    ("Mx. Vance arrived. He spoke.", ["Mx. Vance arrived.", "He spoke."]),
    ("Dr. Vance arrived. He spoke.", ["Dr. Vance arrived.", "He spoke."]),
    ("Prof. Vance arrived. He spoke.", ["Prof. Vance arrived.", "He spoke."]),
    ("Rev. Vance arrived. He spoke.", ["Rev. Vance arrived.", "He spoke."]),
    ("Fr. Vance arrived. He spoke.", ["Fr. Vance arrived.", "He spoke."]),
    ("Hon. Vance arrived. He spoke.", ["Hon. Vance arrived.", "He spoke."]),
    ("Pres. Vance arrived. He spoke.", ["Pres. Vance arrived.", "He spoke."]),
    ("Sen. Vance arrived. He spoke.", ["Sen. Vance arrived.", "He spoke."]),
    ("Rep. Vance arrived. He spoke.", ["Rep. Vance arrived.", "He spoke."]),
    ("Gov. Vance arrived. He spoke.", ["Gov. Vance arrived.", "He spoke."]),
    ("Gen. Vance arrived. He spoke.", ["Gen. Vance arrived.", "He spoke."]),
    ("Adm. Vance arrived. He spoke.", ["Adm. Vance arrived.", "He spoke."]),
    ("Cmdr. Vance arrived. He spoke.", ["Cmdr. Vance arrived.", "He spoke."]),
    ("Col. Vance arrived. He spoke.", ["Col. Vance arrived.", "He spoke."]),
    ("Maj. Vance arrived. He spoke.", ["Maj. Vance arrived.", "He spoke."]),
    ("Capt. Vance arrived. He spoke.", ["Capt. Vance arrived.", "He spoke."]),
    ("Cpt. Vance arrived. He spoke.", ["Cpt. Vance arrived.", "He spoke."]),
    ("Lt. Vance arrived. He spoke.", ["Lt. Vance arrived.", "He spoke."]),
    ("Sgt. Vance arrived. He spoke.", ["Sgt. Vance arrived.", "He spoke."]),
    ("Cpl. Vance arrived. He spoke.", ["Cpl. Vance arrived.", "He spoke."]),
    ("Pvt. Vance arrived. He spoke.", ["Pvt. Vance arrived.", "He spoke."]),
    ("Brig. Vance arrived. He spoke.", ["Brig. Vance arrived.", "He spoke."]),
    ("Det. Vance arrived. He spoke.", ["Det. Vance arrived.", "He spoke."]),
    ("St. Vance arrived. He spoke.", ["St. Vance arrived.", "He spoke."]),
    (
        "Mt. Fuji is tall. He climbed it.",
        ["Mt. Fuji is tall.", "He climbed it."],
    ),
    ("Ft. Knox is guarded. He knows.", ["Ft. Knox is guarded.", "He knows."]),
    # The classic bug this rule fixes.
    ("Sen. Smith spoke. Then left.", ["Sen. Smith spoke.", "Then left."]),
    # Titles hold even before a capitalized non-name.
    ("Gen. Z loves it.", ["Gen. Z loves it."]),
    ("St. Louis is nice.", ["St. Louis is nice."]),
    # Documented cost: "St." is Saint AND Street, we always join.
    (
        "I live on Main St. He lives elsewhere.",
        ["I live on Main St. He lives elsewhere."],
    ),
    # Case-sensitivity: "col." the noun is not "Col." the rank.
    ("Sort by col. Then filter.", ["Sort by col.", "Then filter."]),
]


@pytest.mark.parametrize(("text", "expected"), TITLE_CASES)
def test_titles(text: str, expected: list[str]) -> None:
    """A dot after a title precedes a name; it never ends a sentence."""
    assert tokenize(text) == expected


# --- Group 3: name/company suffixes are conditional on starters ----------

SUFFIX_CASES = [
    (
        "He joined Nike Inc. as an engineer.",
        ["He joined Nike Inc. as an engineer."],
    ),
    ("Apple Inc. He praised it.", ["Apple Inc.", "He praised it."]),
    ("Foo Ltd. announced profits.", ["Foo Ltd. announced profits."]),
    ("Foo Ltd. They dissolved it.", ["Foo Ltd.", "They dissolved it."]),
    ("King Jr. marched on.", ["King Jr. marched on."]),
    (
        "Martin Luther King Jr. He marched.",
        ["Martin Luther King Jr.", "He marched."],
    ),
    ("Bob Sr. smiled at us.", ["Bob Sr. smiled at us."]),
    ("Bob Sr. The family gathered.", ["Bob Sr.", "The family gathered."]),
    ("Tiffany & Co. sells rings.", ["Tiffany & Co. sells rings."]),
    (
        "Tiffany & Co. They shopped there.",
        ["Tiffany & Co.", "They shopped there."],
    ),
    ("Acme Corp. This grew fast.", ["Acme Corp.", "This grew fast."]),
    (
        "Warner Bros. But nothing changed.",
        ["Warner Bros.", "But nothing changed."],
    ),
    ("John Smith Esq. He signed it.", ["John Smith Esq.", "He signed it."]),
    ("Smith et al. (2020) found it.", ["Smith et al. (2020) found it."]),
    ("Smith et al. The results held.", ["Smith et al.", "The results held."]),
    # Documented cost: "Board" is not a starter, the NP-continuation
    # heuristic keeps this joined ("Nike Inc. CEO said..." is one NP).
    ("Acme Inc. Board approved it.", ["Acme Inc. Board approved it."]),
]


@pytest.mark.parametrize(("text", "expected"), SUFFIX_CASES)
def test_suffixes(text: str, expected: list[str]) -> None:
    """Suffixes split only before a safe sentence-starter word."""
    assert tokenize(text) == expected


# --- Group 4: decimals, versions and numeric abbreviations ---------------

NUMBER_CASES = [
    ("It costs 3.14 dollars. Cheap!", ["It costs 3.14 dollars.", "Cheap!"]),
    ("Pi is 3.14. It is irrational.", ["Pi is 3.14.", "It is irrational."]),
    (
        "Upgrade to version 1.5.2 now. It is stable.",
        ["Upgrade to version 1.5.2 now.", "It is stable."],
    ),
    ("Version 1.5.2.", ["Version 1.5.2."]),
    ("It costs $5. 20 people paid.", ["It costs $5.", "20 people paid."]),
    ("He turned 5. Nobody clapped.", ["He turned 5.", "Nobody clapped."]),
    ("No. 5 was best.", ["No. 5 was best."]),
    ("It was No. 5. He knew.", ["It was No. 5.", "He knew."]),
    ("No. He refused.", ["No.", "He refused."]),
    ("Nos. 5-7 were sold.", ["Nos. 5-7 were sold."]),
    ("See Fig. 3 for details.", ["See Fig. 3 for details."]),
    ("Figs. 2-4 show it.", ["Figs. 2-4 show it."]),
    ("Eq. 2 holds. It is neat.", ["Eq. 2 holds.", "It is neat."]),
    ("Ch. 3 is long.", ["Ch. 3 is long."]),
    ("Sec. 5 applies here.", ["Sec. 5 applies here."]),
    ("Art. 12 was amended.", ["Art. 12 was amended."]),
    ("Vol. 2 is out.", ["Vol. 2 is out."]),
    ("See pp. 12-14 for proof.", ["See pp. 12-14 for proof."]),
    ("Founded ca. 1900 it grew.", ["Founded ca. 1900 it grew."]),
    ("It is approx. 5 km away.", ["It is approx. 5 km away."]),
    ("The shop, est. 1999, thrives.", ["The shop, est. 1999, thrives."]),
]


@pytest.mark.parametrize(("text", "expected"), NUMBER_CASES)
def test_numbers(text: str, expected: list[str]) -> None:
    """A dot glued between digits, or after a numeric abbreviation
    followed by a number, is not a boundary."""
    assert tokenize(text) == expected


# --- Group 5: domains, filenames, e-mails (no TLD list) ------------------

DOMAIN_CASES = [
    (
        "He worked at craigslist.org as an analyst.",
        ["He worked at craigslist.org as an analyst."],
    ),
    (
        "Visit example.dev. Then continue.",
        ["Visit example.dev.", "Then continue."],
    ),
    ("Visit acme.co. Then leave.", ["Visit acme.co.", "Then leave."]),
    (
        "See example.co.uk. Next stop is here.",
        ["See example.co.uk.", "Next stop is here."],
    ),
    ("Go to site.xyz and browse.", ["Go to site.xyz and browse."]),
    ("Open notes.txt now.", ["Open notes.txt now."]),
    ("The file user.name.json loaded.", ["The file user.name.json loaded."]),
    ("Email bob@site.com today.", ["Email bob@site.com today."]),
    ("Email a.b@c.net or call.", ["Email a.b@c.net or call."]),
]


@pytest.mark.parametrize(("text", "expected"), DOMAIN_CASES)
def test_domains(text: str, expected: list[str]) -> None:
    """Intra-token dots never split, so any TLD works without a list."""
    assert tokenize(text) == expected


# --- Group 6: dotted acronyms and single-letter initials -----------------

ACRONYM_CASES = [
    (
        "He went to the U.S.A. He liked it.",
        ["He went to the U.S.A.", "He liked it."],
    ),
    ("The U.S. is big.", ["The U.S. is big."]),
    # Documented cost: "Many" is not a starter, acronyms stay joined.
    (
        "He visited the U.S.A. Many stayed home.",
        ["He visited the U.S.A. Many stayed home."],
    ),
    ("She has a Ph.D. in physics.", ["She has a Ph.D. in physics."]),
    (
        "He earned his Ph.D. He was proud.",
        ["He earned his Ph.D.", "He was proud."],
    ),
    ("Washington D.C. is lovely.", ["Washington D.C. is lovely."]),
    (
        "He lives in Washington D.C. He works there.",
        ["He lives in Washington D.C.", "He works there."],
    ),
    (
        "He arrived at 5 p.m. He left at 6 a.m. the next day.",
        ["He arrived at 5 p.m.", "He left at 6 a.m. the next day."],
    ),
    (
        "It happened at 5 a.m. Nobody saw it.",
        ["It happened at 5 a.m. Nobody saw it."],
    ),
    # Rare all-lowercase dotted acronyms never split.
    (
        "Prices are f.o.b. He paid anyway.",
        ["Prices are f.o.b. He paid anyway."],
    ),
    ("I met J. K. Rowling.", ["I met J. K. Rowling."]),
    (
        "E. I. du Pont was founded long ago.",
        ["E. I. du Pont was founded long ago."],
    ),
    ("Harry S. Truman won.", ["Harry S. Truman won."]),
    (
        "He wrote the letter Q. He mailed it.",
        ["He wrote the letter Q.", "He mailed it."],
    ),
    ("I don't. Really.", ["I don't.", "Really."]),
]


@pytest.mark.parametrize(("text", "expected"), ACRONYM_CASES)
def test_acronyms_and_initials(text: str, expected: list[str]) -> None:
    """Pure acronyms and initials split only before a starter word;
    contractions are whole tokens, not initials."""
    assert tokenize(text) == expected


# --- Group 7: latinisms --------------------------------------------------

LATINISM_CASES = [
    (
        "Try databases, e.g. Postgres, first.",
        ["Try databases, e.g. Postgres, first."],
    ),
    ("Consider tools, e.g. The GIMP.", ["Consider tools, e.g. The GIMP."]),
    ("E.g. This one works.", ["E.g. This one works."]),
    ("It runs, i.e. The Thing works.", ["It runs, i.e. The Thing works."]),
    ("Roe vs. Wade was cited.", ["Roe vs. Wade was cited."]),
    ("See cf. Smith 2020 for details.", ["See cf. Smith 2020 for details."]),
    (
        "Three parts, viz. The head and more.",
        ["Three parts, viz. The head and more."],
    ),
    (
        "Apples, pears, etc. were sold out.",
        ["Apples, pears, etc. were sold out."],
    ),
    (
        "I bought apples, etc. The rest rotted.",
        ["I bought apples, etc.", "The rest rotted."],
    ),
    ("Bananas, etc. and more fruit.", ["Bananas, etc. and more fruit."]),
]


@pytest.mark.parametrize(("text", "expected"), LATINISM_CASES)
def test_latinisms(text: str, expected: list[str]) -> None:
    """Forward-pointing latinisms never end a sentence; "etc." does,
    but only before a capitalized word."""
    assert tokenize(text) == expected


# --- Group 8: quotes and closing punctuation -----------------------------

QUOTE_CASES = [
    ('He said "Hello." Then left.', ['He said "Hello."', "Then left."]),
    ('She yelled "Stop!" and ran away.', ['She yelled "Stop!" and ran away.']),
    ('"Are you ok?" She asked.', ['"Are you ok?"', "She asked."]),
    ('"Are you ok?" she asked.', ['"Are you ok?" she asked.']),
    ('She asked "Why?" He shrugged.', ['She asked "Why?"', "He shrugged."]),
    ('"What?!" He gasped.', ['"What?!"', "He gasped."]),
    ('He said ("Hi."). Then left.', ['He said ("Hi.").', "Then left."]),
    ("[Sic.] He wrote it down.", ["[Sic.]", "He wrote it down."]),
    (
        'He said "Go home." "Fine." She left.',
        ['He said "Go home."', '"Fine."', "She left."],
    ),
    (
        'He said "Stop! Now go." She did.',
        ['He said "Stop!', 'Now go."', "She did."],
    ),
]


@pytest.mark.parametrize(("text", "expected"), QUOTE_CASES)
def test_quotes(text: str, expected: list[str]) -> None:
    """Closing quotes are absorbed into the sentence and the text is
    never rearranged around them."""
    assert tokenize(text) == expected


# --- Group 9: ellipses and terminal clusters -----------------------------

ELLIPSIS_CASES = [
    ("He paused... then left.", ["He paused... then left."]),
    # Parity with 0.3: an ellipsis never splits, even before a capital.
    ("He paused... Then he spoke.", ["He paused... Then he spoke."]),
    ("He trailed off...", ["He trailed off..."]),
    ("Stop...! He ran.", ["Stop...!", "He ran."]),
    ("Really...?", ["Really...?"]),
    ("Wait?! She left.", ["Wait?!", "She left."]),
    ("Stop!!! He ran.", ["Stop!!!", "He ran."]),
    ("What.. Happened next is unclear.", ["What.. Happened next is unclear."]),
]


@pytest.mark.parametrize(("text", "expected"), ELLIPSIS_CASES)
def test_ellipses(text: str, expected: list[str]) -> None:
    """Only the last mark of a punctuation run may decide a boundary,
    and ellipsis dots never do."""
    assert tokenize(text) == expected


# --- Group 10: edge cases ------------------------------------------------

EDGE_CASES = [
    ("", []),
    ("   ", []),
    ("\n", []),
    ("\t \n ", []),
    (".", ["."]),
    (" . ", ["."]),
    ("Hi. . Bye.", ["Hi.", ".", "Bye."]),
    ("No trailing punctuation here", ["No trailing punctuation here"]),
    ("  Leading spaces. And more.", ["Leading spaces.", "And more."]),
    ("Trailing spaces here.   ", ["Trailing spaces here."]),
    (
        "One sentence.  Two spaces between.",
        ["One sentence.", "Two spaces between."],
    ),
    ("First line.\nSecond line.", ["First line.", "Second line."]),
    # Newlines inside a sentence are preserved, never rewritten.
    ("He said\nhello. Bye.", ["He said\nhello.", "Bye."]),
    # Parity with 0.3: a blank line alone does not force a boundary.
    ("Title\n\nBody text here.", ["Title\n\nBody text here."]),
]


@pytest.mark.parametrize(("text", "expected"), EDGE_CASES)
def test_edges(text: str, expected: list[str]) -> None:
    """Empty input, bare punctuation and whitespace-only gaps."""
    assert tokenize(text) == expected


# --- Group 11: sentinel collision (bug in <= 0.3) ------------------------

SENTINEL_CASES = [
    ("He wrote <stop> here.", ["He wrote <stop> here."]),
    ("The <prd> tag is literal.", ["The <prd> tag is literal."]),
    ("Use <stop>. Then use <prd>.", ["Use <stop>.", "Then use <prd>."]),
    (
        "Mix <prd> and <stop> freely. It is safe.",
        ["Mix <prd> and <stop> freely.", "It is safe."],
    ),
]


@pytest.mark.parametrize(("text", "expected"), SENTINEL_CASES)
def test_sentinel_collision(text: str, expected: list[str]) -> None:
    """The index-based scanner has no markers to collide with: the old
    <prd>/<stop> sentinels are ordinary text now."""
    assert tokenize(text) == expected


# --- Group 12: unicode quotes and apostrophes ----------------------------

UNICODE_CASES = [
    ("“Hello.” Next one.", ["“Hello.”", "Next one."]),
    ("‘Fine.’ He said.", ["‘Fine.’", "He said."]),
    ("She said “stop!” and ran.", ["She said “stop!” and ran."]),
    ("It’s fine. Really fine.", ["It’s fine.", "Really fine."]),
    ("The world’s end. Nobody came.", ["The world’s end.", "Nobody came."]),
    ("Don’t. Really.", ["Don’t.", "Really."]),
]


@pytest.mark.parametrize(("text", "expected"), UNICODE_CASES)
def test_unicode(text: str, expected: list[str]) -> None:
    """Curly quotes close sentences and curly apostrophes stay
    word-internal."""
    assert tokenize(text) == expected


# --- Group 13: properties guaranteed by construction ---------------------

PROPERTY_CORPUS = [
    README_TEXT,
    'He said "Hello." Then left.',
    'She yelled "Stop!" and ran away.',
    '"What?!" He gasped. "Fine." She left.',
    'He said ("Hi."). Then left.',
    "Upgrade to version 1.5.2 now. It is stable.",
    "It costs $5. 20 people paid. Pi is 3.14. It is irrational.",
    "Visit example.dev. Then continue. See example.co.uk. Next stop.",
    "Sen. Smith spoke. Then left. Gen. Z loves it.",
    "He arrived at 5 p.m. He left at 6 a.m. the next day.",
    "I met J. K. Rowling. E. I. du Pont was there.",
    "Smith et al. (2020) found it. Smith et al. The results held.",
    "I bought apples, etc. The rest rotted. Bananas, etc. and more.",
    "He paused... Then he spoke. Stop...! He ran.",
    "Use <stop>. Then use <prd>.",
    "“Hello.” Next one. Don’t. Really.",
    "He said\nhello. Bye.",
    "Title\n\nBody text here.",
    "  Leading spaces. And more.   ",
    "Hi. . Bye.",
    "No trailing punctuation here",
    "Really...?",
    "No. 5 was best. It was No. 5. He knew.",
    "Acme Corp. This grew fast. Warner Bros. But nothing changed.",
    "First line.\nSecond line.\nThird line without dot",
]


@pytest.mark.parametrize("text", PROPERTY_CORPUS)
def test_sentences_are_literal_substrings(text: str) -> None:
    """The scanner slices, never rewrites: every sentence must appear
    verbatim in the input."""
    for sentence in tokenize(text):
        assert sentence in text


@pytest.mark.parametrize("text", PROPERTY_CORPUS)
def test_spans_reconstruct_text(text: str) -> None:
    """Spans are increasing, non-overlapping, trimmed slices whose
    content is exactly what tokenize() returns."""
    spans = tokenize_spans(text)
    sentences = tokenize(text)
    assert [text[a:b] for a, b in spans] == sentences
    previous_end = 0
    for start, end in spans:
        assert 0 <= previous_end <= start < end <= len(text)
        assert not text[start].isspace()
        assert not text[end - 1].isspace()
        previous_end = end


@pytest.mark.parametrize("text", PROPERTY_CORPUS)
def test_gaps_are_whitespace_only(text: str) -> None:
    """Everything the tokenizer drops between sentences is whitespace:
    no character of content is ever lost."""
    spans = tokenize_spans(text)
    previous_end = 0
    for start, end in spans:
        assert text[previous_end:start].strip() == ""
        previous_end = end
    assert text[previous_end:].strip() == ""


# --- Group 14: known limits, pinned as strict xfails ---------------------

XFAIL_CASES = [
    pytest.param(
        "He left.Then she cried.",
        ["He left.", "Then she cried."],
        id="missing-space-typo",
        marks=pytest.mark.xfail(
            reason="A dot glued to a word never splits; the price of "
            "handling every TLD/decimal without a list.",
            strict=True,
        ),
    ),
    pytest.param(
        'He said "Hello. " Then he left.',
        ['He said "Hello. "', "Then he left."],
        id="detached-closing-quote",
        marks=pytest.mark.xfail(
            reason="Closers are absorbed only when glued to the "
            "terminal mark.",
            strict=True,
        ),
    ),
    pytest.param(
        "i came. i saw. i conquered.",
        ["i came.", "i saw.", "i conquered."],
        id="lowercase-informal-text",
        marks=pytest.mark.xfail(
            reason="A lowercase word after the mark always joins; this "
            "is what protects unknown abbreviations.",
            strict=True,
        ),
    ),
    pytest.param(
        "They met at 5 p.m. Monday was busy.",
        ["They met at 5 p.m.", "Monday was busy."],
        id="ampm-before-non-starter",
        marks=pytest.mark.xfail(
            reason="After a.m./p.m. only starter words split; weekday "
            'names are ambiguous ("5 p.m. Monday").',
            strict=True,
        ),
    ),
    pytest.param(
        "Acme Inc. Revenue grew.",
        ["Acme Inc.", "Revenue grew."],
        id="suffix-before-non-starter",
        marks=pytest.mark.xfail(
            reason="After a company suffix only starter words split; "
            '"Acme Inc. Revenue" can be one noun phrase.',
            strict=True,
        ),
    ),
]


@pytest.mark.parametrize(("text", "expected"), XFAIL_CASES)
def test_known_limits(text: str, expected: list[str]) -> None:
    """Boundaries we deliberately do not detect. If a rule change makes
    one of these pass, strict xfail turns it into a visible failure so
    the tradeoff gets re-reviewed."""
    assert tokenize(text) == expected
