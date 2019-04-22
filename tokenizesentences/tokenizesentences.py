#!/usr/bin/env python3

from re import sub

from typing import List


class SplitIntoSentences:
    """
    Split text into sentences:
        based on the answer of D Greenberg in StackOverflow.
    https://stackoverflow.com/questions/4576077/python-split-text-on-sentences
    """
    def __init__(self):
        self.alphabets = "([A-Za-z])"
        self.prefixes = "(Mr|St|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|Mt)[.]"
        self.suffixes = "(Inc|Ltd|Jr|Sr|Co)"
        self.starters = (
            r"(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s"
            r"|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
        )
        self.acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
        self.websites = "[.](com|net|org|io|gov|me|edu)"
        self.digits = "([0-9])"

    def split_into_sentences(self, text: str) -> List[str]:
        """
        Function that split a text into sentences.
        :param text: str: Text to split.

        """
        text = f" {text}  "
        text = text.replace("\n", " ")

        if "..." in text:
            text = text.replace("...", "<prd><prd><prd>")

        if "e.g." in text:
            text = text.replace("e.g.", "e<prd>g<prd>")

        if "i.e." in text:
            text = text.replace("i.e.", "i<prd>e<prd>")

        text = sub(
            f"{self.digits}[.]{self.digits}",
            "\\1<prd>\\2",
            text
            )

        text = sub(
            self.prefixes,
            "\\1<prd>",
            text
            )

        text = sub(
            self.websites,
            "<prd>\\1",
            text
            )

        if "Ph.D" in text:
            text = text.replace("Ph.D.", "Ph<prd>D<prd>")

        text = sub(
            rf"\s{self.alphabets}[.] ",
            " \\1<prd> ",
            text
            )

        text = sub(
            f"{self.acronyms} {self.starters}",
            "\\1<stop> \\2",
            text
            )

        text = sub(
            f"{self.alphabets}[.]{self.alphabets}[.]{self.alphabets}[.]",
            "\\1<prd>\\2<prd>\\3<prd>",
            text
            )

        text = sub(
            f"{self.alphabets}[.]{self.alphabets}[.]",
            "\\1<prd>\\2<prd>",
            text
            )

        text = sub(
            f" {self.suffixes}[.] {self.starters}",
            " \\1<stop> \\2",
            text
            )

        text = sub(
            f" {self.suffixes}[.]",
            " \\1<prd>",
            text
            )

        text = sub(
            f" {self.alphabets}[.]",
            " \\1<prd>",
            text
            )

        if "”" in text:
            text = text.replace(".”", "”.")

        if '"' in text:
            text = text.replace('."', '".')

        if "!" in text:
            text = text.replace('!"', '"!')

        if "?" in text:
            text = text.replace('?"', '"?')

        text = text.replace(".", ".<stop>")
        text = text.replace("?", "?<stop>")
        text = text.replace("!", "!<stop>")
        text = text.replace("<prd>", ".")

        sentences = text.split("<stop>")
        sentences = sentences[:-1]
        sentences = [s.strip() for s in sentences]

        return sentences
