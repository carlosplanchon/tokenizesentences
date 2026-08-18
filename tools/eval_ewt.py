#!/usr/bin/env python3

"""
Sentence-boundary evaluation on the UD English-EWT test split.

The corpus (CC BY-SA 4.0, not vendored) is pinned to an exact upstream
commit and verified by SHA256, so the August 2026 numbers in the README
can be rebuilt later, not just approximated. Documents are rebuilt by
joining the treebank's gold sentences with a single space inside a
paragraph and a blank line between paragraphs. A boundary is the index
right after a sentence's last non-whitespace character; the final
boundary of each document is excluded (trivial for every system).
Micro-averaged precision, recall and F1 over all documents.

Flags:
    --corpus PATH   use a local copy (still SHA256-verified)
    --competitors   also run the pinned competitor segmenters
    --speed         throughput microbenchmark: 1 warm-up plus 7 timed
                    runs per system, median and min/max reported
    --errors [N]    dump tokenizesentences mistakes classified by
                    cause, N examples per class (default 3)

The competitors are pinned in the `benchmark` dependency group:

    uv sync --group benchmark
    uv run python tools/eval_ewt.py --competitors --speed
"""

import hashlib
import importlib
import importlib.metadata
import platform
import statistics
import sys
import time
import urllib.request
from collections.abc import Callable
from datetime import datetime
from datetime import timezone

from tokenizesentences import tokenize_spans
from tokenizesentences.tokenizesentences import _AMPM
from tokenizesentences.tokenizesentences import _CONDITIONAL_ABBREVS
from tokenizesentences.tokenizesentences import _NUM_ABBREVS
from tokenizesentences.tokenizesentences import _TITLES
from tokenizesentences.tokenizesentences import _TOKEN_BEFORE_RE
from tokenizesentences.tokenizesentences import _TOKEN_WINDOW

CORPUS_COMMIT = "4a4d77f599ea53cc405f85d0cec4b2f14f81d42b"
CORPUS_URL = (
    "https://raw.githubusercontent.com/UniversalDependencies/"
    f"UD_English-EWT/{CORPUS_COMMIT}/en_ewt-ud-test.conllu"
)
CORPUS_SHA256 = (
    "fa024f43dc5da3c5ac02563bc9bd0e974f46cbb1560823976a8f342a37dc494a"
)

COMPETITORS = ["nltk", "pysbd", "syntok", "blingfire", "spacy"]

SystemFn = Callable[[str], list[int]]


def load_conllu() -> str:
    if "--corpus" in sys.argv:
        path = sys.argv[sys.argv.index("--corpus") + 1]
        with open(path, "rb") as f:
            raw = f.read()
        source = path
    else:
        with urllib.request.urlopen(CORPUS_URL) as response:
            raw = response.read()
        source = CORPUS_URL
    digest = hashlib.sha256(raw).hexdigest()
    if digest != CORPUS_SHA256:
        raise SystemExit(
            f"El corpus de {source} no coincide con el benchmark "
            f"congelado:\n  esperado {CORPUS_SHA256}\n  obtenido "
            f"{digest}\nUse el en_ewt-ud-test.conllu del commit "
            f"{CORPUS_COMMIT} de UD_English-EWT."
        )
    return raw.decode("utf-8")


def print_provenance() -> None:
    stamp = datetime.now(timezone.utc).date().isoformat()
    print(f"Fecha: {stamp} (UTC)")
    print(f"Python {platform.python_version()} en {platform.platform()}")
    print(f"Maquina: {platform.machine()}")
    print(f"Corpus: UD_English-EWT test @ {CORPUS_COMMIT[:12]}")
    versions = []
    for package in COMPETITORS:
        try:
            versions.append(f"{package} {importlib.metadata.version(package)}")
        except importlib.metadata.PackageNotFoundError:
            versions.append(f"{package} (no instalado)")
    print("Competidores: " + ", ".join(versions))
    print()


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

    def run(text: str) -> list[int]:
        ends = []
        for paragraph in segmenter.analyze(text):
            for sentence in paragraph:
                if sentence:
                    last = sentence[-1]
                    ends.append(last.offset + len(last.value))
        return ends

    return run


def make_blingfire() -> SystemFn:
    blingfire = importlib.import_module("blingfire")

    def run(text: str) -> list[int]:
        raw = blingfire.text_to_sentences(text)
        sentences = [s for s in raw.split("\n") if s]
        return align_ends(text, sentences) or []

    return run


def make_spacy() -> SystemFn:
    spacy = importlib.import_module("spacy")
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    return lambda text: [span.end_char for span in nlp(text).sents]


def _skip_forward(text: str, i: int) -> int:
    """Next significant char: skips whitespace, openers and closers."""
    skippable = set("\"'“”‘’«»()[]")
    while i < len(text) and (text[i].isspace() or text[i] in skippable):
        i += 1
    return i


def _token_before(text: str, i: int) -> str | None:
    window = text[max(0, i - _TOKEN_WINDOW) : i]
    match = _TOKEN_BEFORE_RE.search(window)
    return match.group(1) if match else None


def classify_fn(text: str, end: int) -> str:
    """Why the engine did NOT split at this gold boundary."""
    i = end - 1
    if text[i] not in ".!?":
        return "sin-terminal"
    back = i - 1
    while back >= 0 and text[back] in " \t":
        back -= 1
    if back >= 0 and text[back] == ".":
        return "ellipsis"
    nxt = i + 1
    if nxt < len(text) and (text[nxt].isalnum() or text[nxt] == "/"):
        return "pegado"
    if nxt < len(text) and text[nxt] in ",;:":
        return "continuacion"
    k = _skip_forward(text, nxt)
    if k >= len(text):
        return "otro"
    if text[k].islower():
        return "minuscula"
    if text[k].isdigit():
        return "digito"
    word_end = k
    while word_end < len(text) and text[word_end].isalpha():
        word_end += 1
    if text[k:word_end] == "I":
        return "pronombre-I"
    token = _token_before(text, i)
    if token in _TITLES:
        return "titulo"
    if token is not None and (
        token in _CONDITIONAL_ABBREVS
        or token in _NUM_ABBREVS
        or token.lower() in _AMPM
        or "." in token
        or len(token) == 1
    ):
        return "abreviatura"
    return "otro"


def classify_fp(text: str, end: int) -> str:
    """Surface shape of a boundary the engine invented."""
    i = end - 1
    closers = set("\"'“”‘’«»)]")
    while i > 0 and text[i] in closers:
        i -= 1
    if text[i] in "!?":
        return "exclamacion-interrogacion"
    if text[i] == ".":
        back = i - 1
        while back >= 0 and text[back] in " \t":
            back -= 1
        if back >= 0 and text[back] == ".":
            return "ellipsis"
        return "punto"
    return "otro"


def context(text: str, end: int) -> str:
    ctx = text[max(0, end - 80) : end + 80].replace("\n", "|")
    return f"...{ctx}..."


def evaluate(
    name: str,
    fn: SystemFn,
    built: list[tuple[str, tuple[str, set[int]]]],
    collect_errors: bool,
) -> dict[str, list[tuple[str, str, int]]]:
    tp = fp = fn_count = 0
    errors: dict[str, list[tuple[str, str, int]]] = {"fp": [], "fn": []}
    for doc_id, (text, gold) in built:
        pred = norm_ends(text, fn(text))
        tp += len(pred & gold)
        fp += len(pred - gold)
        fn_count += len(gold - pred)
        if collect_errors:
            for end in sorted(pred - gold):
                errors["fp"].append((classify_fp(text, end), doc_id, end))
            for end in sorted(gold - pred):
                errors["fn"].append((classify_fn(text, end), doc_id, end))
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn_count) if tp + fn_count else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    print(
        f"{name:20s} P={prec:6.2%}  R={rec:6.2%}  F1={f1:6.2%}"
        f"  (tp={tp} fp={fp} fn={fn_count})"
    )
    return errors


def measure_speed(
    name: str, fn: SystemFn, texts: list[str], total_chars: int
) -> None:
    fn(texts[0])  # warm-up
    times = []
    for _ in range(7):
        started = time.perf_counter()
        for text in texts:
            fn(text)
        times.append(time.perf_counter() - started)
    med = statistics.median(times)
    print(
        f"{name:20s} mediana {total_chars / med / 1e6:6.2f} Mchar/s"
        f"  (min {total_chars / max(times) / 1e6:.2f},"
        f" max {total_chars / min(times) / 1e6:.2f},"
        f" {med:.3f}s por pasada)"
    )


def report_errors(
    kind: str,
    entries: list[tuple[str, str, int]],
    built: dict[str, tuple[str, set[int]]],
    per_class: int,
) -> None:
    by_class: dict[str, list[tuple[str, int]]] = {}
    for cls, doc_id, end in entries:
        by_class.setdefault(cls, []).append((doc_id, end))
    print(f"\n{kind} por clase:")
    ranked = sorted(by_class.items(), key=lambda kv: -len(kv[1]))
    for cls, items in ranked:
        print(f"  {cls:24s} {len(items)}")
    for cls, items in ranked:
        print(f"\n  [{cls}]")
        for doc_id, end in items[:per_class]:
            text, _ = built[doc_id]
            short = doc_id.rsplit("-", 1)[0].split("_")[-1][:24]
            print(f"    {short:24s} @{end}  {context(text, end)}")


def main() -> None:
    print_provenance()
    docs = load_docs(load_conllu())
    built = [(doc_id, build(paras)) for doc_id, paras in docs]
    built_map = dict(built)
    texts = [text for _, (text, _) in built]
    total_chars = sum(len(t) for t in texts)
    total_gold = sum(len(gold) for _, (_, gold) in built)
    print(
        f"Docs: {len(built)}, fronteras gold interiores: {total_gold}, "
        f"caracteres: {total_chars}\n"
    )

    want_errors = "--errors" in sys.argv
    per_class = 3
    if want_errors:
        idx = sys.argv.index("--errors")
        if idx + 1 < len(sys.argv) and sys.argv[idx + 1].isdigit():
            per_class = int(sys.argv[idx + 1])

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

    systems: list[tuple[str, SystemFn]] = []
    for name, factory in factories:
        try:
            systems.append((name, factory()))
        except ModuleNotFoundError as exc:
            print(f"{name:20s} omitido (falta {exc.name})")

    ours_errors: dict[str, list[tuple[str, str, int]]] = {}
    for name, fn in systems:
        errors = evaluate(
            name, fn, built, want_errors and name == "tokenizesentences"
        )
        if name == "tokenizesentences":
            ours_errors = errors

    if "--speed" in sys.argv:
        print("\nVelocidad (1 warm-up + 7 pasadas, mediana):")
        for name, fn in systems:
            measure_speed(name, fn, texts, total_chars)

    if want_errors and ours_errors:
        report_errors("FN", ours_errors["fn"], built_map, per_class)
        report_errors("FP", ours_errors["fp"], built_map, per_class)


if __name__ == "__main__":
    main()
