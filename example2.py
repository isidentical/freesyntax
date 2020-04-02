from freesyntax.factory import RuleFactory
from freesyntax.grammar import Match, Optional, Or, Rule, Token, Unit
from freesyntax.structs import AutoLeaf

factory = RuleFactory()
factory.register_token("?", "QUESTIONMARK")
factory.register_token("?[", "QUESTIONLSBQ")
factory.register_token("?.", "QUESTIONATTR")


@factory.trailer(
    Or[
        Unit[Match["("], Optional[Rule["arglist"]], Match[")"],],
        Unit[Match["["], Rule["subscriptlist"], Match["]"],],
        Unit[Match["?["], Rule["subscriptlist"], Match["]"],],
        Unit[Match["."], Token["NAME"],],
        Unit[Match["?."], Token["NAME"],],
    ]
)
def fix_trailer(node):
    print(node)


factory.transform(
    """
a?.b
"""
)
