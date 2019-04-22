# tokenizesentences
*Python3 module to tokenize english sentences.*
Based on the answer of D Greenberg in StackOverflow:
https://stackoverflow.com/questions/4576077/python-split-text-on-sentences

## Installation
### Install with pip
```
pip3 install -U tokenizesentences
```

## Usage
```
In [1]: import tokenizesentences

In [2]: m = tokenizesentences.SplitIntoSentences()

In [3]: m.split_into_sentences(
    "Mr. John Johnson Jr. was born in the U.S.A but earned his Ph.D. in Israel before joining Nike Inc. as an engineer. He also worked at craigslist.org as a business analyst."
    )

Out[3]: 
[
    'Mr. John Johnson Jr. was born in the U.S.A but earned his Ph.D. in Israel before joining Nike Inc. as an engineer.',
    'He also worked at craigslist.org as a business analyst.'
]
```
