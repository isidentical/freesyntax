import token
from contextlib import contextmanager, suppress

from freesyntax import grammar
from freesyntax.shortcuts import get_tokens, untokenize

IGNORED = frozenset((token.NEWLINE, token.COMMENT, token.NL))
DEBUG = True


class Finish(Exception):
    pass


class ExpectationReached(Exception):
    pass


class RuleParser:
    def __init__(self, source):
        self.tokens = list(get_tokens(source))
        self.state = self.tokens.pop(0)
        self.result = []
        self.contexts = []

    def eat(self):
        if len(self.tokens) == 0:
            raise Finish
        if (
            len(self.contexts) > 0
            and self.state.exact_type == self.contexts[-1]
        ):
            raise ExpectationReached
        self.state = self.tokens.pop(0)
        if self.state.exact_type == token.ENDMARKER:
            raise Finish
        if (
            len(self.contexts) > 0
            and self.state.exact_type == self.contexts[-1]
        ):
            raise Finish
        return self.state

    @contextmanager
    def sub_context(self, expected):
        buffer = []
        _result = self.result
        self.result = buffer
        self.contexts.append(expected)
        try:
            yield buffer
        except ExpectationReached:
            pass
        finally:
            self.contexts.pop()
            self.result = _result.copy()

    def parse_until(self, expected):
        with self.sub_context(expected) as buffer:
            while self.eat().exact_type != expected:
                buffer.append(self.parse_single())

        return buffer

    def parse_single(self):
        rule = []

        def unwrap(items):
            for item in items:
                if isinstance(item, tuple):
                    yield from item
                else:
                    yield item

        if self.state.exact_type == token.LBRACE:
            return grammar.Unit[tuple(unwrap(self.parse_until(token.RBRACE)))]
        elif self.state.exact_type == token.LSQB:
            return grammar.Optional[
                tuple(unwrap(self.parse_until(token.RSQB)))
            ]
        elif self.state.exact_type == token.LPAR:
            return grammar.Unit[tuple(unwrap(self.parse_until(token.RPAR)))]
        elif self.state.exact_type == token.NAME:
            if self.state.string.isupper():
                return grammar.Token[self.state.string]
            elif self.state.string.islower():
                return grammar.Rule[self.state.string]
            else:
                raise ValueError(
                    f"Unknown grammar item, '{self.state.string}'."
                )
        elif self.state.exact_type == token.STRING:
            return grammar.Match[self.state.string[1:-1]]
        elif self.state.exact_type == token.STAR and len(self.result) > 0:
            return grammar.ZeroOrMore[self.result.pop()]
        elif self.state.exact_type == token.PLUS and len(self.result) > 0:
            return grammar.OneOrMore[self.result.pop()]
        elif self.state.exact_type == token.VBAR and len(self.result) > 0:
            left = grammar.FreeUnit(tuple(self.result))
            self.result.clear()
            self.eat()
            with suppress(Finish):
                self.parse()
            right = grammar.FreeUnit(tuple(self.result))
            self.result.clear()
            return grammar.Or[(left, right)]
        elif self.state.exact_type in IGNORED:
            self.eat()
            return self.parse_single()
        else:
            pass
            # Still WIP TO:DO

    def parse(self):
        with suppress(Finish):
            while self.state.exact_type != token.ENDMARKER:
                result = self.parse_single()
                self.result.append(result)
                self.eat()

        return tuple(self.result)


def parse_rule(source):
    rule_parser = RuleParser(source)
    return rule_parser.parse()
