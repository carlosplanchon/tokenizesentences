#!/usr/bin/env python3

"""
The Golden Rules (English) from pragmatic_segmenter, pinned as an
external benchmark.

Test data reproduced from the README of
https://github.com/diasks2/pragmatic_segmenter under the MIT license
(Copyright (c) 2015 Kevin S. Dias).

Rules the engine passes run as regular tests. The rest are strict
xfails grouped by why they sit outside this library's contract: list
detection needs document structure, some expected outputs rewrite the
text, and one rule attaches a spaced ellipsis to the sentence that
follows it. If an engine change makes an xfail pass, strict mode
turns it into a visible failure so the moved limit gets reviewed.
"""

import pytest

from tokenizesentences import tokenize

GOLDEN_RULES = [
    pytest.param(
        "Hello World. My name is Jonas.",
        ["Hello World.", "My name is Jonas."],
        id="01-simple-period-to-end-sentence",
    ),
    pytest.param(
        "What is your name? My name is Jonas.",
        ["What is your name?", "My name is Jonas."],
        id="02-question-mark-to-end-sentence",
    ),
    pytest.param(
        "There it is! I found it.",
        ["There it is!", "I found it."],
        id="03-exclamation-point-to-end-sentence",
    ),
    pytest.param(
        "My name is Jonas E. Smith.",
        ["My name is Jonas E. Smith."],
        id="04-one-letter-upper-case-abbreviations",
    ),
    pytest.param(
        "Please turn to p. 55.",
        ["Please turn to p. 55."],
        id="05-one-letter-lower-case-abbreviations",
    ),
    pytest.param(
        "Were Jane and co. at the party?",
        ["Were Jane and co. at the party?"],
        id="06-two-letter-lower-case-abbreviations-in-the-middle-of-a-sentence",
    ),
    pytest.param(
        "They closed the deal with Pitt, Briggs & Co. at noon.",
        ["They closed the deal with Pitt, Briggs & Co. at noon."],
        id="07-two-letter-upper-case-abbreviations-in-the-middle-of-a-sentence",
    ),
    pytest.param(
        "Let's ask Jane and co. They should know.",
        ["Let's ask Jane and co.", "They should know."],
        id="08-two-letter-lower-case-abbreviations-at-the-end-of-a-sentence",
    ),
    pytest.param(
        "They closed the deal with Pitt, Briggs & Co. It closed yesterday.",
        [
            "They closed the deal with Pitt, Briggs & Co.",
            "It closed yesterday.",
        ],
        id="09-two-letter-upper-case-abbreviations-at-the-end-of-a-sentence",
    ),
    pytest.param(
        "I can see Mt. Fuji from here.",
        ["I can see Mt. Fuji from here."],
        id="10-two-letter-prepositive-abbreviations",
    ),
    pytest.param(
        "St. Michael's Church is on 5th st. near the light.",
        ["St. Michael's Church is on 5th st. near the light."],
        id="11-two-letter-prepositive-postpositive-abbreviations",
    ),
    pytest.param(
        "That is JFK Jr.'s book.",
        ["That is JFK Jr.'s book."],
        id="12-possesive-two-letter-abbreviations",
    ),
    pytest.param(
        "I visited the U.S.A. last year.",
        ["I visited the U.S.A. last year."],
        id="13-multi-period-abbreviations-in-the-middle-of-a-sentence",
    ),
    pytest.param(
        "I live in the E.U. How about you?",
        ["I live in the E.U.", "How about you?"],
        id="14-multi-period-abbreviations-at-the-end-of-a-sentence",
    ),
    pytest.param(
        "I live in the U.S. How about you?",
        ["I live in the U.S.", "How about you?"],
        id="15-u-s-as-sentence-boundary",
    ),
    pytest.param(
        "I work for the U.S. Government in Virginia.",
        ["I work for the U.S. Government in Virginia."],
        id="16-u-s-as-non-sentence-boundary-with-next-word-capitalized",
    ),
    pytest.param(
        "I have lived in the U.S. for 20 years.",
        ["I have lived in the U.S. for 20 years."],
        id="17-u-s-as-non-sentence-boundary",
    ),
    pytest.param(
        "At 5 a.m. Mr. Smith went to the bank. He left the bank at 6 P.M. Mr. Smith then went to the store.",
        [
            "At 5 a.m. Mr. Smith went to the bank.",
            "He left the bank at 6 P.M.",
            "Mr. Smith then went to the store.",
        ],
        id="18-a-m-p-m-as-non-sentence-boundary-and-sentence-boundary",
    ),
    pytest.param(
        "She has $100.00 in her bag.",
        ["She has $100.00 in her bag."],
        id="19-number-as-non-sentence-boundary",
    ),
    pytest.param(
        "She has $100.00. It is in her bag.",
        ["She has $100.00.", "It is in her bag."],
        id="20-number-as-sentence-boundary",
    ),
    pytest.param(
        "He teaches science (He previously worked for 5 years as an engineer.) at the local University.",
        [
            "He teaches science (He previously worked for 5 years as an engineer.) at the local University."
        ],
        id="21-parenthetical-inside-sentence",
    ),
    pytest.param(
        "Her email is Jane.Doe@example.com. I sent her an email.",
        ["Her email is Jane.Doe@example.com.", "I sent her an email."],
        id="22-email-addresses",
    ),
    pytest.param(
        "The site is: https://www.example.50.com/new-site/awesome_content.html. Please check it out.",
        [
            "The site is: https://www.example.50.com/new-site/awesome_content.html.",
            "Please check it out.",
        ],
        id="23-web-addresses",
    ),
    pytest.param(
        "She turned to him, 'This is great.' she said.",
        ["She turned to him, 'This is great.' she said."],
        id="24-single-quotations-inside-sentence",
    ),
    pytest.param(
        'She turned to him, "This is great." she said.',
        ['She turned to him, "This is great." she said.'],
        id="25-double-quotations-inside-sentence",
    ),
    pytest.param(
        'She turned to him, "This is great." She held the book out to show him.',
        [
            'She turned to him, "This is great."',
            "She held the book out to show him.",
        ],
        id="26-double-quotations-at-the-end-of-a-sentence",
    ),
    pytest.param(
        "Hello!! Long time no see.",
        ["Hello!!", "Long time no see."],
        id="27-double-punctuation-exclamation-point",
    ),
    pytest.param(
        "Hello?? Who is there?",
        ["Hello??", "Who is there?"],
        id="28-double-punctuation-question-mark",
    ),
    pytest.param(
        "Hello!? Is that you?",
        ["Hello!?", "Is that you?"],
        id="29-double-punctuation-exclamation-point-question-mark",
    ),
    pytest.param(
        "Hello?! Is that you?",
        ["Hello?!", "Is that you?"],
        id="30-double-punctuation-question-mark-exclamation-point",
    ),
    pytest.param(
        "1.) The first item 2.) The second item",
        ["1.) The first item", "2.) The second item"],
        id="31-list-period-followed-by-parens-and-no-period-to-end-item",
        marks=pytest.mark.xfail(
            reason="List detection needs document-level parallel structure; '1. The' is locally identical to a number ending a sentence.",
            strict=True,
        ),
    ),
    pytest.param(
        "1.) The first item. 2.) The second item.",
        ["1.) The first item.", "2.) The second item."],
        id="32-list-period-followed-by-parens-and-period-to-end-item",
        marks=pytest.mark.xfail(
            reason="List detection needs document-level parallel structure; '1. The' is locally identical to a number ending a sentence.",
            strict=True,
        ),
    ),
    pytest.param(
        "1) The first item 2) The second item",
        ["1) The first item", "2) The second item"],
        id="33-list-parens-and-no-period-to-end-item",
        marks=pytest.mark.xfail(
            reason="List detection needs document-level parallel structure; '1. The' is locally identical to a number ending a sentence.",
            strict=True,
        ),
    ),
    pytest.param(
        "1) The first item. 2) The second item.",
        ["1) The first item.", "2) The second item."],
        id="34-list-parens-and-period-to-end-item",
    ),
    pytest.param(
        "1. The first item 2. The second item",
        ["1. The first item", "2. The second item"],
        id="35-list-period-to-mark-list-and-no-period-to-end-item",
        marks=pytest.mark.xfail(
            reason="List detection needs document-level parallel structure; '1. The' is locally identical to a number ending a sentence.",
            strict=True,
        ),
    ),
    pytest.param(
        "1. The first item. 2. The second item.",
        ["1. The first item.", "2. The second item."],
        id="36-list-period-to-mark-list-and-period-to-end-item",
        marks=pytest.mark.xfail(
            reason="List detection needs document-level parallel structure; '1. The' is locally identical to a number ending a sentence.",
            strict=True,
        ),
    ),
    pytest.param(
        "• 9. The first item • 10. The second item",
        ["• 9. The first item", "• 10. The second item"],
        id="37-list-with-bullet",
        marks=pytest.mark.xfail(
            reason="List detection needs document-level parallel structure; '1. The' is locally identical to a number ending a sentence.",
            strict=True,
        ),
    ),
    pytest.param(
        "⁃9. The first item ⁃10. The second item",
        ["⁃9. The first item", "⁃10. The second item"],
        id="38-list-with-hypthen",
        marks=pytest.mark.xfail(
            reason="List detection needs document-level parallel structure; '1. The' is locally identical to a number ending a sentence.",
            strict=True,
        ),
    ),
    pytest.param(
        "a. The first item b. The second item c. The third list item",
        ["a. The first item", "b. The second item", "c. The third list item"],
        id="39-alphabetical-list",
        marks=pytest.mark.xfail(
            reason="List detection needs document-level parallel structure; '1. The' is locally identical to a number ending a sentence.",
            strict=True,
        ),
    ),
    pytest.param(
        "This is a sentence\ncut off in the middle because pdf.",
        ["This is a sentence\ncut off in the middle because pdf."],
        id="40-errant-newline-in-the-middle-of-a-sentence-pdf",
    ),
    pytest.param(
        "It was a cold \nnight in the city.",
        ["It was a cold night in the city."],
        id="41-errant-newline-in-the-middle-of-a-sentence",
        marks=pytest.mark.xfail(
            reason="The expected output rewrites the text (removes a newline); sentences are literal substrings of the input by contract.",
            strict=True,
        ),
    ),
    pytest.param(
        "features\ncontact manager\nevents, activities\n",
        ["features", "contact manager", "events, activities"],
        id="42-lower-case-list-separated-by-newline",
        marks=pytest.mark.xfail(
            reason="Single newlines never force a boundary by design.",
            strict=True,
        ),
    ),
    pytest.param(
        "You can find it at N°. 1026.253.553. That is where the treasure is.",
        [
            "You can find it at N°. 1026.253.553.",
            "That is where the treasure is.",
        ],
        id="43-geo-coordinates",
    ),
    pytest.param(
        "She works at Yahoo! in the accounting department.",
        ["She works at Yahoo! in the accounting department."],
        id="44-named-entities-with-an-exclamation-point",
    ),
    pytest.param(
        "We make a good team, you and I. Did you see Albert I. Jones yesterday?",
        [
            "We make a good team, you and I.",
            "Did you see Albert I. Jones yesterday?",
        ],
        id="45-i-as-a-sentence-boundary-and-i-as-an-abbreviation",
    ),
    pytest.param(
        "Thoreau argues that by simplifying one’s life, “the laws of the universe will appear less complex. . . .”",
        [
            "Thoreau argues that by simplifying one’s life, “the laws of the universe will appear less complex. . . .”"
        ],
        id="46-ellipsis-at-end-of-quotation",
    ),
    pytest.param(
        '"Bohr [...] used the analogy of parallel stairways [...]" (Smith 55).',
        [
            '"Bohr [...] used the analogy of parallel stairways [...]" (Smith 55).'
        ],
        id="47-ellipsis-with-square-brackets",
    ),
    pytest.param(
        "If words are left off at the end of a sentence, and that is all that is omitted, indicate the omission with ellipsis marks (preceded and followed by a space) and then indicate the end of the sentence with a period . . . . Next sentence.",
        [
            "If words are left off at the end of a sentence, and that is all that is omitted, indicate the omission with ellipsis marks (preceded and followed by a space) and then indicate the end of the sentence with a period . . . .",
            "Next sentence.",
        ],
        id="48-ellipsis-as-sentence-boundary-standard-ellipsis-rules",
    ),
    pytest.param(
        "I never meant that.... She left the store.",
        ["I never meant that....", "She left the store."],
        id="49-ellipsis-as-sentence-boundary-non-standard-ellipsis-rules",
    ),
    pytest.param(
        "I wasn’t really ... well, what I mean...see . . . what I'm saying, the thing is . . . I didn’t mean it.",
        [
            "I wasn’t really ... well, what I mean...see . . . what I'm saying, the thing is . . . I didn’t mean it."
        ],
        id="50-ellipsis-as-non-sentence-boundary",
    ),
    pytest.param(
        "One further habit which was somewhat weakened . . . was that of combining words into self-interpreting compounds. . . . The practice was not abandoned. . . .",
        [
            "One further habit which was somewhat weakened . . . was that of combining words into self-interpreting compounds.",
            ". . . The practice was not abandoned. . . .",
        ],
        id="51-4-dot-ellipsis",
        marks=pytest.mark.xfail(
            reason="An ellipsis run attaches to the sentence it ends; this rule expects the spaced run attached to the NEXT sentence as a leading omission mark.",
            strict=True,
        ),
    ),
]


@pytest.mark.parametrize(("text", "expected"), GOLDEN_RULES)
def test_golden_rules(text: str, expected: list[str]) -> None:
    """Each rule pins the engine against the external benchmark."""
    assert tokenize(text) == expected
