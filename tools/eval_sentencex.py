#!/usr/bin/env python3

"""
Evaluation on the sentencex English suite, in sentencex's own metric.

The suite is tests/en.txt from https://github.com/wikimedia/sentencex
(MIT, Copyright (c) 2025 Santhosh Thottingal), pinned to an exact
commit and verified by SHA256. Parsing, list-case filtering and the
per-case multiset F1 replicate benchmarks/compare.py from that repo,
so the scores are comparable with theirs by construction. Note that
the 60-case table in their README predates the current suite: the
pinned file yields 234 scoreable cases.

Flags:
    --corpus PATH   use a local copy of en.txt (still SHA256-verified)
    --competitors   also run the pinned competitor segmenters
    --errors [N]    show the N worst-scoring cases for
                    tokenizesentences (default 5)

Competitors are pinned in the `benchmark` dependency group:

    uv sync --group benchmark
    uv run python tools/eval_sentencex.py --competitors
"""

import hashlib
import importlib
import importlib.metadata
import platform
import re
import sys
import time
import urllib.request
from collections import Counter
from collections.abc import Callable
from datetime import datetime
from datetime import timezone

from tokenizesentences import tokenize

SUITE_COMMIT = "312da7f610ae4d23a9914d30bbac366a9965e30e"
SUITE_URL = (
    "https://raw.githubusercontent.com/wikimedia/sentencex/"
    f"{SUITE_COMMIT}/tests/en.txt"
)
SUITE_SHA256 = (
    "bdf045f7408c68ad646ef857fd08fec4e2df31d43a9240304be26bcf612768f8"
)

COMPETITORS = ["nltk", "pysbd", "syntok", "blingfire", "spacy", "sentencex"]

SystemFn = Callable[[str], list[str]]


def load_suite() -> str:
    if "--corpus" in sys.argv:
        path = sys.argv[sys.argv.index("--corpus") + 1]
        with open(path, "rb") as f:
            raw = f.read()
        source = path
    else:
        with urllib.request.urlopen(SUITE_URL) as response:
            raw = response.read()
        source = SUITE_URL
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SUITE_SHA256:
        raise SystemExit(
            f"La suite de {source} no coincide con el benchmark "
            f"congelado:\n  esperado {SUITE_SHA256}\n  obtenido "
            f"{digest}\nUse el tests/en.txt del commit {SUITE_COMMIT} "
            f"de wikimedia/sentencex."
        )
    return raw.decode("utf-8")


def print_provenance() -> None:
    stamp = datetime.now(timezone.utc).date().isoformat()
    print(f"Fecha: {stamp} (UTC)")
    print(f"Python {platform.python_version()} en {platform.platform()}")
    print(f"Maquina: {platform.machine()}")
    print(f"Suite: sentencex tests/en.txt @ {SUITE_COMMIT[:12]}")
    versions = []
    for package in COMPETITORS:
        try:
            versions.append(f"{package} {importlib.metadata.version(package)}")
        except importlib.metadata.PackageNotFoundError:
            versions.append(f"{package} (no instalado)")
    print("Competidores: " + ", ".join(versions))
    print()


def _is_list_case(input_text: str) -> bool:
    """Replicates benchmarks/compare.py from wikimedia/sentencex."""
    list_patterns = [r"^\d+[\.\)]\)", r"^\d+\.", r"^[•⁃]", r"^[a-z]\."]
    for line in input_text.splitlines():
        line = line.strip()
        if line and any(re.match(p, line) for p in list_patterns):
            return True
    return False


def load_cases(text: str) -> list[tuple[str, list[str]]]:
    """Replicates load_grs from benchmarks/compare.py."""
    cases = []
    for block in text.split("===\n"):
        block = block.strip()
        if not block or block.startswith("#"):
            continue
        if "---\n" not in block:
            continue
        input_part, expected_part = block.split("---\n", 1)
        input_text = input_part.strip()
        expected = [
            s.strip() for s in expected_part.strip().splitlines() if s.strip()
        ]
        if not input_text or not expected:
            continue
        if _is_list_case(input_text):
            continue
        cases.append((input_text, expected))
    return cases


def f1_score(predicted: list[str], expected: list[str]) -> float:
    """Replicates f1_score from benchmarks/compare.py: multiset F1
    over whitespace-stripped whole sentences."""
    pred = [s.strip() for s in predicted if s.strip()]
    exp = [s.strip() for s in expected if s.strip()]
    if not pred and not exp:
        return 1.0
    if not pred or not exp:
        return 0.0
    common = sum((Counter(pred) & Counter(exp)).values())
    precision = common / len(pred)
    recall = common / len(exp)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def make_ours() -> SystemFn:
    return tokenize


def make_punkt() -> SystemFn:
    nltk = importlib.import_module("nltk")
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)
    punkt = importlib.import_module("nltk.tokenize.punkt")
    tok = punkt.PunktTokenizer("english")
    return tok.tokenize


def make_pysbd() -> SystemFn:
    pysbd = importlib.import_module("pysbd")
    seg = pysbd.Segmenter(language="en", clean=False)
    return seg.segment


def make_syntok() -> SystemFn:
    segmenter = importlib.import_module("syntok.segmenter")

    def run(text: str) -> list[str]:
        sentences = []
        for paragraph in segmenter.analyze(text):
            for sentence in paragraph:
                sentences.append(
                    "".join(tok.spacing + tok.value for tok in sentence)
                )
        return sentences

    return run


def make_blingfire() -> SystemFn:
    blingfire = importlib.import_module("blingfire")
    return lambda text: blingfire.text_to_sentences(text).split("\n")


def make_spacy() -> SystemFn:
    spacy = importlib.import_module("spacy")
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    return lambda text: [span.text for span in nlp(text).sents]


def make_sentencex() -> SystemFn:
    sentencex = importlib.import_module("sentencex")
    # The binding exposes segment dynamically; static attribute access
    # confuses the type checker when the package is installed.
    segment = getattr(sentencex, "segment")  # noqa: B009
    return lambda text: list(segment("en", text))


def main() -> None:
    print_provenance()
    cases = load_cases(load_suite())
    print(f"Casos GRS puntuables: {len(cases)}\n")

    factories: list[tuple[str, Callable[[], SystemFn]]] = [
        ("tokenizesentences", make_ours)
    ]
    if "--competitors" in sys.argv:
        factories += [
            ("sentencex", make_sentencex),
            ("nltk-punkt", make_punkt),
            ("pysbd", make_pysbd),
            ("syntok", make_syntok),
            ("blingfire", make_blingfire),
            ("spacy-sentencizer", make_spacy),
        ]

    want_errors = "--errors" in sys.argv
    worst_n = 5
    if want_errors:
        idx = sys.argv.index("--errors")
        if idx + 1 < len(sys.argv) and sys.argv[idx + 1].isdigit():
            worst_n = int(sys.argv[idx + 1])

    ours_scored: list[tuple[float, str, list[str], list[str]]] = []
    for name, factory in factories:
        try:
            fn = factory()
        except ModuleNotFoundError as exc:
            print(f"{name:20s} omitido (falta {exc.name})")
            continue
        scores = []
        started = time.perf_counter()
        for input_text, expected in cases:
            try:
                predicted = fn(input_text)
            # Replicates compare.py: a crashing segmenter scores 0 on
            # the case instead of aborting the whole run.
            except Exception:  # noqa: BLE001
                predicted = []
            score = f1_score(predicted, expected)
            scores.append(score)
            if name == "tokenizesentences":
                ours_scored.append(
                    (score, input_text, list(predicted), expected)
                )
        elapsed = time.perf_counter() - started
        mean = 100 * sum(scores) / len(scores)
        perfect = sum(1 for s in scores if s == 1.0)
        zero = sum(1 for s in scores if s == 0.0)
        print(
            f"{name:20s} mean F1 {mean:6.2f}  "
            f"(perfectos {perfect}/{len(scores)}, en cero {zero}, "
            f"{elapsed:.2f}s)"
        )

    if want_errors and ours_scored:
        print(f"\nPeores {worst_n} casos de tokenizesentences:")
        for score, input_text, predicted, expected in sorted(
            ours_scored, key=lambda item: item[0]
        )[:worst_n]:
            print(f"\n  F1={score:.2f}  input: {input_text!r}")
            print(f"    esperado: {expected!r}")
            print(f"    obtenido: {predicted!r}")


if __name__ == "__main__":
    main()
