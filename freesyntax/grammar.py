from dataclasses import dataclass
from typing import Tuple, Union

from freesyntax.lib2to3.pgen2 import token

GrammarItem = Union[str, Tuple[str, ...]]


@dataclass(unsafe_hash=True)
class _GrammarRepresentative:
    value: GrammarItem

    def __init_subclass__(cls, *, requires_sequence=False):
        cls.requires_sequence = requires_sequence

    def __post_init__(self):
        if self.requires_sequence and not isinstance(self.value, tuple):
            self.value = (self.value,)

        self._old_value = self.value
        self.initalize_representative()

    def __str__(self):
        return self._value

    def __class_getitem__(cls, value):
        return cls(value)


class Token(_GrammarRepresentative):
    def initalize_representative(self):
        if hasattr(token, self.value.upper()):
            self._value = self.value.upper()
        else:
            raise ValueError(f"Unknown token, {self.value}!")


class Rule(_GrammarRepresentative):
    def initalize_representative(self):
        self._value = self.value


class Optional(_GrammarRepresentative, requires_sequence=True):
    def initalize_representative(self):
        self._value = f"[{' '.join(map(str, self.value))}]"


class Match(_GrammarRepresentative):
    def initalize_representative(self):
        self._value = f"{self.value!r}"


class ZeroOrMore(_GrammarRepresentative):
    def initalize_representative(self):
        self._value = f"{self.value}*"


class OneOrMore(_GrammarRepresentative):
    def initalize_representative(self):
        self._value = f"{self.value}+"


class Unit(_GrammarRepresentative, requires_sequence=True):
    def initalize_representative(self):
        self._value = f"({' '.join(map(str, self.value))})"


class FreeUnit(_GrammarRepresentative, requires_sequence=True):
    def initalize_representative(self):
        self._value = " ".join(map(str, self.value))


class Or(_GrammarRepresentative, requires_sequence=True):
    def initalize_representative(self):
        self._value = f"{' | '.join(map(str, self.value))}"
