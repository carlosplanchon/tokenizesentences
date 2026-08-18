#!/usr/bin/env python3

"""
Sentence-boundary evaluation on the UD English-EWT test split.

Documents are reconstructed by joining the treebank's gold sentences
with a single space inside a paragraph and a blank line between
paragraphs. A boundary is the index right after a sentence's last
non-whitespace character; the final boundary of each document is
excluded (trivial for every system). Micro-averaged precision, recall
and F1 over all documents, plus wall-clock speed per system.

The corpus (CC BY-SA 4.0, not vendored) is downloaded on the fly, or
read from a local copy:

    uv run python tools/eval_ewt.py [--corpus en_ewt-ud-test.conllu]

Competitors are optional and skipped when not installed. To run them:

    uv run --with nltk --with pysbd --with syntok --with blingfire \\
        --with spacy python tools/eval_ewt.py --competitors
"""

import importlib
import sys
import time
import urllib.request
from collections.abc import Callable

from tokenizesentences import tokenize_spans

CORPUS_URL = (
    "https://raw.githubusercontent.com/UniversalDependencies/"
    "UD_English-EWT/master/en_ewt-ud-test.conllu"
)

SystemFn = Callable[[str], list[int]]


def load_conllu() -> str:
    if "--corpus" in sys.argv:
        path = sys.argv[sys.argv.index("--corpus") + 1]
        with open(path, encoding="utf-8") as f:
            return f.read()
    with urllib.request.urlopen(CORPUS_URL) as response:
        return response.read().decode("utf-8")


def load_docs(conllu: str) -> list[tuple[str, list[list[str]]]]:
    docs: list[tuple[str, list[list[str]]]] = []
    paragraphs: list[list[str]] = []
    doc_id = ""
    for line in conllu.splitlines():
        if line.startswith("# newdoc"):
            if paragraphs:
                docs.append((doc_id, paragraphs))
            doc_id = line.split("=", 1)[1].strip() if "=" in line else ""
            paragraphs = []
        elif line.startswith("# newpar"):
            paragraphs.append([])
        elif line.startswith("# text = "):
            if not paragraphs:
                paragraphs.append([])
            paragraphs[-1].append(line[len("# text = ") :].strip())
    if paragraphs:
        docs.append((doc_id, paragraphs))
    return docs


def build(paragraphs: list[list[str]]) -> tuple[str, set[int]]:
    parts: list[str] = []
    gold_ends: list[int] = []
    offset = 0
    for p_idx, para in enumerate(paragraphs):
        if p_idx > 0:
            parts.append("\n\n")
            offset += 2
        for s_idx, sent in enumerate(para):
            if s_idx > 0:
                parts.append(" ")
                offset += 1
            parts.append(sent)
            offset += len(sent)
            gold_ends.append(offset)
    return "".join(parts), set(gold_ends[:-1])


def norm_ends(text: str, ends: list[int]) -> set[int]:
    out = []
    for end in ends:
        while end > 0 and text[end - 1].isspace():
            end -= 1
        out.append(end)
    return set(out[:-1]) if out else set()


def align_ends(text: str, sentences: list[str]) -> list[int] | None:
    """Map whitespace-normalized sentences back to text offsets."""
    ends: list[int] = []
    i = 0
    for sent in sentences:
        last = -1
        for c in sent:
            if c.isspace():
                continue
            while i < len(text) and text[i].isspace():
                i += 1
            if i >= len(text) or text[i] != c:
                return None
            i += 1
            last = i
        if last > 0:
            ends.append(last)
    return ends


def make_ours() -> SystemFn:
    return lambda text: [end for _, end in tokenize_spans(text)]


def make_punkt() -> SystemFn:
    nltk = importlib.import_module("nltk")
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)
    punkt = importlib.import_module("nltk.tokenize.punkt")
    tok = punkt.PunktTokenizer("english")
    return lambda text: [end for _, end in tok.span_tokenize(text)]


def make_pysbd() -> SystemFn:
    pysbd = importlib.import_module("pysbd")
    seg = pysbd.Segmenter(language="en", clean=False, char_span=True)
    return lambda text: [span.end for span in seg.segment(text)]


def make_syntok() -> SystemFn:
    segmenter = importlib.import_module("syntok.segmenter")
    analyze = segmenter.analyze

    def run(text: str) -> list[int]:
        ends = []
        for paragraph in analyze(text):
            for sentence in paragraph:
                if sentence:
                    last = sentence[-1]
                    ends.append(last.offset + len(last.value))
        return ends

    return run


def make_blingfire() -> SystemFn:
    blingfire = importlib.import_module("blingfire")
    to_sentences = blingfire.text_to_sentences

    def run(text: str) -> list[int]:
        sentences = [s for s in to_sentences(text).split("\n") if s]
        return align_ends(text, sentences) or []

    return run


def make_spacy() -> SystemFn:
    spacy = importlib.import_module("spacy")
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    return lambda text: [span.end_char for span in nlp(text).sents]


def main() -> None:
    docs = load_docs(load_conllu())
    built = [(doc_id, build(paras)) for doc_id, paras in docs]
    total_chars = sum(len(text) for _, (text, _) in built)
    total_gold = sum(len(gold) for _, (_, gold) in built)
    print(
        f"Docs: {len(built)}, fronteras gold interiores: {total_gold}, "
        f"caracteres: {total_chars}\n"
    )

    factories: list[tuple[str, Callable[[], SystemFn]]] = [
        ("tokenizesentences", make_ours)
    ]
    if "--competitors" in sys.argv:
        factories += [
            ("nltk-punkt", make_punkt),
            ("pysbd", make_pysbd),
            ("syntok", make_syntok),
            ("blingfire", make_blingfire),
            ("spacy-sentencizer", make_spacy),
        ]

    for name, factory in factories:
        try:
            fn = factory()
        except ModuleNotFoundError as exc:
            print(f"{name:20s} omitido (falta {exc.name})")
            continue
        tp = fp = fn_count = 0
        started = time.perf_counter()
        predictions = [fn(text) for _, (text, _) in built]
        elapsed = time.perf_counter() - started
        for (_, (text, gold)), ends in zip(built, predictions):
            pred = norm_ends(text, ends)
            tp += len(pred & gold)
            fp += len(pred - gold)
            fn_count += len(gold - pred)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn_count) if tp + fn_count else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        speed = total_chars / elapsed / 1_000_000
        print(
            f"{name:20s} P={prec:6.2%}  R={rec:6.2%}  F1={f1:6.2%}"
            f"  {elapsed:7.2f}s  {speed:6.2f} Mchar/s"
        )


if __name__ == "__main__":
    main()
