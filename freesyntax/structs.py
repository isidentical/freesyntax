from freesyntax.lib2to3.fixer_util import *
from freesyntax.lib2to3.pgen2 import grammar, token
from freesyntax.lib2to3.pytree import *


class _AutoMeta(type):
    def __getattr__(cls, value):
        return cls.auto(value)


class AutoLeaf(metaclass=_AutoMeta):
    @staticmethod
    def auto(token):
        if token in grammar.opvalue:
            value = grammar.opvalue[token]
            return Leaf(grammar.opmap[value], value)
        else:
            raise ValueError(f"Unknown token, {token}!")


class Tokens(metaclass=_AutoMeta):
    @staticmethod
    def auto(value):
        return getattr(token, value)


class Symbols(metaclass=_AutoMeta):
    @classmethod
    def auto(cls, value):
        if not hasattr(cls, "factory"):
            raise ValueError("Factory is not bound!")
        return cls.factory.rule_grammar.grammar.symbol2number[value]
