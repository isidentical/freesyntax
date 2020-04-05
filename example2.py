from freesyntax.factory import RuleFactory
from freesyntax.grammar import Match, Optional, Or, Rule, Token, Unit
from freesyntax.structs import (
    AutoLeaf,
    Call,
    Name,
    Node,
    String,
    Symbols,
    Tokens,
)

factory = RuleFactory()
factory.register_token("!", "MARK")


@factory.trailer(
    Or[
        Unit[Match["("], Optional[Rule["arglist"]], Match[")"],],
        Unit[Match["["], Rule["subscriptlist"], Match["]"],],
        Unit[Match["."], Token["NAME"],],
    ],
    Optional[Token["MARK"]],
)
def fix_trailer(trailer):
    if trailer.children[-1].type == Tokens.MARK:
        trailer.children[-1].remove()
        start = trailer.parent.children.index(trailer)
        children = trailer.parent.children[: start + 1]
        for child in children[1:]:
            child.remove()

        import_module = "".join(map(str, children))
        import_module = String(repr(import_module.strip()))
        children[0].replace(Call(Name("__import__"), [import_module]))


print(
    factory.transform(
        """
with open('file') as file:
    data = file.read()  # read a file!
    editor = gd.api!.Editor.from_string(data)
"""
    )
)
