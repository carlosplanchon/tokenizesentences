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

## notes
Deterministic, rule-based and English-only: an index-based scanner
inspired by [the answer of D Greenberg in StackOverflow](https://stackoverflow.com/questions/4576077/python-split-text-on-sentences),
with no models and no dependencies.

Sentences are literal substrings of the input, by construction. The
text is never rewritten: punctuation stays where the author put it
(also inside quotes) and single newlines inside a sentence are
preserved. A blank line always ends a sentence.

The heuristics are conservative: when in doubt they join, so a missed
boundary is preferred over a spurious split. Known limits, pinned by the
test suite:

- A lowercase word after the mark never splits: `she yelled "Stop!" and
  ran away.` is one sentence, and so is informal text like `i came. i
  saw.`
- A dot glued to a word never splits (that is how any domain, filename
  or version number survives without a TLD list), so the typo
  `He left.Then she cried.` stays joined.
- `...` (glued or spaced `. . .`) ends a sentence only when a
  capitalized word follows. `I` does not count: it is always
  capitalized, so it carries no signal.
- After ambiguous abbreviations (`p.m.`, `Inc.`, `U.S.A.`) a sentence
  break is only detected before common starter words: `at 5 p.m. He
  left` splits, `at 5 p.m. Monday` does not.
- Titles (`Mr.`, `Sen.`, `St.`) never end a sentence, so `Main St. He
  walked.` stays joined.

## benchmarks
- 40 of the 51 English [Golden Rules](https://github.com/diasks2/pragmatic_segmenter#the-golden-rules)
  from pragmatic_segmenter pass verbatim; the other 11 are pinned in
  `tests/test_golden_rules.py` as strict xfails with documented
  reasons (list detection, text rewriting, ellipsis attachment).
- Boundary detection on the UD English-EWT test split: 2,077 gold
  sentences of raw web text in 316 reconstructed documents, scored on
  the 1,761 interior boundaries (the trivial final boundary of each
  document is excluded). All systems ran the same day (August 2026)
  on the same inputs with the same scoring; reproduce with
  `uv run python tools/eval_ewt.py --competitors --speed`:

  | system | precision | recall | F1 | throughput |
  |---|---|---|---|---|
  | pysbd | 95.67% | 84.10% | **89.51%** | 0.05 Mchar/s |
  | **tokenizesentences** | **99.50%** | 79.22% | 88.21% | **4.6 Mchar/s** |
  | syntok | 98.38% | 79.16% | 87.73% | 0.30 Mchar/s |
  | nltk-punkt | 97.38% | 69.56% | 81.15% | 1.91 Mchar/s |
  | spacy-sentencizer | 96.62% | 68.14% | 79.92% | 0.60 Mchar/s |
  | blingfire | 98.79% | 60.02% | 74.67% | 1.50 Mchar/s |

  Highest precision and throughput of the six on this evaluation;
  only pysbd scores a higher F1, trading 3.8 points of precision and
  two orders of magnitude of throughput for it. Recall is spent on
  informal lowercase web text on purpose. Timings are medians of 7
  passes after a warm-up; the blingfire and syntok figures include
  offset reconstruction overhead. The corpus commit, its SHA256 and
  the competitor versions are pinned, so the run is reconstructible:
  see `tools/eval_ewt.py` and the `benchmark` dependency group.

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
