import token

from freesyntax import grammar
from freesyntax.shortcuts import get_tokens, untokenize


class RuleParser:
    def __init__(self, source):
        self.tokens = list(get_tokens(source))
        self.state = self.tokens[0]

    def eat(self):
        self.state = self.tokens.pop(0)

    def parse_until(self, expected):
        buffer = []
        while self.state.exact_type not in {expected, token.ENDMARKER}:
            if result := self.parse():
                buffer.append(result)
            else:
                raise ValueError
        return buffer

    def parse(self):
        rule = []
        while self.state.exact_type != token.ENDMARKER:
            try:
                self.eat()
            except IndexError:
                break

            if self.state.exact_type == token.LBRACE:
                rule.append(grammar.Unit[self.parse_until(token.RBRACE)])

            if self.state.exact_type == token.LSQB:
                rule.append(grammar.Optional[self.parse_until(token.RSQB)])

            if self.state.exact_type == token.NAME:
                if self.state.string.isupper():
                    rule.append(grammar.Token[self.state.string])
                elif self.state.string.islower():
                    rule.append(grammar.Rule[self.state.string])
                else:
                    raise ValueError(
                        f"Unknown grammar item, '{self.state.string}'."
                    )

            if self.state.exact_type == token.STRING:
                rule.append(grammar.Match[self.state.string])

            if self.state.exact_type == token.STAR and len(rule) > 0:
                rule.append(grammar.ZeroOrMore[rule[-1]])

            if self.state.exact_type == token.PLUS and len(rule) > 1:
                rule.append(grammar.OneOrMore[rule[-1]])

            if self.state.exact_type == token.VBAR and len(rule) > 1:
                rule.append(grammar.Or[rule[-1], self.parse()])

        return tuple(rule)


def parse_rule(source):
    rule_parser = RuleParser(source)
    return rule_parser.parse()
