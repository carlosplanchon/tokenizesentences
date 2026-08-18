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
    # Institutional and street abbreviations are conditional too.
    (
        "The Sales Dept. Heads met today.",
        ["The Sales Dept. Heads met today."],
    ),
    (
        "The Sales Dept. They met today.",
        ["The Sales Dept.", "They met today."],
    ),
    ("Natl. Grid stock rose.", ["Natl. Grid stock rose."]),
    ("Fifth Ave. Traffic was heavy.", ["Fifth Ave. Traffic was heavy."]),
    (
        "He walked down Fifth Ave. Then he stopped.",
        ["He walked down Fifth Ave.", "Then he stopped."],
    ),
    (
        "Ohio State Univ. Its campus is huge.",
        ["Ohio State Univ.", "Its campus is huge."],
    ),
    ("Acme Mfg. Workers went home.", ["Acme Mfg. Workers went home."]),
    (
        "The office is on Elm Ln. Nobody was there.",
        ["The office is on Elm Ln.", "Nobody was there."],
    ),
]


@pytest.mark.parametrize(("text", "expected"), SUFFIX_CASES)
def test_suffixes(text: str, expected: list[str]) -> None:
    """Suffixes split only before a safe sentence-starter word."""
    assert tokenize(text) == expected


# --- Group 3b: expanded starter words ------------------------------------

EXPANDED_STARTER_CASES = [
    ("Acme Inc. Then it grew.", ["Acme Inc.", "Then it grew."]),
    ("Acme Inc. Later it folded.", ["Acme Inc.", "Later it folded."]),
    (
        "Foo Ltd. Meanwhile profits fell.",
        ["Foo Ltd.", "Meanwhile profits fell."],
    ),
    (
        "They met at 5 p.m. When he arrived, they left.",
        ["They met at 5 p.m.", "When he arrived, they left."],
    ),
    (
        "Apple Inc. What happened next surprised everyone.",
        ["Apple Inc.", "What happened next surprised everyone."],
    ),
    (
        "He toured the U.S.A. In 2020 he stopped.",
        ["He toured the U.S.A.", "In 2020 he stopped."],
    ),
    ("Smith et al. Nothing held up.", ["Smith et al.", "Nothing held up."]),
    (
        "It closed at 6 a.m. Afterward we slept.",
        ["It closed at 6 a.m.", "Afterward we slept."],
    ),
    (
        "He was plan B. Nevertheless it worked.",
        ["He was plan B.", "Nevertheless it worked."],
    ),
    ("Acme Corp. Everyone cheered.", ["Acme Corp.", "Everyone cheered."]),
    # Rejected words stay out: they are real surnames or fixed
    # collocations, so these must remain joined.
    (
        "He reads U.S.A. Today on the train.",
        ["He reads U.S.A. Today on the train."],
    ),
    (
        "They ranked the U.S.A. No. 1 in exports.",
        ["They ranked the U.S.A. No. 1 in exports."],
    ),
    (
        "The paper cited W. So and others.",
        ["The paper cited W. So and others."],
    ),
    (
        "He toured the U.S.A. Revenue rose anyway.",
        ["He toured the U.S.A. Revenue rose anyway."],
    ),
    # Auxiliaries open questions after conditional abbreviations.
    (
        "We make a good team, you and I. Did you see the game?",
        ["We make a good team, you and I.", "Did you see the game?"],
    ),
    ("Acme Inc. Is it profitable?", ["Acme Inc.", "Is it profitable?"]),
    (
        "They met at 5 p.m. Was that late?",
        ["They met at 5 p.m.", "Was that late?"],
    ),
    (
        "He lives in the U.S.A. Has he moved?",
        ["He lives in the U.S.A.", "Has he moved?"],
    ),
    ("Bob Sr. Should we call him?", ["Bob Sr.", "Should we call him?"]),
    # Rejected auxiliaries: real surnames or date words stay joined.
    (
        "A column by George F. Will appeared today.",
        ["A column by George F. Will appeared today."],
    ),
    (
        "A header by E. Can won the match.",
        ["A header by E. Can won the match."],
    ),
    (
        "Reports by H. Do appeared online.",
        ["Reports by H. Do appeared online."],
    ),
    (
        "The deadline is 5 p.m. May 5 at noon.",
        ["The deadline is 5 p.m. May 5 at noon."],
    ),
]


@pytest.mark.parametrize(("text", "expected"), EXPANDED_STARTER_CASES)
def test_expanded_starters(text: str, expected: list[str]) -> None:
    """Function words that cannot continue a noun phrase split after
    conditional abbreviations; rejected lookalikes stay joined."""
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
    # Month abbreviations bind to a following number.
    (
        "He was born Jan. 15, 1990 in Ohio.",
        ["He was born Jan. 15, 1990 in Ohio."],
    ),
    (
        "The deadline is Aug. 2026 at the latest.",
        ["The deadline is Aug. 2026 at the latest."],
    ),
    ("It happened on Oct. 7 that year.", ["It happened on Oct. 7 that year."]),
    ("Prices fell on Dec. 24 as usual.", ["Prices fell on Dec. 24 as usual."]),
    ("Sept. 11 changed everything.", ["Sept. 11 changed everything."]),
    # Before a capital the month still ends the sentence.
    (
        "It was cold in Jan. He stayed home.",
        ["It was cold in Jan.", "He stayed home."],
    ),
    # Documented cost: a person named Jan followed by a digit joins.
    (
        "I met Jan. 5 minutes later she left.",
        ["I met Jan. 5 minutes later she left."],
    ),
    # Degree-sign variants of "No.".
    ("Find it at N°. 1026 on the map.", ["Find it at N°. 1026 on the map."]),
    ("See Nº. 7 for details.", ["See Nº. 7 for details."]),
    (
        "The city (pop. 256,000) grew fast.",
        ["The city (pop. 256,000) grew fast."],
    ),
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
    # Marks glued to a slash are URL or path innards.
    (
        "See index.ssf?/lsustory for notes.",
        ["See index.ssf?/lsustory for notes."],
    ),
    ("Run ./configure before building.", ["Run ./configure before building."]),
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
    # "Many" is a quantifier starter: acronyms split before it.
    (
        "He visited the U.S.A. Many stayed home.",
        ["He visited the U.S.A.", "Many stayed home."],
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
        ["It happened at 5 a.m.", "Nobody saw it."],
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
    # A title after a clock time reads as the subject of the same
    # clause; uppercase "P.M." keeps the generic acronym behavior.
    (
        "At 5 a.m. Mr. Smith went to the bank.",
        ["At 5 a.m. Mr. Smith went to the bank."],
    ),
    (
        "He left at 6 P.M. Mr. Smith then went home.",
        ["He left at 6 P.M.", "Mr. Smith then went home."],
    ),
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


# --- Group 7b: glued continuation punctuation ----------------------------

CONTINUATION_CASES = [
    (
        "They came from Kingston, Ont.; Toronto; and Ottawa.",
        ["They came from Kingston, Ont.; Toronto; and Ottawa."],
    ),
    (
        "I bought apples, etc., and more fruit.",
        ["I bought apples, etc., and more fruit."],
    ),
    ('"Go home.", she said.', ['"Go home.", she said.']),
    ("He yelled Stop!, then ran.", ["He yelled Stop!, then ran."]),
]


@pytest.mark.parametrize(("text", "expected"), CONTINUATION_CASES)
def test_continuation_punctuation(text: str, expected: list[str]) -> None:
    """A comma, semicolon or colon glued after the mark (and its
    closers) means the sentence continues."""
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


# --- Group 8b: detached unambiguous closers ------------------------------

DETACHED_CLOSER_CASES = [
    # The motivating case: a spaced curly quote joins its sentence.
    (
        "He said “Hello. ” Then he left.",
        ["He said “Hello. ”", "Then he left."],
    ),
    # Same shape with a parenthesis.
    (
        "He waved (goodbye. ) Then he left.",
        ["He waved (goodbye. )", "Then he left."],
    ),
    # Lowercase continuation: absorbing the closer lets R5 see "and"
    # and repairs a spurious split.
    (
        "He mumbled (quietly. ) and left.",
        ["He mumbled (quietly. ) and left."],
    ),
    # R4 defer: another terminal follows the absorbed closers, so the
    # inner dot yields to the enclosing sentence.
    (
        "He whispered (“Wait. ”). Then he ran.",
        ["He whispered (“Wait. ”).", "Then he ran."],
    ),
    # An elision apostrophe after a space is an opener, not a closer.
    (
        "The ’80s ended. ’90s kids remember.",
        ["The ’80s ended.", "’90s kids remember."],
    ),
    # Newlines are never crossed: the quote stays with the next line.
    (
        "He said “Fine.\n” Then he left.",
        ["He said “Fine.", "” Then he left."],
    ),
]


@pytest.mark.parametrize(("text", "expected"), DETACHED_CLOSER_CASES)
def test_detached_closers(text: str, expected: list[str]) -> None:
    """Unambiguous closers separated from the mark by spaces or tabs
    are absorbed into the sentence; ambiguous straight quotes stay
    glued-only."""
    assert tokenize(text) == expected


# --- Group 9: ellipses and terminal clusters -----------------------------

ELLIPSIS_CASES = [
    ("He paused... then left.", ["He paused... then left."]),
    # An ellipsis before a capitalized word starts a new sentence.
    ("He paused... Then he spoke.", ["He paused...", "Then he spoke."]),
    (
        "I never meant that.... She left the store.",
        ["I never meant that....", "She left the store."],
    ),
    (
        "He wondered... What if it fails?",
        ["He wondered...", "What if it fails?"],
    ),
    (
        "What.. Happened next is unclear.",
        ["What..", "Happened next is unclear."],
    ),
    # "I" is always capitalized, so it carries no signal and joins.
    (
        "He trailed off... I never saw him again.",
        ["He trailed off... I never saw him again."],
    ),
    # Digits and glued words join too.
    ("It costs... 42 dollars.", ["It costs... 42 dollars."]),
    ("Wait...Maybe not.", ["Wait...Maybe not."]),
    ("He trailed off...", ["He trailed off..."]),
    ("Stop...! He ran.", ["Stop...!", "He ran."]),
    ("Really...?", ["Really...?"]),
    ("Wait?! She left.", ["Wait?!", "She left."]),
    ("Stop!!! He ran.", ["Stop!!!", "He ran."]),
    # Spaced (Chicago-style) ellipses behave like glued ones and never
    # shatter into dot fragments.
    ("He paused . . . then spoke.", ["He paused . . . then spoke."]),
    ("He paused . . . Then he spoke.", ["He paused . . .", "Then he spoke."]),
    (
        "The laws will appear less complex. . . .",
        ["The laws will appear less complex. . . ."],
    ),
    (
        "Indicate the end with a period . . . . Next sentence.",
        ["Indicate the end with a period . . . .", "Next sentence."],
    ),
    # Bracketed ellipses are editorial omission marks, never ends.
    (
        "He said [...] and left. Then he ran.",
        ["He said [...] and left.", "Then he ran."],
    ),
    # Documented cost: a sentence starting with a dotted name joins.
    ("I use C#. .NET is great.", ["I use C#. .NET is great."]),
]


@pytest.mark.parametrize(("text", "expected"), ELLIPSIS_CASES)
def test_ellipses(text: str, expected: list[str]) -> None:
    """Only the last mark of a punctuation run may decide a boundary;
    an ellipsis ends a sentence only before a capitalized word other
    than "I"."""
    assert tokenize(text) == expected


# --- Group 10: edge cases ------------------------------------------------

EDGE_CASES = [
    ("", []),
    ("   ", []),
    ("\n", []),
    ("\t \n ", []),
    (".", ["."]),
    (" . ", ["."]),
    # A stray spaced dot reads as an ellipsis run: it attaches left
    # and the capitalized word starts a new sentence.
    ("Hi. . Bye.", ["Hi. .", "Bye."]),
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
    # A blank line always ends a sentence, even without punctuation.
    ("Title\n\nBody text here.", ["Title", "Body text here."]),
    (
        "One para ends\n\nAnother starts. And ends.",
        ["One para ends", "Another starts.", "And ends."],
    ),
    ("He said hello.\n\nShe left.", ["He said hello.", "She left."]),
    (
        "A title\n \nwith a spaced blank line.",
        ["A title", "with a spaced blank line."],
    ),
    ("“Quote.”\n\nNext paragraph.", ["“Quote.”", "Next paragraph."]),
    # "!" and "?" split only before a capital or a digit; ASCII-art
    # banners read as decoration.
    (
        "Over 19 Servers! =----- More below.",
        ["Over 19 Servers! =----- More below."],
    ),
    ("It works! 20 people agree.", ["It works!", "20 people agree."]),
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
    "He said “Hello. ” Then he left.",
    "Indicate the end with a period . . . . Next sentence.",
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
            reason="A detached straight quote is ambiguous between "
            "opening and closing; only unambiguous closers are "
            "absorbed across spaces.",
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
