from freesyntax.factory import RuleFactory
from freesyntax.grammar import Match, Optional, Rule, Token
from freesyntax.structs import AutoLeaf

factory = RuleFactory()


@factory.funcdef(
    Match["define"],
    Token["STAR"],
    Token["NAME"],
    Token["STAR"],
    Rule["parameters"],
    Token["RARROW"],
    Rule["suite"],
)
def fixer(node):
    node.children[0].value = "def "
    node.children[1].remove()
    node.children[2].remove()
    node.children[-3].prefix = str()
    node.children[-2].replace(AutoLeaf.COLON)


print(
    factory.transform(
        """
define *greet* (name: str) ->
    print(Hello, name)
"""
    )
)
