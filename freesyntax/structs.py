from freesyntax.lib2to3.pgen2 import grammar
from freesyntax.lib2to3.pytree import Leaf


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
