#
#  Attrarchy - Dataclass-like class attributes hierarchical system
#      Copyright (c) 2025. Jan Alster
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging

import pytest
import attrarchy as aa


### Tests for simple params (with verbatim value, like float, str, ...)

## create a basic param - class definition
# via automation with type and default value
def test_create_basic_with_type():
    """
    Define simple paramized class with a single Param specified by value and type.
    :return:
    """
    @aa.infuse
    class Test:
        param: float = 1.

# via automation without type and with default value
def test_create_basic_without_type():
    """
    Define simple paramized class with a single Param specified by value without type.
    :return:
    """
    @aa.infuse
    class Test:
        param = 1.


# via automation with type and without default value (error)
def test_create_basic_blank_with_type():
    """
    Fail to define Param without default value.
    :return:
    """
    with pytest.raises(ValueError):
        @aa.infuse
        class Test:
            param: float

# diractly as Param, with default value
def test_create_basic_param_with_type():
    """
    Define paramized class with a single Param, specified directly as Param with value of correct type.
    :return:
    """
    @aa.infuse
    class Test:
        param: float = aa.Attr(1.)


def test_create_basic_param_with_bad_type():
    """
    Define paramized class with a single Param, specified directly as Param with value of incorrect type.
    :return:
    """
    @aa.infuse
    class Test:
        param: float = aa.Attr("spam")

def test_create_basic_param_without_type():
    """
    Define paramized class with a single Param, specified directly as Param with value without type.
    :return:
    """
    @aa.infuse
    class Test:
        param = aa.Attr(1.)

# directly as Param, without default value
def test_create_basic_param_blank():
    """
    Fail to define paramized class with a single Param, specified directly as Param without default value.
    :return:
    """
    with pytest.raises(ValueError):
        @aa.infuse
        class Test:
            param = aa.Attr(float)

def test_create_basic_param_blank_with_leader():
    """
    Define paramized class with a single Param, specified directly as Param without default value, but with a leader.
    :return:
    """
    @aa.infuse
    class Test:
        param_leader = aa.Attr("spam")
        param = aa.Attr(str, leader=param_leader)

def test_create_basic_param_blank_with_bad_leader_type():
    """
    Param itself does not have a default value, but relies on leader to provide it.
    Fail if the leader's value is not of a compatible type.
    :return:
    """
    with pytest.raises(ValueError):
        @aa.infuse
        class Test:
            param_leader = aa.Attr(10.)
            param = aa.Attr(str, leader=param_leader)

# directly as Param, with leader set (with default value)
def test_create_basic_param_with_leader():
    """
    Define paramized class with a single Param, specified directly as Param with default value and with a leader.
    :return:
    """
    @aa.infuse
    class Test:
        param_parent = aa.Attr("spam")
        param = aa.Attr("egg", leader=param_parent)

# set leader outside of hierarcchy (error)
def test_create_basic_param_blank_with_bad_leader():
    """
    Fail to use Param's leader from a different hierarchy.

    Leaders defined on class hierarchy has to be from the same hierarchy
    (otherwise we cannot create the instance hierarchy properly).
    (You should be able to use leaders from different hierarchy on the instance level as that is not automated.)
    :return:
    """
    @aa.infuse
    class Test_leader:
        param = aa.Attr("egg")

    # with pytest.raises(ValueError):
    # it seems that __set_name__ will raise RuntimeError if we raise ValueError inside
    with pytest.raises(ValueError):
        @aa.infuse
        class Test:
            param = aa.Attr("spam", leader=Test_leader.param)



## create a basic param - instance
# (This is slightly innane, but instance creation has some quirks that should be tested)
def test_create_basic_with_type_instance():
    """
    Create an instance of a simple paramized class (single Param defined with type and value).
    :return:
    """
    @aa.infuse
    class Test:
        param: float = 1.

    test = Test()

# via automation without type and with default value
def test_create_basic_without_type_instance():
    """
    Create an instance of a simple paramized class (single Param defined with value).
    :return:
    """
    @aa.infuse
    class Test:
        param = 1.

    test = Test()

# diractly as Param, with default value
def test_create_basic_param_with_type_instance():
    """
    Create an instance of a simple paramized class (with type, directly using Param with value).
    :return:
    """
    @aa.infuse
    class Test:
        param: float = aa.Attr(1.)

    test = Test()

# TODO: not sure what should happen here
def test_create_basic_param_with_bad_type_instance():
    """
    Create an instance of a simple paramized class (directly using Param with value of wrong type).
    :return:
    """
    @aa.infuse
    class Test:
        param: float = aa.Attr("spam")
    test = Test()

def test_create_basic_param_without_type_instance():
    """
    Create an instance of a simple paramized class (without type, directly using Param with value).
    :return:
    """
    @aa.infuse
    class Test:
        param = aa.Attr(1.)
    test = Test()

# todo: test different basic types, we need some looping from pytest (pytest.parametrize?)

# directly as Param, with leader set (with default value)
def test_create_basic_param_blank_with_leader_instance():
    """
    Create an instance of a simple paramized class (with type, directly using Param with value and leader).
    :return:
    """
    @aa.infuse
    class Test:
        param_leader = aa.Attr("spam")
        param = aa.Attr("egg", leader=param_leader)
    test = Test()



## misc
def test_inheritance():
    """
    Setting class defaults for inherited classes.
    :return:
    """
    @aa.infuse
    class Base:
        param: float = 1.
        pass

    @aa.infuse
    class ChildA(Base):
        pass

    ChildA.param.set(2)
    assert ChildA.param() == 2

    @aa.infuse
    class ChildB(Base):
        pass

    ChildB.param.set(3)

    assert ChildA.param() == 2
    assert ChildB.param() == 3

# def test_stretch_height():
#     import tolp.margin_layout as ml
#     @aa.infuse
#     class EmptyPart(ml.MarginLayoutPart):
#         pass
#
#     EmptyPart.requirements.stretch_height.set(False)
#     assert EmptyPart.requirements.stretch_height() == False
#
#     @aa.infuse
#     class StretchyPart(ml.MarginLayoutPart):
#         pass
#     StretchyPart.requirements.stretch_height.set(True)
#
#     # OK, here is the problem, inherited classes will inherit also the class hierarchy param descriptor, so
#     #  instead of setting EmptyPart.requirements and StretchyPart.requirements independently, they are shared :(
#     # this is not a bug, this is a design flaw
#     #  we need to adjust the class hierarchy so that EmptyPart gets it own requirements (with MarginLayoutPart.requirements as parent or leader)
#     #    but not parent, since parent is the owner class (like Figure.title) and leader has to be on the same class hierarchy which MarginLayoutPart is not
#     #  this is in fact specific to class hierarchy, since instances do not have ancestor instances inside of them
#     #  but this is bad, because EmptyPart.requirements will not find the MarginLayoutPartRequirements instance on itself and will take the one
#     #    from MarginLayoutPart; which is fine for reading, but bad for writing and at the point of access, we do not know if we will be reading or writing
#     #    declaration of inherited class will not give an opportunity to adjust the descendant class
#     #  this might need a custom metaclass after all :(
#     print(ml.MarginLayoutPart.requirements)
#     print(EmptyPart.requirements)
#     print(StretchyPart.requirements)
#
#     empty_part = EmptyPart()
#     assert empty_part.requirements.stretch_height() == False

## TODO:
# signal emmision on value change when setting own value
# signal emmission on value change when unsetting own value
# the same but check not emmiting when own and effective value are the same
# dtto, using leader value for the effective value

# link instances outside of hierarchy (probably using signals, not leaders)
# get links value if linked

# serialization (for different basic types)


### Test for paramized params (i.e. group of params used as a param)

def test_detect_paramized_class_ok():
    """
    Check is_paramized().
    :return:
    """
    @aa.infuse
    class Test:
        pass

    assert aa.is_infused(Test)


def test_detect_paramized_class_bad():
    """
    Check not is_paramized().
    :return:
    """
    class Test:
        pass

    assert not aa.is_infused(Test)


# param creation

def test_create_paramized_blank():
    """
    Use paramized class as param.
    :return:
    """
    @aa.infuse
    class Test:
        param: str = "spam"

    @aa.infuse
    class User:
        test: Test

    # todo: possibly add more checks here (or more tests) - for default value, class value, etc.
    #  or rather for the public interface, the implementation details should not matter that much


def test_create_paramized():
    """
    Use paramized class as param; with value.
    :return:
    """
    @aa.infuse
    class Test:
        param: str = "spam"

    @aa.infuse
    class User:
        test: Test = Test(param="hello")

    # todo: possibly add more checks here (or more tests) - for default value, class value, etc.
    #  or rather for the public interface, the implementation details should not matter that much


# instance creation
def test_create_paramized_blank_instance():
    """
    Create instance of paramized class with paramized param.
    :return:
    """
    @aa.infuse
    class Test:
        param: str = "spam"

    @aa.infuse
    class User:
        test: Test

    user = User()

    assert isinstance(user.test, Test)


# todo: (try pytest.parametrize to test different values: int, str, float, [], custom arbitrary non-paramized class)
def test_param_value_set():
    """
    Set own param value on instance creation.
    :return:
    """
    @aa.infuse
    class Test:
        param: float = 1.

    test = Test(param=10.)
    assert test.param() == 10.
    # todo: we have a float comparison here, might not be a good idea, but should be the same value


# todo: (try pytest.parametrize to test different values: int, str, float, [], custom arbitrary non-paramized class)
def test_param_value_unset():
    """
    Instance uses class default value.
    :return:
    """
    @aa.infuse
    class Test:
        param: float = 1.

    test = Test()
    assert test.param() == 1.
    # todo: we have a float comparison here, might not be a good idea, but should be the same value


def test_nested_params():
    """
    Check that instance own value is set on instance not into class default.
    :return:
    """
    @aa.infuse
    class Test:
        param: str = "spam"

    @aa.infuse
    class User:
        test: Test = Test()

    user = User()
    user2 = User()


    """
    class Test:
        param = Param() 
        # this descriptor returns param._default ("spam") if called via class (Test.param)
        #  or instance._param_param (getattr(instance, param._instance_value_name)) for instance (Test().param)
            # this is not exact, it starts to look up the value there, but can look elsewhere
            # if the param is a basic one (i.e. its default value is not a paramized class)
            #  the next step is Test.param which has to be defined
            
    class User:
        test = Param()
        # again, this descriptor returns test._default (an empty Test instance) if called via class (User.test)
        #  lets call this instance "class hierarchy value"
        #  since it is a Test instance, it will search in Test class default if not defined 
        # it will return a different Test instance, belonging solely to the User() instance if called via it
        #    (i.e. User().test), lets call it "instance hierarchy value"
        #   however, even though it is a Test instance, it should NOT ask Test class default directly if undefined
        #  it should first ask the "class hierarchy value"
        # it is the same descriptor though and the values themselves have no idea if they are on the class or
        #  instance hierarchy
        # well the idea is the same, but we need to replace the root of the hierarchy
        # test.param -> Test.param
        # user.test -> User.test (and not Test)
        
        problem here is if it is nested
        user.test.param -> User.test.param and not Test.param
        but this is handled by the Test.param descriptor
        when resolving first we get user.test, which will return the "instance hierarchy Test() instance"
          then we ask its param using Test.param descriptor with "instance hierarchy Test() instance" as instance
          the Test.param descriptor does not know that this instance is part of the instance hierarchy
          when dealing with the unset "param" value, it will directly use the Test.param._default
          
          might be handled if we store the upper in the lookup chain directly
          but that will conflict with the leader system - we might end up with two leaders (one is instance 
          hierarchy leader and the other class hierarchy leader)
            the instance hierarchy leader should not use its class hierarchy leader value when asked for effective value
            if it is not set, we will ask the class hierarchy leader
            
            is there a problem with storing the class hierarchy leader reference? should not be, the class definition
            cannot be destroyed if there are its instances around..
            (well there is memory consumption, but we do not care at this point)
            
            class hierarchy leader cannot be set on instances used for class hiereachy values, but they can have 
            the instance hiereachy leader - so this naming is confusing
            instead we might call them "same level hiereachy leader" (which only gives us its own value if defined)
            and "upper level hierarchy leader" (which is guaranteed to get a valid value and will ask for the class
            default if its own value and optionally own value of its same level leader are unset)
            
            class default might be considered the "upper level hiereachy leader" for class hierarchy values
            (and class default will always have the value defined)
            however the class is not a instance, so the access is a bit different, so probably they cannot
            be handled in exactly the same way
        
    
    """

    # base class default
    assert user.test.param() == "spam"
    assert user2.test.param() == "spam"

    # hierarchy class  default
    aa.print_hierarchy(User)
    aa.print_hierarchy(user)
    User.test.param.set("eggs")  # actually this might be forbidden, we might need to use set_default
    # it breaks here: we need to check two things:
    # 1. that User.test.param is set to correct value
    assert User.test.param() == "eggs"  # this gives the correct answer, but it seems that Param object are messed up
    # possibly the user instance test Test instance has a copy of the original default value, which is "spam"
    #  and is not overriden by the new class hierarchy level "eggs"
    # that would mean that instance hierarchy shadows must not inherit the default values from the class hierarchy ones
    # but it does not look like it is inherited in paramize.init
    # 2. that User.test.param is used during user.test.param value search before Test.param
    # it seems that the problem is in the second possibility: user.test.param remains unset, User.test.param is set
    #  to eggs, but user.test.param lookup returns Test.param default spam.
    aa.print_hierarchy(User)
    aa.print_hierarchy(user)
    assert user.test.param() == "eggs"
    assert user2.test.param() == "eggs"

    # instance value
    user.test.param.set("jam")
    assert user.test.param() == "jam"
    assert user2.test.param() == "eggs"



    """here it goes too fast from instance value
    we test instance's descriptor instance for default value on the instance and its param
    we do not test instance's descriptor instance for default value
    and go straight to descriptor class default value
    or something like that

    we want print user hierarchy
    we print user User instance
    then go for it first param, which is described by Param 1 'test' of User class
       and stored in user._param_test (Test instance 0x7f8...7c0)
      next we want to print its params, starting with param
        it is unset on the (Test instance 0x7f8...7c0)._param_param
        so we look for an effective value initializing the lookup by getattr((Test instance 0x7f8...7c0), "param")
          this will trigger the descriptors (Param 0 'param' of Test) __get__() with (Test instance 0x7f8...7c0) instance
          that will try to get the instance value (which is Unset) and proceeds via _get_class_value()
          
          going for (Param 0 'param' of Test)._default value which is 'spam'
          
          but we wanted User.test param default value - i.e. not class/descriptor of (Test instance 0x7f8...7c0)
            but its class hierarchy equivalent: (Test instance 0x7f8...a60) of User and its _param_param value
            
        can we store the class hierarchy equivalent during instance hierarchy creation? 
    """

def test_inheritance_unparamized():
    """
    Inheriting from paramized class.
    (Note: this works, but Unparamized will use Paramized params)
    :return:
    """
    @aa.infuse
    class Paramized:
        spam: str = None

    class Unparamized(Paramized):
        def __init__(self):
            super().__init__()

    instance = Unparamized()


def test_inheritance_paramized_with_init():
    """
    Inheriting from paramized class; with __init__ defined.
    :return:
    """
    @aa.infuse
    class Paramized:
        spam: str = None


    @aa.infuse
    class Paramized2(Paramized):
        def __init__(self):
            super().__init__()

    instance = Paramized2()




def test_inheritance_paramized_simple():
    """
    Inheriting from paramized class
    :return:
    """
    @aa.infuse
    class Paramized:
        spam: str = None


    @aa.infuse
    class Paramized2(Paramized):
        ham: float = 0.

    instance = Paramized2()
    # this perhaps also does not work, since I do not see a spam duplicated on the instance !
    print(instance._attrarchy_attrs)
    print(instance.ham)
    print(instance.spam)
    # perhaps we need to go down the inheritance chain in duplication
    # or at least collect all inherited params


# non-param attributes for paramized classes
"""
Use case:
class LayoutPart:
    background_color: str = "black"  # param
    _layout: "Layout" = None   
    # _layout is not a param, it does not make sense to set it for the whole group
    #  but we might still want to input it here instead of writing __init__
    
    def _set_layout(self, layout):
         self._layout = layout
         
"""

def test_non_param_class_attribute():
    """
    Stop paramizing at specific point, leave other class attributes as is.
    :return:
    """
    @aa.infuse
    class Paramized:
        param_spam: str = "spam"
        command:int = aa.END_OF_ATTRS
        non_param_foo: float = None

    assert isinstance(Paramized.param_spam, aa.AttrLeaf)
    assert not isinstance(Paramized.non_param_foo, aa.AttrLeaf)


def test_setting_param_directly_forbidden():
    """
    Fail assigning param value directly for instance.
    :return:
    """
    @aa.infuse
    class Paramized:
        param_spam: str = "spam"

    # TODO: this fails and this is the one that cannot be caught
    # with pytest.raises(AttributeError):
    #     Paramized.param_spam = "test"

    instance = Paramized()
    with pytest.raises(AttributeError):
        instance.param_spam = "test"

# signaling
"""
We have several layers of value: own, leader, parent, class_default
- leaders and parents only use their instance_hierarchy values for their followers or children

We need to test that signals are triggered when values are changed
- when setting new value of the same layer
- when setting new value for layer above
- when unsetting value from layer above
But not
- when the new value is the same as the old one (even from a different layer)
- when setting class default, but we listen to leader or parent

"""

# how to check that function is called?
class MarkerError(UserWarning):
    pass

def mark(*args, **kw):
    logging.debug("mark: %s, %s", args, kw)
    raise MarkerError(f"mark: {args}, {kw}")

def loud_slot(*args, **kw):
    logging.debug("loud_slot: %s, %s", args, kw)
    pass

def test_signal_change_own_value():
    """
    changed signal emits on own value change
    :return:
    """
    @aa.infuse
    class Test:
        param = "spam"

    # Test.param is a ParamLeaf instance set with own value "spam"
    Test.param.changed.connect(mark)
    with pytest.raises(MarkerError):
        Test.param.set("jam")


def test_signal_keep_own_value():
    """
    changed signal does not emit on setting own value if effective value is not changed
    :return:
    """
    @aa.infuse
    class Test:
        param = "spam"

    # Test.param is a ParamLeaf instance set with own value "spam"
    Test.param.changed.connect(mark)
    Test.param.set("spam")


def test_signal_set_own_class():
    """
    several test for changed signal (does not) emit if various levels of value are set, but effective value is (not) changed
    :return:
    """
    @aa.infuse
    class Test:
        param = "spam"

    # Test.param is a ParamLeaf instance set with own value "spam"
    test = Test() # test instance does not have its own value set (it will use the class default)
    test.param.changed.connect(mark)

    # no own value, no leader, no parent leader, class value "spam"
    # set own value "jam" -> signal change
    with pytest.raises(MarkerError):
        test.param.set("jam")


    # own value "jam", no leader, no parent leader, class value "spam"
    # set own value "jam" -> do not signal when repeating the same value
    test.param.set("jam")

    # own value "jam", no leader, no parent leader, class value "spam"
    # unset own value - back to classe default "spam" -> signal change
    with pytest.raises(MarkerError):
        test.param.set(aa.Unset)

    # no own value, no leader, no parent leader, class value "spam"
    # set own value "spam" -> do not signal when repeating the same value, even from deffirent layer
    test.param.set("spam")

    # own value "spam", no leader, no parent leader, class value "spam"
    # change class value to "ham" -> do not signal if lower layer is changed
    Test.param.set("ham")

    # own value "spam", no leader, no parent leader, class value "ham"
    # unset own value - back to "ham" -> signal change
    with pytest.raises(MarkerError):
        test.param.set(aa.Unset)

    # no own value, no leader, no parent leader, class value "ham"
    # change class value to "spam" ->  signal change
    with pytest.raises(MarkerError):
        Test.param.set("spam")


def test_unset_default_value():
    """
    Fail to unset the class default value.
    :return:
    """
    @aa.infuse
    class Test:
        param = "spam"
    with pytest.raises(ValueError):
        Test.param.set(aa.Unset)  # this should be forbidden

def test_signal_set_own_leader():
    """
    Test changed signal emits if leader changes class default value.
    :return:
    """
    @aa.infuse
    class Test:
        param_leader = aa.Attr("spam")
        param_follower = aa.Attr(str, leader=param_leader)

    Test.param_follower.changed.connect(mark)
    Test.param_leader.changed.connect(loud_slot)


    # change leader value with own unset
    # FIXME: paramize fails to connect leader and follower at class hierarchy level
    with pytest.raises(MarkerError):
        Test.param_leader.set("ham")

    # repeat leader value with own unset
    Test.param_leader.set("ham")

    # set own value
    with pytest.raises(MarkerError):
        Test.param_follower.set("jam")

    # change leader with own set
    Test.param_leader.set("spam")

    Test.param_leader.set("jam")

    #unset value with same effective value
    Test.param_follower.set(aa.Unset)

    # set own value with same effective value
    Test.param_follower.set("jam")

    # change leader and unset own value
    Test.param_leader.set("spam")
    with pytest.raises(MarkerError):
        Test.param_follower.set(aa.Unset)



def test_signal_set_own_leader_instance():
    """
    Test changed signal emits if leader changes instance value.
    :return:
    """
    @aa.infuse
    class Test:
        param_leader = aa.Attr("spam")
        param_follower = aa.Attr(str, leader=param_leader)

    test = Test()
    test.param_follower.changed.connect(mark)

    # what if we change class default leader value?
    # actually what is the effective value now? - leader on instance hierarchy will be unset
    #   meaning the follower on instance hierarchy is unset
    #   so test.param_follower should ask Test.param_follower and the will ask its leader, Test.param_leader and that has own value

    # test if everything works as intended

    # change class default of leader
    with pytest.raises(MarkerError):
        Test.param_leader.set("jam")

    # change class default follower
    with pytest.raises(MarkerError):
        Test.param_follower.set("ham")

    # set instance leader - will override class follower default
    with pytest.raises(MarkerError):
        test.param_leader.set("jam")

    #setting class default should not signal
    Test.param_follower.set("spam")

    Test.param_leader.set("spam2")

    # set own value
    with pytest.raises(MarkerError):
        test.param_follower.set("spam")

    test.param_leader.set("ham2")


def test_signal_parent():
    """
    test signals with parent having or not having a leader; class default
    :return:
    """
    @aa.infuse
    class Inner:
        param: str = "spam"

    @aa.infuse
    class Top:
        param_leader = aa.Attr(Inner)
        param_follower = aa.Attr(Inner, leader=param_leader)

    # now Top.param_follower is a parent of Top.param_follower.param and has leader
    # if Top.param_follower.param is not set, it can ask its parent to supply a value from its leader
    # before asking class default Inner.param

    Top.param_follower.param.changed.connect(mark)

    # changing leader should signal
    with pytest.raises(MarkerError):
        Top.param_leader.param.set("ham")
        # Top.param_leader signals are not connected to Top.param_follower (perhaps that only happens on instance hierarchy for now?)
        # also check those TODO: or parent


def test_signal_parent_instance():
    """
    test signals with parent having or not leader; instance
    :return:
    """
    @aa.infuse
    class Inner:
        param: str = "spam"

    @aa.infuse
    class Top:
        param_leader = aa.Attr(Inner)
        param_follower = aa.Attr(Inner, leader=param_leader)

    # now Top.param_follower is a parent of Top.param_follower.param and has leader
    # if Top.param_follower.param is not set, it can ask its parent to supply a value from its leader
    # before asking class default Inner.param

    top = Top()
    top.param_follower.param.changed.connect(mark)

    # changing leader should signal
    with pytest.raises(MarkerError):
        top.param_leader.param.set("ham")


def test_signal_set_nested_node():
    """
    Test changed signal emit when changing value of nested paramized class.
    :return:
    """
    @aa.infuse
    class Inner:
        param = "spam"
        param2 = 10

    @aa.infuse
    class Outer:
        param_node: Inner

    Outer.param_node.changed.connect(mark)

    # Outer.param_node.param is not set actually, it does not have leader and its parent (Outer.param_node) does not
    #  have a leader either, so it has to ask its class default Inner.param
    # when that changes, we should see a signal change

    # changing class default
    with pytest.raises(MarkerError):
        Inner.param.set("ham")
    # or the other
    with pytest.raises(MarkerError):
        Inner.param2.set(11)

    # not whe setting own the same
    Outer.param_node.param.set("ham")

    # but signal if own is different
    with pytest.raises(MarkerError):
        Outer.param_node.param2.set(8)

    # ignore class default change if we have own
    Inner.param.set("spam")
    Inner.param2.set(8)

    #do not signal if unset own but efficient value is the same (8 -> 8)
    Outer.param_node.param2.set(aa.Unset)

    # do signal, if unset own, but efficient is different ("spam" -> "ham")
    with pytest.raises(MarkerError):
        Outer.param_node.param.set(aa.Unset)


def test_signal_ancestor_connect():
    """
    Derived class should have its own store for its own value, so that it does not override the ancestor's one,
    but it should honor the signal connections.
    (At least unless the param is redefined from scratch.)
    :return:
    """
    @aa.infuse
    class Ancestor:
        param = "spam"

    Ancestor.param.changed.connect(mark)

    @aa.infuse
    class Descendant(Ancestor):
        pass

    """
    fixme: problem here is that Descendant will create its own ParamLeaf as a copy of Ancestor.param (or rather 
    Ancestor._paramValue_param)
    But Signal() lives inside ParamLeaf instance and will be duplicated too, meaning that
    Descendant.param.changed is different from Ancestor.param.changed
    but we probably do not want that.
    
    We want the derived class to have its own default value, so that Descendant.param.set() will not 
    change Ancestor.param.value(), but keep the signals. 
    
    So either we need only one ParamLeaf and store the own value based on class.
    Or keep the signal separate.
    Or copy all connections from ancestor upon derived class creation.
    or call acenstors equivalent signal!
    
    However, if do something like
    Descendant.param.changed.connect(...)
    should it include Ancestor.param changes too? Probably not. I have to think about a use case.
    It makes sense that derived class is specific in making a new connection... That leaves copying the connections from
    the ancestor too - that will be a pain. If at all possible, it could be connected to arbitrary places.
    
    If we only allow connection on instances, this should not be a problem, right? Anything inside Ancestor's __init__
    on Descendant instance should use Descendant.param.changed, right? Yes, see the next test.
    """

    with pytest.raises(MarkerError):
        Descendant.param.set("ham")


def test_signal_ancestor_connect_instance():
    """
    Derived class should have its own store for its own value, so that it does not override the ancestor's one,
    but it should honor the signal connections.
    (At least unless the param is redefined from scratch.)
    :return:
    """

    @aa.infuse
    class Ancestor:
        param = "spam"

        def __init__(self):
            self.param.changed.connect(mark)

    @aa.infuse
    class Descendant(Ancestor):
        pass

    with pytest.raises(MarkerError):
        Descendant().param.set("ham")


def test_signal_ancestor_connect_redefined():
    """
    Derived class should have its own store for its own value, so that it does not override the ancestor's one,
    but it should honor the signal connections.
    (At least unless the param is redefined from scratch.)
    :return:
    """
    @aa.infuse
    class Ancestor:
        param = "spam"

    Ancestor.param.changed.connect(mark)

    @aa.infuse
    class Descendant(Ancestor):
        param = "ham"
        pass

    # This should not trigger the signal, since param is redefined from scratch in Descendant.
    # TODO: This is a gray zone and I am not so sure about this decision.
    #  perhaps this syntax should be interpreted simply as setting the own value
    Descendant.param.set("jam")

    raise

def test_signal_ancestor_connect_redefined_instance():
    """
    Derived class should have its own store for its own value, so that it does not override the ancestor's one,
    but it should honor the signal connections.
    (At least unless the param is redefined from scratch.)
    :return:
    """
    @aa.infuse
    class Ancestor:
        param = "spam"

        def __init__(self):
            self.param.changed.connect(mark)


    @aa.infuse
    class Descendant(Ancestor):
        param = "ham"
        pass

    # This should not trigger the signal, since param is redefined from scratch in Descendant.
    # TODO: This is a gray zone and I am not so sure about this decision.
    #  perhaps this syntax should be interpreted simply as setting the own value
    Descendant().param.set("jam")

    raise


def test_signal_set_nested_leaf():
    @aa.infuse
    class Inner:
        param = "spam"

    @aa.infuse
    class Outer:
        param_node: Inner

    Outer.param_node.param.changed.connect(mark)

    # Outer.param_node.param is not set actually, it does not have leader and its parent (Outer.param_node) does not
    #  have a leader either, so it has to ask its class default Inner.param
    # when that changes, we should see a signal change

    # do change when class default changes
    with pytest.raises(MarkerError):
        Inner.param.set("ham")

    # do not change when setting own, but efficient is the same
    Outer.param_node.param.set("ham")

    with pytest.raises(MarkerError):
        Outer.param_node.param.set("spam")

    Inner.param.set("eggs")

    with pytest.raises(MarkerError):
        Outer.param_node.param.set(aa.Unset)

    Outer.param_node.param.set("eggs")

    Outer.param_node.param.set(aa.Unset)


def test_signal_set_inheritance_descendant():
    @aa.infuse
    class Ancestor:
        param = "spam"

    @aa.infuse
    class Descendant(Ancestor):
        pass

    # Descendant.param.change is different from Ancestor.param.change
    Descendant.param.changed.connect(mark)
    # Descendant should have a same but independent copy of class default value for the param

    # do not trigger when changing Ancestor
    Ancestor.param.set("ham")

    # do signal when changing Descendant class default
    with pytest.raises(MarkerError):
        Descendant.param.set("eggs")

    with pytest.raises(ValueError):
        Descendant.param.set(aa.Unset) # this probably belongs elsewhere, but this should be forbidden


def test_signal_set_inheritance_ancestor():
    @aa.infuse
    class Ancestor:
        param = "spam"

    @aa.infuse
    class Descendant(Ancestor):
        pass

    # Descendant.param.change is different from Ancestor.param.change
    Ancestor.param.changed.connect(mark)
    # Descendant should have a same but independent copy of class default value for the param

    # do not signal when changing Descendant class default
    Descendant.param.set("eggs")


def test_overwrite_descendant_param_default_value():
    """
    What if we overwrite param in derived class? We should change the default value, or completely
    overwrite the param?

    This is used in figure_qt.QtPlot to change default color.
    Of course we can do
    @paramize
    class QtPlot(Plot, QGraphicsItem):
        ...

    QtPlot.background_color.set("pink")

    and that should work fine, but this is no the same thing, or should it be?
    :return:
    """
    @aa.infuse
    class Test:
        param: str = "spam"

    @aa.infuse
    class Derived(Test):
        param = "ham"

    # fixme: likely the post init part that handles copying derived class params will override the explicit param="ham"
    #  of Derived with a "spam" copy of Test
    # we want the ability to copy and set new value, but that must be done via Derived.param.set("ham")
    # if we explicitly state new param, it should override the one from ancestor class
    #   losing leaders and other stuff
    # so here we still have a bug

    # l 322 paramize: Derived has its own Param descriptor created due to its own param="ham" class attribute overriding the original inherited descriptor from Test
    #  but once derived class test is performed in paramize, it will find out the Test's descriptor as the original one and use its value to
    #  create a "descendant copy"
    # we need to handle the cases where the descendant create its own params separately from those where it inherits them
    #  perhaps split cls._param_params?

    assert Derived.param.value() == "ham"


# TODO: creating a derived class paramized instance will call param_init twice (or more times), is it ok? do a test for this
# for AxisQt it was three times and then directly margin_layout.MarginLayoutPart
#  seems like param_init of ancestor class might get registered as original_init, that is possibly wrong
#  and it skipper QtPart.__init__
# and we are dealing with multiple inheritance here
def test_multiple_inheritance():
    @aa.infuse
    class Part:
        param: str = "spam"


    @aa.infuse
    class Axis(Part):
        pass

    # todo: problem 1 - Axis's paramized_init will call Part's paramized_init, which will call Part's original init (object.__init__)
    #  meaning that the params will be duplicated twice
    #  we probably should NOT call ancestor class paramized_init, but its original init directly
    #  however, we do not have access to that info, it is stored in ancestor's paramized_init closure
    #  - can we modify paramized_init to not repeat already duplicated params?
    #  - or skip paramized_init in original init __mro__ lookup

    @aa.infuse
    class QtPart(Part):
        def __init__(self):
            super().__init__()
            print("special treatment")
            mark()

    @aa.infuse
    class AxisQt(Axis, QtPart):
        ...

    with pytest.raises(MarkerError):
        axis =AxisQt() # this should trigger special treatment

def test_multiple_inheritance_override():
    """
    This is a problem that occured in tolp
    We have such structure
    MarginLayoutPart
       requirements

    QtPart(MarginLayoutPart)

    Axis(QtPart)
        ticks_out:bool = False

    ColorAxis(Axis)
       which in init tries to override the default of ticks_out from Axis
       via super().__init__(ticks_out=True)
       which should be able to set instance self value to True

    tracing the problem, during ColorAxis init it indeed sets ticks_out to True
    but somewhere along the line (when super().__init__ of Axis is called)
    it get overwriten back to False

    it seems that the hierarchy for inheritance is messed up

    but this will be a pain to fix

    :return:
    """

    @aa.infuse
    class Origin:
        param_origin: int = 0
        def __init__(self):
            print("Origin original __init__", f"{self.param_axis()=}")

    @aa.infuse
    class Axis(Origin):
        param_axis: bool = False
        def __init__(self):
            print("Axis original __init__ before super().__init__", f"{self.param_axis()=}")
            super().__init__()
            print("Axis original __init__ after super().__init__", f"{self.param_axis()=}")

    # note that this works, the problem is in calling __init__ of Origin
    # @aa.infuse
    # class Axis:
    #     param_axis: bool = False

    # version 1
    @aa.infuse
    class ColorAxis(Axis):
        def __init__(self):
            print("ColorAxis original __init__ before super().__init__", f"{self.param_axis()=}")
            super().__init__(param_axis=True)
            print("ColorAxis original __init__ after super().__init__", f"{self.param_axis()=}")

    color_axis = ColorAxis()

    # version 2
    @aa.infuse
    class ColorAxis2(Axis):
        def __init__(self):
            print("ColorAxis2 original __init__ before super().__init__", f"{self.param_axis()=}")
            super().__init__()
            print("ColorAxis2 original __init__ after super().__init__", f"{self.param_axis()=}")

    color_axis2 = ColorAxis2(param_axis=True)

    assert color_axis.param_axis() is True
    assert color_axis2.param_axis() is True

    """
    seems like there are two problems
     we are setting nodes of color_axis multiple times
     
    we need to organize how this case should be handled
    
    for sure passing default value to ancestor init should work
    (we can of course change default for the class after its declaration, but that will not force the value the same way 
    as passing value to init would - on the other hand, if we do that, we completely bypass the class default
    perhaps a more consistent way would be to change class default;
    overriding the default after class declaration is fine but the problem is that it is not placed where one would
    expect the default value to be - at the start of class declaration)
    (we can override the param in descendant class, which will create a completely new param, including possible leader 
    and other settings (not only the default value))
    (and anyway, setting value in init should work)
    
    second version changes order of setting the param
    
    
    NOTE:
    Setting value in instance init will not set the class default. The only way to redefine class default
    of descendant class is via Descendant.param.set(value) after class Descendant declaration.
    Using param=value in class Descendant will recreate the param descriptor (ditching all descriptor settings).
    Using param=value in Descendant init will change instance value.  
    """

def test_multiple_inheritance_paramized():
    """
    There was a problem in figure.Text which inherits both
    QtPart (with requirements param) and TextParams (with text param).
    Setting Text() instance text value will reset all texts.

    Tracing the issue, it seems that text node is shared and
    only the class node is used, whereas requirements node is
    properly duplicated for instance.

    Perhaps param_init cannot duplicate params hierarchies from multiple
    ancestors?
    :return:
    """

    @aa.infuse
    class Ancestor1:
        text:str = "Default text"

    @aa.infuse
    class Ancestor2:
        number:int = 10

    @aa.infuse
    # class Descendant(Ancestor2, Ancestor1):  # will fail text check
    class Descendant(Ancestor1, Ancestor2):  # will fail number check
        pass

    instance = Descendant()

    instance2 = Descendant()

    instance2.text.set("changed")
    instance2.number.set(20)

    """
    The problem lies in param_init, when handling params from ancestor classes
    the lookup is done via cls._param_params.
    But that is taken from the first ancestor class and not from both of them.
    
    TODO: there will be a conflict if the two ancestor classes each define param
    with the same name. This should return an exception. But do take care
    of going through __mro__, because if we have an even older ancestor, the newer
    ancestor is supposed to have its params. 
    We only need to look for cls._param_params of direct sibling ancestors
    (unless we have some obscure situation that one of the ancestors is not 
    paramized, but has paramized ancestor; hopefully noone will make such 
    a thing).
    
    i.e. scan __bases__ instead of __mro__
    
    fixed
    """

    assert instance.text() == "Default text"
    assert instance.number() == 10

def sand_multiple_inheritance_nonparamized():
    class Part:
        param: str = "spam"
        def __init__(self):
            print("Part.__init__ start")
            super().__init__()
            print("Part.__init__ end")



    class Axis(Part):
        def __init__(self):
            print("Axis.__init__ start")
            super().__init__()
            print("Axis.__init__ end")

        pass

    # todo: problem 1 - Axis's paramized_init will call Part's paramized_init, which will call Part's original init (object.__init__)
    #  meaning that the params will be duplicated twice
    #  we probably should NOT call ancestor class paramized_init, but its original init directly
    #  however, we do not have access to that info, it is stored in ancestor's paramized_init closure
    #  - can we modify paramized_init to not repeat already duplicated params?
    #  - or skip paramized_init in original init __mro__ lookup

    class QtPart(Part):
        def __init__(self):
            print("QtPart.__init__ start")
            super().__init__()
            print("QtPart.__init__ end")

    class AxisQt(Axis, QtPart):
        def __init__(self):
            print("AxisQt.__init__ start")
            super().__init__()
            print("AxisQt.__init__ end")


    axis = AxisQt()


def test_paramize_stop():
    # we need the ability to tell paramize that some class attribute is NOT a param
    @aa.infuse
    class Test:
        param1: str = "spam"
        param2 = 10
        command:str = aa.END_OF_ATTRS

        # this is bad, because it goes first over all __annotations__
        #  and command is only in __dict__
        #  and how are we supposed to know that some __dict__ entry was before?
        # on the other hand if command is processed as annotated, param2
        #  will be left out, since it is only in __dict__
        # do we really have to force order of annotated and non-annotated params?
        #  is it even doable?
        # or force all params to be annotated? that is a pain
        # we cannot reconstruct order from __dict__ and __annotations__
        #   only metaclass has the original order :(
        #   there is probably no guarantee of order here

        # well it seems that __dict__ keeps order __module__, __annotations__, class attributes in order, __dict__ ...
        #  but we need at least define values of annotated params without default value so that they are included into __dict__

        not_a_param1: str = "jam"
        not_a_param2 = "ham"
        not_a_param3:int

        def test(self):
            ...

        def __init__(self):
            ...

    # assert "not_a_param" not in Test._param_params
    assert Test._attrarchy_attrs == ("param1", "param2")

def test_ignore_descriptor():
    """
    paramize should ignore descriptor and not interpret them as params
    (unless they are Param descriptors).

    This is to allow using ClassSignal and perhaps even Qy signals
    easily.
    :return:
    """

    @aa.infuse
    class Paramized:
        param1 = 51
        signal = aa.ClassSignal()

    assert Paramized._attrarchy_attrs == ("param1",)
    assert hasattr(Paramized, "signal")



def test_paramize_stop2():
    # we need the ability to tell paramize that some class attribute is NOT a param
    @aa.infuse
    class Paramized:
        param1: str = "spam"
        param2 = 10
        param3: int
        command:int = aa.END_OF_ATTRS

        not_a_param1: str = "jam"
        not_a_param2 = "ham"
        not_a_param3:int

        """
        problem here is that paramize will scan annotated and
        mark those without default value with special value
        to include them into dict
        but it will not keep order there (it will be appended to the end)
        it has no way of knowing if param3:int was before or after
         command
         
        we need to make the command both annotated (with whatever datatype)
         and with special value (it would be possible to use special name instead)
         only with this can we determine correct order in both __annotations__ and __dict__
        
        this test fails, but that is Ok, since param3 is not valid, but I wanted
        to test if paramize will catch it as a param  
        """

        def __init__(self):
            ...

    # assert "not_a_param" not in Test._param_params
    assert Paramized._param_params == ("param1", "param2", "param3")


# -------------------------

def test_on_changed():
    """
    Paramized class (node Param) might have defined on_changed()
    method which will be called right before changed signal is emitted.

    (this is a manual test right now)
    :return:
    """
    @aa.infuse
    class Paramized:
        param1: int = 10
        param2 = "spam"

        def on_changed(self, **changed_params):
            print("on_changed:", changed_params)

    instance = Paramized()
    instance.param1.set(20)

    instance.set(param2="ham")




# ---------------------------

"""
TODO:
nested paramized classes

nested paramized classes with leaders

nested classes with leaders

implementation details:
setting value will not change the descriptor on the class
setting value will not change instance of paramized class


paramize abstract base class
and/or something derived from ABC


cyclic params
A.B

B.A




there is a specific situation
 we have a paramized class
 we make a derived class from that, but forget to paramize it
   -> it will use params of the ancestor class (so far it might it intentional)
   -> BUT it seems this will cause instances of the derived class to also use params of the ancestor class directly,
     instead of creating their own instance hierarchy
     this is likely a bug and needs to be resolved
     (does it not call param_init at all? It might not if super().__init__ is not called. But the situation remain
     even if super().__init__ is called...)
     
     the general expectation is for the derived class to be also paramized (which would result in it having its own 
     param_init and copy of params)
     but there is no rule forbidding it not being paramized nor enforcing it being paramized
     This might result in some pretty obscure bugs!
     
"""
