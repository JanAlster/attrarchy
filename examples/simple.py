"""
A really simple example of using Attrarchy
"""
import attrarchy as aa

@aa.infuse
class Test:
    attr: float = 1.
    attr2: int = 2

test = Test(attr=5.)
print(test.attr())  # 5.
print(test.attr2())  # 2