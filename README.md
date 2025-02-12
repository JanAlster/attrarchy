# Attrarchy

## Introduction
The `infuse` decorator will install some additional methods to supplied class 
and convert class attributes to `Attr`s.
`Attr`s are descriptors that live on the enhanced class definition and store information
about the attribute (data type/class, name, position in the hierarchy). Any attribute
can have a leader whose value will be used if its own is not set. Any attribute can have a parent
whose value will be used (or rather the parent's leader's value if it is defined) if attribute
does not have a leader or its leader also does not have a value set. Any top level attributes 
have to have a default value set.

When instancing an enhanced class, the whole attribute hierarchy is copied, preserving the 
relationships between the nested attributes. 

The intention here is that attributes on class definition serve as default values, whereas
attributes on instances can override them if desired. Attrs have a value change signal.
Setting attribute values during initialization is handled. Validation might be added in the future. 

## Motivation
Yet another "dataclass" clone. Inspired in part by attrs (www.attrs.org), when I wanted
to figure out how does it work.

I wanted to see how far I can push this with Python, messing with descriptors and injecting 
external functionality into existing classes. The concept mostly works, but there are some
quirks, especially if mixed with class inheritance. Still work in progress.



## Simple Example
```
import attrarchy as aa
@aa.infuse
class Test:
    attr: float = 1.
    attr2: int = 2

test = Test(attr=5.)
print(test.attr())  # 5.
print(test.attr2())  # 2
```

Note that typecheck is likely to protest that `Test.attr` is defined as float and therefore is not callable.
However, `@aa.infuse` will replace `Test.attr` float by a descriptor with enhanced functionality. 
Allowing `test.attr = 2` assignment would replace the Attr descriptor and break attrarchy.


## Structure
Briefly, `Attr` represents one of two types: 1. leaf attr that represent a single value (can be int, str, dataclass, ...)
and 2. node attr which contain other attributes. The second type is the enhanced class.
What `infuse` does is to add methods and (hidden) attributes that turn
supplied class into a node attr. In addition, some class attributes are changed into leaf attrs.

Individual attributes can be linked to other attributes (of compatible type) and
use their values if their own is not defined. Nested attributes can also
ask their parent node attrs for a value. If a value cannot be found
for a given instance (or within its network), class hierarchy is queried.


## THE RULES
- hierarchy is set on class creation
- leaf with class root (i.e. the top most parent is a user class) has to have value or leader set
  (or their parent's leader's equivalent)
- Nodes do not have "real" value, they aggregate values of their leaves
- effective value of leaves is self.value, self.leader.value, self.parent.leader.self_equivalent.value (possibly 
   going for its leader, etc), self_class_equivalent.value
- leaders need to have the same structure/datatype as self
- leaders have the same hierarchy root as followers
- Attrs cannot have a value of type "type".

Rules are not enforced for the most part, but things are likely to break if not followed.


## Notes
- Classes derived from enhanced classes should be explicitly infused too. Otherwise,
they will share its ancestor class attrs.


