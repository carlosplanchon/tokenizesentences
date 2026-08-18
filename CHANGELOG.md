# Changelog

## 0.5.0 (unreleased)

Complete rewrite of the historical library.

- New engine: an index-based scanner over the untouched input. Every
  sentence is a literal substring of the input, by construction, and
  the spans API exposes the offsets.
- New public API: `tokenize(text)` and `tokenize_spans(text)`. The
  `SplitIntoSentences` class is gone; migrate
  `SplitIntoSentences().split_into_sentences(text)` to
  `tokenize(text)`.
- Regression corpus (350+ cases, with the documented limits pinned as
  strict xfails), property-based fuzzing, and three pinned
  benchmarks: the pragmatic_segmenter English Golden Rules (40 of 52
  pass), a reproducible UD English-EWT evaluation, and the sentencex
  English suite scored in its own metric, all with frozen corpora
  and competitor versions (see `tools/`).
- Modern packaging: PEP 639 license metadata, `py.typed`, CI across
  Python 3.10 to 3.14, ruff and ty, PyPI trusted publishing.

## 0.3

Last release of the historical implementation: the substitution-based
algorithm adapted from D Greenberg's StackOverflow answer, with the
`SplitIntoSentences` class API.
