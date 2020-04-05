from pprint import pprint

from freesyntax.parser import parse_rule

src = "testlist_star_expr (annassign | augassign (yield_expr|testlist))"
print(parse_rule(src))
print(" ".join(map(str, parse_rule(src))))
