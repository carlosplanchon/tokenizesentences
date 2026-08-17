# tokenizesentences

![tokenizesentences banner](https://raw.githubusercontent.com/carlosplanchon/tokenizesentences/master/assets/banner.jpg)

*Tiny, dependency-free English sentence tokenizer.*

[![CI](https://github.com/carlosplanchon/tokenizesentences/actions/workflows/ci.yml/badge.svg)](https://github.com/carlosplanchon/tokenizesentences/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/tokenizesentences.svg)](https://pypi.org/project/tokenizesentences/)
[![Python versions](https://img.shields.io/pypi/pyversions/tokenizesentences.svg)](https://pypi.org/project/tokenizesentences/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/carlosplanchon/tokenizesentences)

## installation
```
uv add tokenizesentences
```
or
```
pip install tokenizesentences
```

## usage
```python
In [1]: from tokenizesentences import tokenize

In [2]: tokenize(
    "Mr. John Johnson Jr. was born in the U.S.A but earned his Ph.D. in Israel before joining Nike Inc. as an engineer. He also worked at craigslist.org as a business analyst."
    )

Out[2]:
[
    'Mr. John Johnson Jr. was born in the U.S.A but earned his Ph.D. in Israel before joining Nike Inc. as an engineer.',
    'He also worked at craigslist.org as a business analyst.'
]
```

Sentence offsets are available too. Every span is a half-open
`[start, end)` slice of the input, so `text[start:end]` is the sentence,
verbatim:
```python
In [3]: from tokenizesentences import tokenize_spans

In [4]: tokenize_spans("It works. Try it!")
Out[4]: [(0, 9), (10, 17)]
```

### legacy API
The 0.3 interface keeps working and delegates to `tokenize()`:
```python
from tokenizesentences import SplitIntoSentences

SplitIntoSentences().split_into_sentences("It works. Try it!")
```

## notes
Deterministic, rule-based and English-only: an index-based scanner
inspired by [the answer of D Greenberg in StackOverflow](https://stackoverflow.com/questions/4576077/python-split-text-on-sentences),
with no models and no dependencies.

Sentences are literal substrings of the input, by construction. The text
is never rewritten — punctuation stays where the author put it (also
inside quotes) and internal newlines are preserved.

The heuristics are conservative: when in doubt they join, so a missed
boundary is preferred over a spurious split. Known limits, pinned by the
test suite:

- A lowercase word after the mark never splits: `she yelled "Stop!" and
  ran away.` is one sentence, and so is informal text like `i came. i
  saw.`
- A dot glued to a word never splits — that is how any domain, filename
  or version number survives without a TLD list — so the typo
  `He left.Then she cried.` stays joined.
- `...` never ends a sentence.
- After ambiguous abbreviations (`p.m.`, `Inc.`, `U.S.A.`) a sentence
  break is only detected before common starter words: `at 5 p.m. He
  left` splits, `at 5 p.m. Monday` does not.
- Titles (`Mr.`, `Sen.`, `St.`) never end a sentence, so `Main St. He
  walked.` stays joined.

## development
```
uv sync --group dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run ty check
```

## license
This project is licensed under the MIT License.
