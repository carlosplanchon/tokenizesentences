#!/usr/bin/env python3

"""
Regenerate tests/test_golden_rules.py from pragmatic_segmenter's README.

The Golden Rules (English) live in the README of
https://github.com/diasks2/pragmatic_segmenter (MIT license, Copyright
(c) 2015 Kevin S. Dias). This tool parses that section, runs the
current engine over every rule and emits the pinned benchmark file:
passing rules become regular tests, failing ones become strict xfails
whose reason comes from the CATEGORY map below.

Usage:
    uv run python tools/gen_golden_rules.py [path-to-readme.md]

Without an argument the README is downloaded from GitHub. Afterwards
run `uv run ruff format tests/test_golden_rules.py` and
`uv run pytest`. A KeyError from CATEGORY means a rule changed state
after an engine change: review it and update the map on purpose.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

from tokenizesentences import tokenize

README_URL = (
    "https://raw.githubusercontent.com/diasks2/pragmatic_segmenter/"
    "master/README.md"
)
OUT_PATH = (
    Path(__file__).resolve().parent.parent / "tests" / "test_golden_rules.py"
)

LISTS = (
    "List detection needs document-level parallel structure; "
    "'1. The' is locally identical to a number ending a sentence."
)
ELLIPSIS_ATTACH = (
    "An ellipsis run attaches to the sentence it ends; this rule "
    "expects the spaced run attached to the NEXT sentence as a "
    "leading omission mark."
)
CATEGORY = {
    31: LISTS,
    32: LISTS,
    33: LISTS,
    35: LISTS,
    36: LISTS,
    37: LISTS,
    38: LISTS,
    39: LISTS,
    41: (
        "The expected output rewrites the text (removes a newline); "
        "sentences are literal substrings of the input by contract."
    ),
    42: "Single newlines never force a boundary by design.",
    51: ELLIPSIS_ATTACH,
}

RULE_RE = re.compile(
    r"^(\d+)\.\)\s+\*\*(.+?)\*\*\s*\n```\n(.*?)\n```",
    re.MULTILINE | re.DOTALL,
)

HEADER = '''#!/usr/bin/env python3

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
'''

FOOTER = '''
]


@pytest.mark.parametrize(("text", "expected"), GOLDEN_RULES)
def test_golden_rules(text: str, expected: list[str]) -> None:
    """Each rule pins the engine against the external benchmark."""
    assert tokenize(text) == expected
'''


def load_readme() -> str:
    """Read the README from a path argument or download it."""
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).read_text(encoding="utf-8")
    with urllib.request.urlopen(README_URL) as response:
        return response.read().decode("utf-8")


def main() -> None:
    content = load_readme()
    start = content.index("#### Golden Rules (English)")
    rest = content[start:]
    end = rest.index("#### Golden Rules (", 10)
    section = rest[:end]

    params = []
    n_pass = n_fail = 0
    for match in RULE_RE.finditer(section):
        number = int(match.group(1))
        title = match.group(2)
        block = match.group(3)
        lines = block.split("\n")
        arrow = next(
            i for i, line in enumerate(lines) if line.startswith("=>")
        )
        text = "\n".join(lines[:arrow])
        # The README writes escapes literally inside the code blocks.
        text = text.replace('\\"', '"').replace("\\n", "\n")
        expected_raw = "\n".join(lines[arrow:])[2:].strip()
        try:
            expected = json.loads(expected_raw)
        except json.JSONDecodeError:
            # Rule 50 in the README is missing its closing bracket.
            expected = json.loads(expected_raw + "]")

        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        rule_id = f"{number:02d}-{slug}"
        if tokenize(text) == expected:
            if number in CATEGORY:
                raise SystemExit(
                    f"rule {number} passes but is still categorized; "
                    "remove it from CATEGORY"
                )
            n_pass += 1
            params.append(
                f"    pytest.param(\n"
                f"        {text!r},\n"
                f"        {expected!r},\n"
                f"        id={rule_id!r},\n"
                f"    ),"
            )
        else:
            reason = CATEGORY[number]
            n_fail += 1
            params.append(
                f"    pytest.param(\n"
                f"        {text!r},\n"
                f"        {expected!r},\n"
                f"        id={rule_id!r},\n"
                f"        marks=pytest.mark.xfail("
                f"reason={reason!r}, strict=True),\n"
                f"    ),"
            )

    OUT_PATH.write_text(HEADER + "\n".join(params) + FOOTER, encoding="utf-8")
    total = n_pass + n_fail
    print(f"{OUT_PATH}: {n_pass} pass, {n_fail} xfail, {total} rules")


if __name__ == "__main__":
    main()
