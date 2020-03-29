from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from freesyntax.lib2to3 import pygram, pytree
from freesyntax.lib2to3.pgen2 import token, tokenize
from freesyntax.lib2to3.pgen2.driver import Driver
from freesyntax.lib2to3.pgen2.pgen import generate_grammar

GRAMMAR = Path(__file__).parent / "lib2to3" / "Grammar.txt"


@dataclass
class RuleGrammar:
    raw_grammar: str
    rules: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        readline = io.StringIO(self.raw_grammar)
        tokens = tuple(tokenize.generate_tokens(readline.readline))

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

        for current_token in tokens:
            if current_token[0] in {token.COMMENT, token.NEWLINE}:
                continue
            if current_token[0] == token.NL:
                continue

            if len(buffer) > 1 and current_token[1] == ":":
                self.rules[name] = tokenize.untokenize(
                    reset_lines(buffer[:-1])
                )
                name = buffer[-1]
                buffer.clear()
                buffer.append(name)

            if len(buffer) == 1 and current_token[1] == ":":
                name = buffer.pop()[1]
            else:
                buffer.append(current_token)
        else:
            self.rules[name] = tokenize.untokenize(reset_lines(buffer[:-1]))

        self.regen_grammar()

    def _prepare_grammar(self):
        return (
            "\n".join(f"{name}:{rule}" for name, rule in self.rules.items())
            + "\n"
        )

    def regen_grammar(self):
        self.grammar = generate_grammar(self._prepare_grammar())
        self.symbols = pygram.Symbols(self.grammar)
        return self.grammar


@dataclass
class RuleProxy:
    rule: str
    factory: RuleFactory

    def __call__(self, *items):
        self.factory.notify(self.rule, " ".join(map(str, items)))

        def wrapper(func):
            self.factory.transformers[self.rule] = func
            return func

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

    def notify(self, rule_name, rule_string):
        self.transformers.pop(rule_name, None)
        # when changing the rule, ensure the transformers are obsolete
        self.rule_grammar.rules[rule_name] = rule_string
        self.pgen2_driver.grammar = self.rule_grammar.regen_grammar()

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
