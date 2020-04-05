from __future__ import annotations

import io
import re
import token
import tokenize
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from freesyntax.grammar import _GrammarRepresentative
from freesyntax.lib2to3 import pygram, pytree
from freesyntax.lib2to3.pgen2 import grammar as _grammar
from freesyntax.lib2to3.pgen2 import token as _token
from freesyntax.lib2to3.pgen2 import tokenize as _tokenize
from freesyntax.lib2to3.pgen2.driver import Driver
from freesyntax.lib2to3.pgen2.pgen import generate_grammar
from freesyntax.parser import parse_rule
from freesyntax.shortcuts import get_tokens
from freesyntax.structs import Symbols

GRAMMAR = Path(__file__).parent / "lib2to3" / "Grammar.txt"


@dataclass
class RuleGrammar:
    raw_grammar: str
    rules: Dict[str, str] = field(default_factory=dict)
    pyrules: Dict[str, _GrammarRepresentative] = field(default_factory=dict)

    def __post_init__(self):
        tokens = get_tokens(self.raw_grammar)

        buffer = []
        name = None

        def reset_lines(tokens):
            first_line = tokens[0][2][0] - 1
            first_col = tokens[0][2][1]
            new_tokens = []
            current_line = 1
            for current_token in tokens:
                token_type, value, start, end, line = current_token
                start = (start[0] - first_line, start[1] - first_col)
                end = (end[0] - first_line, end[1] - first_col)
                new_tokens.append((token_type, value, start, end, line))

            return new_tokens

        def add_rule():
            rule_text = tokenize.untokenize(reset_lines(buffer[:-1]))
            rule_text = rule_text.replace("\\", str())
            self.pyrules[name] = parse_rule(rule_text)
            self.rules[name] = rule_text.split()

        for current_token in tokens:
            if current_token[0] in {token.COMMENT, token.NEWLINE}:
                continue
            if current_token[0] == token.NL:
                continue

            if len(buffer) > 1 and current_token[1] == ":":
                add_rule()
                name = buffer[-1]
                buffer.clear()
                buffer.append(name)

            if len(buffer) == 1 and current_token[1] == ":":
                name = buffer.pop()[1]
            else:
                buffer.append(current_token)
        else:
            add_rule()

        self.regen_grammar()

    def _prepare_grammar(self):
        rule_texts = []
        for name, rule in self.rules.items():
            rule_text = " ".join(map(str, rule))
            rule_texts.append(f"{name}:{rule_text}")
        return "\n".join(rule_texts) + "\n"

    def regen_grammar(self):
        self.grammar = generate_grammar(self._prepare_grammar())
        self.symbols = pygram.Symbols(self.grammar)
        return self.grammar


@dataclass
class RuleProxy:
    rule: str
    factory: RuleFactory

    def __call__(self, *items):
        def wrapper(func):
            self.factory.transformers[self.rule] = func
            return func

        if len(items) == 1 and callable(items[0]):
            return wrapper(*items)
        else:
            self.factory.notify(self.rule, items)
            return wrapper


class RuleFactory:
    def __init__(self):
        self.transformers = {}
        self.rule_grammar = RuleGrammar(GRAMMAR.read_text())
        self.pgen2_driver = Driver(
            grammar=self.rule_grammar.grammar, convert=pytree.convert
        )

    def __getattr__(self, rule):
        if rule in self.rule_grammar.grammar.symbol2number:
            return RuleProxy(rule, self)
        raise AttributeError(rule)

    def notify(self, rule_name, rule_value):
        self.transformers.pop(rule_name, None)
        # when changing the rule, ensure the transformers are obsolete
        self.rule_grammar.rules[rule_name] = rule_value
        self.pgen2_driver.grammar = self.rule_grammar.regen_grammar()
        self.bind_syms()

    def bind_syms(self):
        Symbols.factory = self

    def transform(self, source):
        tree = self.pgen2_driver.parse_string(source)
        for node in tree.pre_order():
            if isinstance(node, pytree.Leaf):
                continue
            node_type = self.rule_grammar.grammar.number2symbol[node.type]
            if transformer := self.transformers.get(node_type):
                if new := transformer(node):
                    node.replace(new)
        return str(tree)

    def register_token(self, token, token_name):
        token_slot = self._next_free_token_slot()
        _token.tok_name[token_slot] = token_name
        setattr(_token, token_name, token_slot)
        _grammar.opmap[token] = token_slot
        _grammar.opvalue[token_name] = token
        _tokenize.EXACT_TOKEN_TYPES[token] = token_slot
        _tokenize.PseudoToken = _tokenize.Whitespace + _tokenize.group(
            re.escape(token),
            _tokenize.PseudoExtras,
            _tokenize.Number,
            _tokenize.Funny,
            _tokenize.ContStr,
            _tokenize.Name,
        )

    def _next_free_token_slot(self):
        return max(_token.tok_name.keys() ^ {256}) + 1
