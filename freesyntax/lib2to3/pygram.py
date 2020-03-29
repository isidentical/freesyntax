# Copyright 2006 Google, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

"""Export the Python grammar and symbols."""

# Python imports
import os

from . import pytree
# Local imports
from .pgen2 import driver, token

# The grammar file
_GRAMMAR_FILE = os.path.join(os.path.dirname(__file__), "Grammar.txt")
_PATTERN_GRAMMAR_FILE = os.path.join(
    os.path.dirname(__file__), "PatternGrammar.txt"
)


class Symbols:
    def __init__(self, grammar):
        """Initializer.

        Creates an attribute for each grammar symbol (nonterminal),
        whose value is the symbol's type (an int >= 256).
        """
        for name, symbol in grammar.symbol2number.items():
            setattr(self, name, symbol)


python_grammar = driver.load_packaged_grammar("lib2to3", _GRAMMAR_FILE)
python_symbols = Symbols(python_grammar)

pattern_grammar = driver.load_packaged_grammar(
    "lib2to3", _PATTERN_GRAMMAR_FILE
)
pattern_symbols = Symbols(pattern_grammar)
