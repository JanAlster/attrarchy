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

import functools
import logging
import types
from typing import Self, Any


## helpers

class NamedObject:
    """
    For creating unique sentinel values.
    Better that using object() directly, since we can
    pattern match against NamedObject() to capture these sentinels
    but pattern matching against object() will gobble everything.
    """

    def __init__(self, name:str|None=None):
        self._name = name

    def __repr__(self) -> str:
        if self._name is None:
            return super().__repr__()
        return self._name

    # def __eq__(self, other):
    #     return self is other
    # I have wanted to add this to prevent some edge case problems
    #  but it makes this unhashable, which is a no-go


Unset = NamedObject("Unset")
END_OF_ATTRS = NamedObject("End_of_attrs")
"""
Use 
`command:str = END_OF_ATTRS`
to mark a end of infusing (rest of the class attributes will not be enhanced).
Unfortunately, in the current implementation, we need both value and type
annotation for the command. Actual name of the class attribute and its
datatype can be whatever.
"""

#Follower = typing.TypeVar("Follower", bound=Callable)

class Signal[Follower]:
    """
    Keep track of registered callbacks.

    To type hint the expected signature, use with
    my_signal = Signal[Callable[[signal_signature], return_type]]()

    Note: these signals are blocking and sending the signal to followers in order,
     waiting for the response (even if Signal does not do anything with it
     and expects None as the response).
     This works for now, but I am not sure if this is the best approach and
     it might change in the future. Note that QuerySignal needs the responses in
     some cases. But perhaps that could be done asynchronously.

    Todo: use weakref here, no need to keep the followers alive, simply disconnect them on death.
    """
    def __init__(self) -> None:
        self._followers:list[Follower] = []
        self._followers_after:list[Follower] = []


    def connect(self, follower:Follower) -> None:
        """
        Register follower to receive the signal.
        :param follower:
        :return:
        """
        assert follower not in self._followers #todo: this might be a warning
        self._followers.append(follower)

    def connect_after(self, follower:Follower) -> None:
        """
        Primitive ordering in case you need to shift some callback to the back.
        'Connected' callbacks will be notified before callbacks 'connected after'.
        :param follower:
        :return:
        """
        assert follower not in self._followers_after #todo: this might be a warning
        self._followers_after.append(follower)

    def disconnect(self, follower:Follower)->None:
        """
        Unregister follower from receiving the signal. Note that this will remove
        first occurrence of the follower from the known followers.

        It is assumed that a single follower is only connected once.
        It is possible to connect a single follower to both connect and conect_after.
        (That might change in the future.) In this case first call of disconnect
        will disconnect the connect connection. Second call will disconnect the
        connect_after connection.

        Raise RuntimeError for unknown follower.

        :param follower:
        :return:
        """
        if follower in self._followers:
            self._followers.remove(follower)
            return

        if follower in self._followers_after:
            self._followers_after.remove(follower)
            return

        raise RuntimeError(f"Follower {follower} is not connected to signal {self}.")


    def emit(self, *args, **kw) -> None:
        for follower in self._followers:
            follower(*args, **kw)

        for follower in self._followers_after:
            follower(*args, **kw)


class QuerySignal[Follower](Signal):
    """
    Signals that expect a response.
    But only if the signal is emitted via a 'query'.

    Note that it is possible to somewhat type hint the signal signature
    and follower response by (this does not work perfectly):
    my_query_signal = QuerySignal[Callback[[signal_signature], response_type]]()
    """

    def query(self, *args, **kw) -> tuple[list,list]:
        """
        Just send the signal and aggregate the responses.
        :param args:
        :param kw:
        :return: (responses from connected, responses from connected after)
        """
        responses = []
        for follower in self._followers:
            responses.append(follower(*args, **kw))

        responses_after = []
        for follower in self._followers_after:
            responses_after.append(follower(*args, **kw))

        return responses, responses_after

    def query_true_all(self, *args, short_circuit=False, ignore_none=False, **kw):
        """
        Send the signal and process the responses.

        Will ask all connected followers even if some answers False.

        Raises a RuntimeError if answer is not True or False (as in "is True" and not "== True")

        :param args: Will be sent as part of the signal.
        :param short_circuit: If True, query will return after first False response, not sending the signal to the rest of the followers.
        :param ignore_none: If True, ignore None responses.
        :param kw: Will be sent as part of the signal.
        :return: True if all respond True otherwise False
        """
        result = True
        for follower in self._followers + self._followers_after:
            response = follower(*args, **kw)
            if response is False:
                if short_circuit:
                    return False
                result = False
            elif response is not True and not (response is None and ignore_none):
                raise RuntimeError("Response was not True or False (query_true_all requires strict match as in 'is True' and not '== True').")

        return result

    # todo: we can do other queries like false all or true any, ...

class ClassSignal:
    def __init__(self, signal_type:type=Signal):
        self._signal_type = signal_type
        pass

    def __set_name__(self, owner_class:type, signal_name: str):
        self._name = signal_name
        self._instance_attribute_name = "_signal_"+signal_name

    def __get__(self, owner_instance, owner_class):
        logging.debug("ClassSignal.__get__ %s %s", owner_instance, owner_class)
        if owner_instance is None:
            return None

        bound_signal = getattr(owner_instance, self._instance_attribute_name, None)

        if bound_signal is None:
            bound_signal = self._signal_type()
            setattr(owner_instance, self._instance_attribute_name, bound_signal)

        return bound_signal

    # def __set__(self, owner_instance, value):


## end of helpers


## infuse and friends
# todo: typehint descriptor and method

def _find_descriptor(cls:type, attr_name:str):
    """
    Find descriptor while considering inheritance.

    :param cls:
    :param attr_name:
    :return: descriptor or None
    """
    for it in cls.__mro__:
        if attr_name in it.__dict__:
            return it.__dict__[attr_name]
            # get the first one, NOTE that MRO order matters! attrs need to go first (or do not conflict in names with the rest of ancestors)

    raise AttributeError(f"Enhanced class {cls} does not have Attr {attr_name}.")

def _install_method(cls:type, name:str, method) -> None:
    """
    Insert method into cls class definition under name.
    :param cls:
    :param name:
    :param method:
    :return:
    """
    # just in case we want to do something more complex later on
    logging.debug("installing method %s.%s", cls, name)
    setattr(cls, name, method)


def _install_descriptor(cls:type, name:str, descriptor) -> None:
    """
    Insert descriptor into class definition cls under name.
    :param cls:
    :param name:
    :param descriptor:
    :return:
    """
    # just in case we want to do something more complex later on
    logging.debug("installing descriptor %s.%s: %s", cls, name, descriptor)
    setattr(cls, name, descriptor)
    descriptor.__set_name__(cls, name)


def is_infused(cls:type) -> bool:
    """
    Is the cls enhanced?
    Also returns True if is enhanced indirectly (inherited).
    :param cls:
    :return:
    """
    return hasattr(cls, "_attrarchy_attrs")


def _is_directly_infused_class(cls:type) -> bool:
    """
    Is the cls directly enhanced (no inheritance)?
    :param cls:
    :return:
    """
    for name in ("_value_up", "_value_down", "_change_leader_value", "_change_parent_value"):
        if name not in cls.__dict__:
            return False

    return True


def infuse(cls: type):
        """
        Add Node interface to cls:
        - search for class attributes to change into Attrs
        - add __init__ creating and setting up the attrs
        - add value lookup mechanism traversing the attr's hierarchy
    
        :param cls: target class for infusion
        :return:
        """

        logging.debug("infusing into class %s", cls)
        # search for attrs
        attrs = []  # found attrs

        # attrs with typehint will be in __annotations__
        logging.debug("probing __annotations__")
        logging.debug("%s", cls.__annotations__)
        for name in cls.__annotations__:
            if name not in cls.__dict__:
                # for now, we will need to use annotated stop command :( and create attrs without default value here
                logging.debug("attrs without a default value: %s", name)
                attr = Attr(cls.__annotations__[name])
                _install_descriptor(cls, name, attr)
                attrs.append(name)
            elif cls.__dict__[name] is END_OF_ATTRS:
                break


        # attrs without typehint will be in __dict__
        # we need to find them
        to_change = []
        logging.debug("probing __dict__")
        logging.debug("%s", cls.__dict__)
        for name in cls.__dict__:
            value = cls.__dict__[name]
            # we could use match here
            if value is END_OF_ATTRS:
                logging.debug("END_OF_ATTRS found, stopping __dict__ scan")
                break

            # ignore original class methods
            if isinstance(value, types.FunctionType):
                continue

            # ignore descriptors
            if hasattr(value, "__get__") and not isinstance(value, Attr):
                logging.debug("ignoring suspected descriptor %s: %s", name, value)
                continue

            # ignore our own internals
            if name.startswith("_attrarchyValue_"):
                logging.debug("ignoring previously added internal attr storage %s", name)
                continue

            if name == "_attrarchy_attrs":
                logging.debug("ignoring _attrarchy_attrs class attr memory")
                continue

            # ignore dunders
            if name.startswith("__"):
                logging.debug("ignoring dunder %s", name)
                continue

            # ignore already registered attrs
            if name in attrs:
                logging.debug("ignoring previously registered attr %s", name)
                continue

            # register the rest
            to_change.append(name)

        original_init = cls.__dict__.get("__init__", False)

        # postponed to prevent modification of __dict__ during iteration over it
        for name in to_change:
            logging.debug("installing descriptor %s", name)
            value = cls.__dict__[name]
            if not isinstance(value, Attr):
                _install_descriptor(cls, name, Attr(value))
            attrs.append(name)

        # store a tuple of attrs
        # what if cls is derived from a infused class? It shall inherit the attrs too!
        derived = hasattr(cls, "_attrarchy_attrs")
        derived_map = {} # {original_node:copied_node}
        if derived:
            # but we need to make our own nodes, otherwise we will share default values with the ancestor class
            # copy node
            node_map = {}  # {old_node:new_node, ...}
            leader_map = {}  # {new_node:old_leader, ...}

            # we have to check all direct ancestor classes, not just the first one which has _attrarchy_attrs
            ancestor_attrs = []
            for ancestor_cls in cls.__bases__:
                if is_infused(ancestor_cls):
                    for ancestor_attr in ancestor_cls._attrarchy_attrs:
                        if ancestor_attr in ancestor_attrs:
                            raise RuntimeError(f"Class {cls} inherits attr {ancestor_attr} from multiple ancestor classes.")
                        ancestor_attrs.append(ancestor_attr)


            for attr_name in ancestor_attrs:
                # attr_name is from ancestor class, but it might be overridden in the descendant class in which case we should NOT proceed here
                if attr_name in to_change:
                    continue
                descriptor = _find_descriptor(cls, attr_name)
                # original attr node is saved on Attr descriptor owner, but we should overwrite that
                # we do not overwrite the descriptor though
                # but we should store the node setattr(cls, descriptor.class_node_attr, copy_of(original_node, ie. what descriptor gives back)
                # this depends on Attr implementation, so it is not that nice
                original_node = getattr(descriptor._owner, descriptor.class_node_attr)

                logging.debug("derived infused class node duplication: cls %s, attr_name %s", cls, attr_name)

                if descriptor.infused:
                    copied_node = descriptor.attrarchy_class(_construction=(attr_name, cls,
                                                                                      node_map, original_node,
                                                                                      leader_map),
                                                                       )
                elif isinstance(original_node, AttrLeaf):
                    copied_node = AttrLeaf(parent=cls, name=attr_name, value=original_node._value)
                else:
                    raise RuntimeError("An attrs is neither node (infused) nor a leaf.")

                node_map[original_node] = copied_node
                if original_node._attrarchy_leader is not None:
                    leader_map[copied_node] = original_node._attrarchy_leader

                setattr(cls, descriptor.class_node_attr, copied_node)
                derived_map[original_node] = copied_node
                # derived_map = {original_node:copy_node}

                for item in leader_map:
                    item._attrarchy_leader = node_map[leader_map[item]]

            cls._attrarchy_attrs = tuple(ancestor_attrs) + tuple(attrs)
        else:
            cls._attrarchy_attrs = tuple(attrs)


        logging.debug("attrs summary for %s: %s", cls, cls._attrarchy_attrs)

        # all the attrs are changed to descriptors, it is time to link leaders
        for attr_name in cls._attrarchy_attrs:
            #this is slightly tricky, the descriptor might belong to ancestor class and might not be in cls.__dict__
            if attr_name not in cls.__dict__:
                continue

            descriptor = cls.__dict__[attr_name]
            leader = descriptor.leader_to_be
            if leader is not None:
                # inside infuse we deal with class hierarchy and leaders there have to be on the same hierachy as followers
                """
                WIP 
                
                @infuse
                class Test:
                    param1 = Attr("spam")
                    param2 = Attr(leader=param1)
                    
                class Test2(Test):
                    #param3 = Attr(leader=Test2.param2) #this cannot be done, but that is what is meant here    
                    param3 = Attr(leader=Test.param2) #this should be valid
                    # the meaning here is that Test2 will use its own param2 and not Test.param2 directly
                    # this is simply to ensure that setting the default value is not shared between derived classes
                    # but Test.param2 will trigger Test.param2 descriptor's __get__ with instance=None and owner=Test
                    #  and will return not the descriptor, but AttrLeaf instance (whereas leader=param in Test 
                    #     declarataion will give directly the descriptor, since Test class is not ready yet)
                    #  AND we need that it is the Test2 param2's node (or replace it) and not Test's one 
                    #  however, during Test2 declaration, we will not get it as the owner
                    # we probably need to keep the links on the descriptor levels on class hierarchy and keep 
                    # the default value separate as hidden class attributes   
                    # on the instance hierarchy the links need to be on instances
                    
                    # ideally, we would want to delay the resolution of leaders only after the class is done, or 
                    #  do it in infuse - but the only way is to keep the expression as a string - that is not acceptable
                    
                    in infuse we have access to the derived class, we will have to recast (one level only?)
                    attr nodes to new class, we can trace the attrs to root (which should be the class being infused)
                    and use its name to find the new node or create one
                    
                class Test3:
                    param3 = Attr(leader=Test.param1) # this is forbidden since Test3 and Test are not on the same hierarchy    
                    
                we also might use
                class Test:
                    param = Attr(leader=Test.paramX.paramY)    
                    
                going with this, descriptor.leader_to_be is a descriptor and the leader should be a node instance 
                 on class hierarchy 
                """
                if isinstance(leader, Attr):
                    # if leader is Attr, it should be something declared on the class-being-infused directly
                    # leader = leader.node
                    leader = leader.__get__(None, cls)
                elif derived:
                    if leader in derived_map:
                        leader = derived_map[leader]

                # enforce leader and node from same class hierarchy
                leader_path = path_to_root(leader)
                node = getattr(cls, attr_name)
                node_path = path_to_root(node)
                if not leader_path[-1] is node_path[-1]:
                    raise ValueError("Leader has different root from node.\n", leader_path, node_path)

                node._attrarchy_leader = leader
                leader._changed_instance_signal.connect(node._change_leader_value)

        if not hasattr(cls, "attrs"):
            @classmethod
            def attrs(cls) -> tuple:
                """
                Returns names of all attrs.
                :param self:
                :return:
                """
                # maybe: could be an iterator
                return cls._attrarchy_attrs

            _install_method(cls, "attrs", attrs)

        _check_all_leaders_on_same_hierarchy(cls)
        _check_all_leaders_match_follower(cls)

        # value lookup methods
        """
        Note that we can get rid of storing name on each attr if we lookup the name in __dict__.
    
        def search(dic, value):
            return next((key for key, val in dic.items() if val == value), None)
    
        Trading memory for speed.
        - __dict__ should be small, so the lookup should be fast, but it will still be slower
        - name will not be that large either, but I want to limit the number of things added to 
    
        Each instance might keep a lookup dictionary, but it would be probably better to just store the name.
        One point though: attrs do not know their names during the class definition
        whereas __dict__ search will work always.
    
        I would prefer speed, so put name to each attr instance.
        Question is then how to handle arguments of infused class original init and attrarchy_init.
    
        Duplication __init__ needs: name, parent and _construction; it can also get setup values for attrs.
    
        When building class node in Attr, name and parent are not know, so we cannot supply those.
        Can we separate __init__ and duplication?
        Node in Attr will create instances of its subattrs - so it will need the duplication.
        """
        # todo: _value_up and _value_down need not be methods, we can use functional programming here to keep the infused class clean(er)
        def _value_up(self, name, names=None):
            """
            Traverse the hierarchy to look for the effective value. Moving up the tree (or sideways).

            :param self:
            :param name:
            :param names:
            :return:
            """
            logging.debug("infused class _value_up: self %s, name %s, names %s", self, name, names)
            if names is None: names = []

            if self._attrarchy_leader is not None:
                value = self._attrarchy_leader._value_down(name, names)

                if value is not Unset:
                    return value

            # for nodes on class hierarchy, the root is not an instance, but a class,
            #  it does not have a leader and it does not have self attached, so do not call it
            # We need it to be present on the path because we check for common root and None does not fit the bill.
            # So either is_infused() will fail on that (as it was probably intended), or we add additional test here.
            if is_infused(self._attrarchy_parent) and not isinstance(self._attrarchy_parent, type):
                # todo: it always have to check all the way up to root
                #  we can do some flag parent_has_leader that will propagate down in the hierarchy
                #  to limit this need (only do that if parent_has_leader)
                names.append(name)
                return self._attrarchy_parent._value_up(self._attr_name, names)

            # give up
            return Unset

        _install_method(cls, "_value_up", _value_up)

        def _value_down(self, name, names):
            """
            Traverse the hierarchy to look for effective value. Moving down the tree.
            :param self:
            :param name:
            :param names:
            :return:
            """
            # we require that leader has the same hierarchy
            if name not in self._attrarchy_attrs:
                raise TypeError("Leader does not have required attr")  # TODO: this should be checked earlier

            if len(names) == 0:
                # name should be a Leaf
                # return getattr(self, name).value()  # this should invoke the "name" Attr descriptor
                return getattr(self, name).value(_instance_only=True)  # todo: this is a bit tricky

            return getattr(self, name)._value_down(names[-1], names[:-1])

        _install_method(cls, "_value_down", _value_down)


        def set(self, **attrs):
            """
            This is equivalent to setting own values of subnodes of self.
            :param self:
            :param attrs: attrs to set {name:value, ...}
            :return:
            """
            self._attrarchy_multiset_guard = True
            for attr_name in attrs:
                if attr_name not in self._attrarchy_attrs:
                    raise ValueError(f"'{attr_name}' is not a valid attr of {self}.")

                getattr(self, attr_name).set(attrs[attr_name])
            self._attrarchy_multiset_guard = False
            # todo: it seems that changing own value to 0 from Unset, with class default 0,
            #  will result in change of instance value and it will be added to self._attrarchy_changed_instance_values
            #  it is true that instance value changed from Unset to 0, but is this what we want?
            #  probably yes...

            if len(self._attrarchy_changed_instance_values)>0:
                self._changed_instance_signal.emit(self._attrarchy_changed_instance_values)
                self._attrarchy_changed_instance_values = {}

            if len(self._attrarchy_changed_values) > 0:
                # MARK
                # self._changed_signal.emit(self._attrarchy_changed_values)
                """
                This is not perfect. Because if we do not define on_changed
                directly on the infused class, it will not be in __dict__
                but we want to call which ever here, even from ancestors. 

                We cannot do this at infuse time, we need
                to check at runtime.
                There is a possibility that on_changed is defined 
                on non-infused descendant class of a infused one,
                in which case infuse cannot know about existence
                of on_changed() here.
                """
                if hasattr(self, "on_changed"):
                    self.on_changed(**self._attrarchy_changed_values)
                self._changed_signal.emit(self._attrarchy_changed_values)
                self._attrarchy_changed_values = {}
        _install_method(cls, "set", set)

        def value(self):
            """
            Get infused class (node) value
            as {attr_name:attr_value, ...}.
            :param self:
            :return:
            """
            return {attr_name:getattr(self, attr_name).value() for attr_name in self._attrarchy_attrs}
        _install_method(cls, "value", value)


        def _subnode_instance_value_changed(self, attr_name, value):
            """
            Handle subnode changing value on instance
            :param self:
            :param attr_name:
            :param value:
            :return:
            """
            self._attrarchy_changed_instance_values[attr_name] = value
            if not self._attrarchy_multiset_guard:
                self._changed_instance_signal.emit(self._attrarchy_changed_instance_values)
                self._attrarchy_changed_instance_values = {}
        _install_method(cls, "_subnode_instance_value_changed", _subnode_instance_value_changed)


        def _subnode_value_changed(self, attr_name, value):
            self._attrarchy_changed_values[attr_name] = value
            if not self._attrarchy_multiset_guard:
                # MARK
                """
                This is not perfect. Because if we do not define on_changed
                directly on the infused class, it will not be in __dict__
                but we want to call which ever here, even from ancestors 

                We cannot do this at infuse time, we need
                to check at runtime.
                There is a possibility that on_changed is defined 
                on non-infused descendant class of a infused one,
                in which case infuse cannot know about existence
                of on_changed() here.
                """
                if hasattr(self, "on_changed"):
                    self.on_changed(**self._attrarchy_changed_values)
                self._changed_signal.emit(self._attrarchy_changed_values)
                self._attrarchy_changed_values = {}

        _install_method(cls, "_subnode_value_changed", _subnode_value_changed)

        def _change_leader_value(self, values):
            """
            Leader value will be sent here.
            AttrLeaf will directly remember it, but infused class needs to send it on,
              distributed to individual attrs, as "parent value"
            :param self:
            :param values:
            :return:
            """
            for attr_name in values:
                getattr(self, attr_name)._change_parent_value(values[attr_name])
        _install_method(cls, "_change_leader_value", _change_leader_value)

        def _change_parent_value(self, **values):
            """
            infused class might also receive a parent value, just distribute it down the chain
            :param self:
            :param values:
            :return:
            """
            # this is actually the same as _change_leader_value for infused class
            for attr_name in values:
                getattr(self, attr_name)._change_parent_value(values[attr_name])
        _install_method(cls, "_change_parent_value", _change_parent_value)

        # descriptor/property for changed signal

        def changed(self):
            """Notification signal of change of effective value (own or passed from leader or parent)."""
            return self._changed_signal
        _install_method(cls, "changed", property(changed))

        # set_leader - change leader on instance level
        #   equivalent to AttrLeaf.set_leader
        def set_leader(self, leader:Attr = None):
            """
            Set leader for this node.
            :param self:
            :param leader:
            :return:
            """
            if leader is None:
                self._attrarchy_leader = None
                return
            # todo: possibly do some checks
            self._attrarchy_leader = leader
        _install_method(cls, "set_leader", set_leader)

        # todo: consider this
        # But this means that the infused class itself does not have a changed signal
        # @infuse
        # class Test:
        #   param1: str = "spam"
        #   param2: int = 10
        #
        # Changing Test.param1 will trigger Test.param1.changed signal
        # But there is no Test.changed signal
        #
        # class Test2:
        #     param: Test
        #
        # Test2.param is an instance and it does have changed signal
        # and changing Test2.param.param1 will (or should) trigger both
        # Test2.param.param1.changed and Test2.param.changed
        #
        # So there is a bit of asymmetry here

        # Moreover, we need an update method that will change values of nested attrs, but only trigger the master
        #  changed signal once.
        # Test2.param.update(param1="ham", param2=0)
        # And that should work as Test.update(param1="ham", param2=0)
        #   but it should trigger some changed signal too...
        #  So we probably need Test.changed too ... or not?
        #  We can only allow signals on instances and assume that changing the class default will trigger them
        #   when appropriate.


        def create_attrarchy_init():
            # this construct will allow using super() in attrarchy_init
            __class__ = cls
            def attrarchy_init(self, *args, _construction=None, **values):
                """
                This is creation of a infused class instance. Copy the attr class hierarachy to
                the instance hierarchy (replacing self.__class__ with self as the root of the hierarchy).

                :param self:
                :param _construction: (name=Unset, parent=None, node_map, class_hierarchy_subnode, leader_map)
                :param values: initialization values for attrs (if set) and other kw for original init
                :return:
                """

                # Handle infused derived classes. Only run the attrarchy_init once
                """
                Derived class is supposed to have its own nodes to shadow those from ancestor, so that
                it does not share the default value of the ancestor.
                
                There is a problem though. What if we run attrarchy_init on the first (most descendant) class 
                (what the instance actually is), but some of the ancestors init has implicit default value?
                
                @infuse
                class OldAncestor:
                    param:bool = False
                
                @infuse
                class Ancestor(OldAncestor):
                    def __init__(self, param=True):
                        super().__init__()
                
                @infuse
                class Descendant(Ancestor):
                    ...
                    
                instance = Descendant()
                
                What will happen:
                - we call attrarchy_init installed on top of Descendant
                 - it will create all instance nodes using Descendant default values
                 - and trigger original_init  
                - since we do not have init on Descendant, Ancestor's init will be called
                  but that is in fact shadowed by Ancestors attrarchy_init, right?
                - and that will create nodes from scratch, using Ancestors default values
                - and triggers super().__init__, i.e. OldAncestors init, or rather OldAncestors attrarchy_init   
                 
                 -> it seems that the easiest way out is to only call original_init if we are not the first attrarchy_init
                 
                Another version    
                @infuse
                class OldAncestor:
                    pass
                
                @infuse
                class Ancestor(OldAncestor):
                    param:bool = False
                
                @infuse
                class Descendant(Ancestor):
                    def __init__(self):
                        super().__init__(param=True)
                    
                    
                instance = Descendant()
                
                
                There is another problem, if we use param=value several times, if we call attrarchy_init only for the first one
                and then use these values to override the value, we will keep the value from the oldest ancestor that 
                sets it. 
                That is the case even for init, if it does not set value after super().__init__ call.
                attrarchy_init sets values first, so if you want to propagate, be sure to explicitly repeat the value in super().__init__(param=value) call
                todo: this seems tedious so perhaps it might be automated later on
                """
                # print(f"instance {self.__class__=}, closure {__class__=}")

                logging.debug("attrarchy_init %s", self)

                # only create instance hierarchy nodes if we are the first attrarchy_init in the line
                #  otherwise only call original_init

                # first direcly infused class
                for test_class in self.__class__.__mro__:
                    if _is_directly_infused_class(test_class):
                        break

                if test_class is __class__:
                    # Create a infused class instance with all of its Attrs unset.

                    # mimic Attr here
                    self._attrarchy_leader = None
                    self._attrarchy_parent = None
                    self._attr_name = Unset

                    # signals
                    self._changed_instance_signal = Signal()  # this has to be named the same as in AttrLeaf
                    self._changed_signal = Signal()
                    self._attrarchy_changed_instance_values = {}
                    self._attrarchy_changed_values = {}
                    self._attrarchy_multiset_guard = False

                    # We need to create the instance hierarchy chain for Attrs,
                    # i.e. create empty Attrs shadowing the class Attrs.

                    # We need to link to equivalent leaders, which might be on different level/branches of the hierarchy
                    #  so we need to keep track of the whole thing.

                    # todo: this must not trigger the signals, perhaps install directly to _attrarchy_instace_value
                    #  but infused class does not have access to that

                    # todo: sending _construction as a init parameter is not very user friendly for original __init__
                    #  perhaps it will not cause too much problems, but otherwise, we can store the info on the root
                    #  of the instance hierarchy (each level would have to grab it from there, so it will be slower)

                    cls = self.__class__

                    """
                    Here we have an issue
                    Subnode change should trigger self change signal. 
                    But it should be processed after all other responses to
                    the subnode change are done, not before them.
                    
                    If we connect the signals here, they will be first in line.
                    And the global object (self) will notify of its part change
                    before other things connected directly to the subnode
                    can react to the change.
                    
                    Options
                    - somehow change order of triggering recievers
                      - but in general I want to keep order of adding them
                    - do not handle triggering node changed signal as response
                    to subnode change signal, but have subnode give another
                    notification after all its receivers are handled?
                      - another signal triggered after changed signal is handled
                        - that means another signal...
                      - directly access node from subnode (I do not like the sound of that)
                         and trigger the change...   
                      - have signal keep two lists, normal ones and delayed?
                         e.g. connect_after()                      
                    """

                    if _construction is None:
                        node_map = {}  # {old_node:new_node, ...}
                        leader_map = {}  # {new_node:old_leader, ...}
                        logging.debug("top level duplication %s", self)

                        for attr_name in cls._attrarchy_attrs:
                            descriptor = _find_descriptor(cls, attr_name)
                            class_hierarchy_subnode = descriptor.__get__(None, cls)
                            instance_hierarchy_subnode = _copy_subnode(descriptor, class_hierarchy_subnode, self,
                                                                       node_map, leader_map, attr_name, values)
                            # connect signals
                            instance_hierarchy_subnode._changed_signal.connect_after(functools.partial(self._subnode_value_changed, attr_name))
                            instance_hierarchy_subnode._changed_instance_signal.connect_after(functools.partial(self._subnode_instance_value_changed, attr_name))
                            pass

                    else:
                        name, parent, node_map, class_hierarchy_node, leader_map = _construction
                        self._attr_name = name
                        self._attrarchy_parent = parent

                        for attr_name in class_hierarchy_node._attrarchy_attrs:
                            # descriptor = cls.__dict__[attr_name]
                            descriptor = None
                            for it in cls.__mro__:
                                if attr_name in it.__dict__:
                                    descriptor = it.__dict__[attr_name]

                            class_hierarchy_subnode = getattr(class_hierarchy_node, descriptor.attrarchy_node_attr)
                            instance_hierarchy_subnode = _copy_subnode(descriptor, class_hierarchy_subnode, self,
                                                                       node_map, leader_map, attr_name, values)
                            # connect signals
                            instance_hierarchy_subnode._changed_signal.connect_after(functools.partial(self._subnode_value_changed, attr_name))
                            instance_hierarchy_subnode._changed_instance_signal.connect_after(functools.partial(self._subnode_instance_value_changed, attr_name))
                            pass


                    # only the first one/top most should assign leaders
                    if _construction is None:
                        # print("node_map", {key._attr_name: node_map[key]._attr_name for key in node_map})
                        # print("leader map", leader_map)

                        for item in leader_map:
                            item._attrarchy_leader = node_map[leader_map[item]]
                            # connect the leader signals
                            item._attrarchy_leader._changed_instance_signal.connect(item._change_leader_value)

                else:
                    # If we are not the first attrarchy_init in line, gobble up all attr values
                    # original_init will not expect them!
                    for attr_name in self.__class__._attrarchy_attrs:
                        if attr_name in values:
                            # nodes should be already set
                            value = values.pop(attr_name)
                            attr = getattr(self, attr_name)
                            if isinstance(attr, AttrLeaf):
                                attr.set(value)
                            else:
                                attr.set(**value)

                if original_init:
                    # original_init is stored in the closure, not on instance
                    #  so it will be inaccessible from outside
                    original_init(self, *args, **values)
                else:
                    super().__init__(*args, **values)
                pass

            return attrarchy_init


        _install_method(cls, "__init__", create_attrarchy_init())

        return cls


## Internals


import inspect

dump_args_level = -1


def dump_args(func):
    """
    Decorator to print function call details.

    This includes parameters names and effective values.
    """

    def wrapper(*args, **kwargs):
        global dump_args_level
        func_args = inspect.signature(func).bind(*args, **kwargs).arguments
        func_args_str = ", ".join(map("{0[0]} = {0[1]!r}".format, func_args.items()))
        dump_args_level += 1
        print(" " * dump_args_level, f"{func.__module__}.{func.__qualname__} ( {func_args_str} )")
        res = func(*args, **kwargs)
        print(" " * dump_args_level, "returns", res)
        dump_args_level -= 1
        return res

    return wrapper


def path_to_root(node):
    """
    Follow node.parent up to the end.
    I do not want to have this on every infused class so it can be a function instead.
    :param node:
    :return:
    """
    path = [node]
    while hasattr(path[-1], "_attrarchy_parent") and path[-1]._attrarchy_parent is not None:
        path.append(path[-1]._attrarchy_parent)
    return path



def print_hierarchy(node, level=""):
    if level == "":
        print("-- print_hierarchy -------------------------")
        path = path_to_root(node)
        if isinstance(path[-1], type):
            print(" (class hierarchy)")
        else:
            print(" (instance hierarchy)")

    print(level, node)

    if is_infused(node):
        for attr in node.attrs():
            print_hierarchy(getattr(node, attr), level=level + "  ")
    else:
        print(level + "  ", "effective value:", node.value())
        # maybe: print value lookup path



# Note: I do not want to separate AttrLeaf and AttrNode since it will make the user interface less intuitive
#  (although probably more explicit) - user would have to distinguish Leaf and Node when specifying the Attr.
# Attr has to handle 4 different cases: Leaf (actual attr) or Node (groups of attrs)
# on class hierarchy (default values) or instance hierarchy (actual values).



class AttrLeaf[ValueType]:
    """
    Helper class to store Attr actual value.
    """

    def __init__(self, value:ValueType|Unset=Unset, parent=None, name="<unset>", class_leaf=None):
        logging.debug("AttrLeaf.__init__ value %s, parent %s, name %s", value, parent, name)
        self._attr_name = name
        self._attrarchy_parent = parent
        self._attrarchy_leader = None

        # None for the AttrLeaf on class hierarchy
        # or the AttrLeaf on class hierarchy (default value) for the ones on instance hierarchy
        self.class_leaf = class_leaf
        # note that name and class_leaf are the same for all equivalent AttrLeafs
        #  we can store a link to the Attr descriptor instead

        self._leader_instance_value = Unset
        self._parent_instance_value = Unset
        self._class_effective_value = Unset

        if class_leaf is not None:
            self.class_leaf.changed.connect(self._change_class_value)
            self._class_effective_value = self.class_leaf.value()

        self._changed_signal = Signal()
        self._changed_instance_signal = Signal()

        self._value = Unset
        self.set(value)


    #read only protection
    @property
    def changed(self) -> Signal:
        """Notification signal of change of effective value (own or passed from leader or parent)."""
        return self._changed_signal

    """
    The tricky part with signals is to know when to emit.
    
    Because if our own value is not set, we need to listen to leaders and parent and perhaps even default AttrLeafs on class definitions.
    
    But if AttrLeaf will be listening to leaders and parents for value changes, in case that these will change its effective
    value, we might as well store the last leader or parent value so that we do not need to look it up when needed.
    
    This will of course lead to massive duplication of values everywhere. Every AttrLeaf will not store only its own
    value, but its parent value and possibly its leader value (if it has a leader). 
    
    Or we might disconnect listening to leader and parent when we have own value?
    It is also true that we do not care about leaders effective value, we only should consider its instance hierarchy value.
    For that we need another signal and we need to consider when to emit that. 
    """

    def __repr__(self) -> str:
        return f"AttrLeaf {self._attr_name} of {self._attrarchy_parent}"


    def set_leader(self, leader:Self|None = None) -> None:
        """
        Set leader for this attr. Leader's value will be used if own value is not set.

        :param leader: AttrLeaf, or None to remove leader.
        :return:
        """
        if leader is None:
            self._attrarchy_leader = None
            return

        # todo: with Attr._leader_to_be is it even possible to have type(leader)==Attr here?
        # if isinstance(leader, Attr):
        #     self._attrarchy_leader = leader.node
        #     return
        #
        #     leader = leader.node
        #
        #     # I assume that this can only happen when linking leader from different level of the hierarchy inside
        #     #  class definition (see test_mock_lookup6.py test_lookup_unset_leaf_on_node_with_set_leader_on_root())
        #     # In that case we need the leader to be from the same hierarchy as self.
        #     # And the root of the hierarchy is a class, not an instance.
        #
        #     # ok, this does not work - during class definition we do not have parent and name set, we only get it after
        #     #  - options:
        #     #   -> set the leader anyway and let infuse traverse the whole hierarchy and check the leaders (it does
        #     #   that for top level Attrs)
        #     #   -> store the info somewhere and let infuse set the leaders similar to top level Attrs._leader_to_be
        #     #  question is where to save it? we do not have access to the parent here ...
        #     self_path = path_to_root(self)
        #     assert isinstance(self_path[-1], type), self_path
        #     leader_path = path_to_root(leader)
        #     if self_path[-1] is not leader_path[-1]:
        #         raise ValueError("Leader has different root from self.\n", leader_path, self_path)
        #
        #     self._attrarchy_leader = leader
        #     return

        # here I assume that we are linking on instance level and do not keep inside the same hierarchy
        #  (the requirement for the same hierarchy is necessary to allow duplication of class hierarchy
        #  to instance hierarchy - we cannot do that if we do not start from the same instance)
        if not isinstance(leader, AttrLeaf):
            # maybe: this could be a protocol instead, we do not need AttrLeaf exactly
            raise ValueError("Leader {} of {} is not AttrLeaf".format(leader, self))

        self._attrarchy_leader = leader

    def value(self, _instance_only:bool=False) -> ValueType:
        """
        Get current effective value.

        The lookup order is:
        - use instance own value if set
        - use instance leader's value if leader is set and its value is set (will not use leader's default class value)
        - use parent value (i.e. parent's leader's equivalent sub-attr's value) if set
        - use default value from class hierarchy

        :param _instance_only: Do not look for default value from class hierarchy.
        :return:
        """
        logging.debug("%s value evaluation; own: %s", self, self._value)
        value = self._value
        if value is not Unset:
            return value

        logging.debug("leader value %s %s", self._attrarchy_leader, self._leader_instance_value)
        if self._leader_instance_value is not Unset:
            return self._leader_instance_value

        # # Note that according to rules we should not get here without valid parent
        # todo: perhaps if _value_up and _value_down logic is handled by signals
        #  we might even redefine parent as default leader
        value = self._parent_instance_value

        if (value is not Unset) or _instance_only:
            return value

        return self._class_effective_value

    __call__ = value

    def _change_leader_value(self, leader_instance_value:ValueType|Unset) -> None:
        """
        Handle value-changed signal from leader.
        :param leader_instance_value:
        :return:
        """
        assert self._leader_instance_value != leader_instance_value, "Just a guard against unexpected behavior"
        logging.debug("_change_leader_value. %s, %s", self,leader_instance_value)
        self._leader_instance_value = leader_instance_value
        # this will trigger change in instance of effective value if own value is not set
        if self._value is Unset:
            # TODO: unify order of these signal everywhere
            self._changed_instance_signal.emit(leader_instance_value)
            self._changed_signal.emit(leader_instance_value)

    def _change_parent_value(self, parent_instance_value:ValueType|Unset) -> None:
        """
        Handle value-changed signal from parent.
        :param parent_instance_value:
        :return:
        """
        assert self._parent_instance_value != parent_instance_value, "Just a guard against unexpected behavior"
        self._parent_instance_value = parent_instance_value
        # this will trigger change in instance or effective value if own and leader values are not set
        if self._value is Unset and self._leader_instance_value is Unset:
            # TODO: unify order of these signal everywhere
            self._changed_instance_signal.emit(parent_instance_value)
            self._changed_signal.emit(parent_instance_value)

    def _change_class_value(self, class_effective_value:ValueType|Unset) -> None:
        """
        Handle value-changed signal from class.
        :param class_effective_value:
        :return:
        """
        assert self._class_effective_value != class_effective_value, "Just a guard against unexpected behavior"
        self._class_effective_value = class_effective_value
        # this will trigger change in effective value if no other value is set
        if self._value is Unset and self._leader_instance_value is Unset and self._parent_instance_value is Unset:
            self._changed_signal.emit(self._class_effective_value)
            # but not instance value - class effective value is never instance value

    def set(self, value:ValueType) -> None:
        """
        Set own value for this leaf attr.

        Will emit value changed signal if effective value is changed by this change.

        :param value:
        :return:
        """
        if value == self._value:  # own value
            return

        # we possibly change the effective value here
        if self._value is not Unset:
            if value is not Unset:
                # change the actual value
                self._value = value
                self.changed.emit(value)
                self._changed_instance_signal.emit(value)
                return
            else:
                # remove own value, is the new effective different?
                old_value = self._value
                # now we have to try to follow the leader
                if self._attrarchy_leader is not None:
                    self._leader_instance_value = self._attrarchy_leader.value(_instance_only=True)
                    self._attrarchy_leader._changed_instance_signal.connect(self._change_leader_value)

                # todo: possibly start/stop listening to parent value too
                self._value = Unset
                effective_value = self.value()
                if effective_value != old_value:
                    self.changed.emit(effective_value)

                effective_instance_value = self.value(_instance_only=True)
                if effective_instance_value != old_value:
                    self._changed_instance_signal.emit(effective_instance_value)

                return

        # setting own value (self._value is Unset)
        old_instance_value = self.value(_instance_only=True)
        old_effective_value = self.value()
        self._value = value

        # now we do not need to follow the leader
        if self._attrarchy_leader is not None:
            self._attrarchy_leader._changed_instance_signal.disconnect(self._change_leader_value)
        # todo: possibly start/stop listening to parent value too

        if value != old_effective_value:
            self.changed.emit(value)
        if value != old_instance_value:
            self._changed_instance_signal.emit(value)



# noinspection SpellCheckingInspection
class Attr:
    """
    Descriptor for handling attr automation.
    """
    # - init ----------------------------------------------------------------------

    def __init__(self, attr, leader:Self = None):
        super().__init__()

        # the same for Node and Leaf, class hierarchy and instance hierarchy
        self.name = None

        self.infused = is_infused(attr)
        self.leader_to_be = leader  # leader can only be properly set inside infuse(), so store it for later

        if self.infused:  # Node
            # store only a simple version of the attr's class into the descriptor
            if isinstance(attr, type):
                # is a class
                # maybe: this is for the future: attrarchy_class = protocolize(attr) (i.e. we only need a simplified version of the class here)
                # infused attr does not need a default value, because it can use its attrs default values instead
                attrarchy_class = attr
                node = attr()
            else:
                # is an instance
                # maybe: change once protocolize() is implemented
                #  however it might be better to keep the instance the user had supplied
                # attrarchy_class = protocolize(attr.__class__)
                # attr_default = attrarchy_class.fromInstance(attr)
                attrarchy_class = attr.__class__
                node = attr
        else:  # Leaf
            if isinstance(attr, type):
                # is a class
                if leader is None:
                    raise ValueError("A leaf attr needs to have a default value or a leader.")
                attrarchy_class = attr
                logging.debug("create AttrLeaf, leader %s", leader)
                node = AttrLeaf()
            else:
                # is an instance
                attrarchy_class = attr.__class__
                logging.debug("create AttrLeaf, value %s, leader %s", attr, leader)
                node = AttrLeaf(value=attr)

        # both Leaf and Node
        self._node_to_be = node  # class hierarchy
        self.attrarchy_class = attrarchy_class
        self.attrarchy_node_attr = None  # instance hierarchy name

    def __set_name__(self, owner, name: str):
        logging.debug("Attr.__set__name__ parent %s, name %s", owner, name)
        self.name = name
        self.attrarchy_node_attr = "_attrarchyValue_" + name  # be careful here, we create a lot of _attrarchy_something attributes
        self.class_node_attr = "_attrarchyValue_" + name

        self._node_to_be._attrarchy_parent = owner
        self._node_to_be._attr_name = name
        setattr(owner, self.class_node_attr, self._node_to_be)
        self._node_to_be = None

        self._owner = owner


    # - identification helpers -------------------------------------------------

    # def path_to_root(self):
    #     return path_to_root(self.node)  # fixme: self.node does not exist, that is probably a relic

    # def __str__(self):
    #     return self.format_path_to_root()
    #
    # def __repr__(self):
    #     return self.format_path_to_root()

    # def format_path_to_root(self):
    #     path = self.path_to_root()
    #     return ":".join(it.name for it in path[::-1])

    # - descriptor interface ----------------------------------------------------


    def __get__(self, instance, owner):
        """
        Descriptor mandatory method. Get the appropriate node/leaf.

        :param instance:
        :param owner:
        :return:
        """
        # self descriptor instance might live on ancestor class, but owner would be the descendant class if we trigger it via inheritance
        #  so here we have to watch and do not allow using ancestor's node in place of descendant node
        logging.debug("Attr.__get__: instance %s, owner %s", instance, owner)
        # if owner is not self._owner:
        #     raise AssertionError("This is just a test of derived class access detection,")
        if instance is None:
            return getattr(owner, self.class_node_attr)
        # it also means that self.node is possibly not needed (it is not needed to store the default value)
        # BUT it still might have to be used for duplicting the hierrchy from class to instance
        # parhaps the correct way is simply to forbid setting values in class definition at all
        # a redirect all access to class values to the repository, which will keep track of which class to ask
        # but by itself will not store any default valus, those will be still placed on the class definitions?
        else:
            return getattr(instance, self.attrarchy_node_attr)


    def __set__(self, instance, value):
        """
        Prevent setting the descriptor value.
        :param instance:
        :param value:
        :return:
        """
        logging.debug("Attempt to set Attr value directly: self %s, name %s, instance %s, value %s", self, self.name, instance, value)
        raise AttributeError("Attrs must be set via set_{name}(value).", name=self.name, obj=self.__get__(instance, self._owner)._attrarchy_parent)
# do NOT allow __set__




def _check_all_leaders_on_same_hierarchy(node, root=None):
    """
    Check that all leaders are on the same hierarchy.
    :return:
    """
    logging.debug("check_all_leaders_on_same_hierarchy (node %s, root %s)", node, root)
    if root is None:
        root = node

    if is_infused(node):
        for attr in node.attrs():
            _check_all_leaders_on_same_hierarchy(getattr(node, attr), root)

    # root might not have a leader set (it is supposed to be the infused class directly)
    if node is root:
        return

    if node._attrarchy_leader is not None:
        if path_to_root(node._attrarchy_leader)[-1] is not root:
            raise ValueError(
                "Leader {} is not on the same hierarchy as node {}".format(path_to_root(node._attrarchy_leader),
                                                                           path_to_root(node)))


def _check_all_leaders_match_follower(node):
    """
    Check that leaders and followers have compatible data types. WIP
    :param node:
    :return:
    """
    if hasattr(node, "_attrarchy_leader") and node._attrarchy_leader is not None:
        leader = node._attrarchy_leader
        if is_infused(node):
            if not is_infused(leader):
                raise TypeError("Leader {} of infused class {} is not infused.".format(leader, node))

            for node_attr in node.attrs():
                if node_attr not in leader.attrs():
                    raise TypeError(
                        "Leader {} does not provide required attr {} for {}".format(leader, node_attr, node))
        else:
            # todo: not sure how to check validity of datatype match for leafs
            ...

    if is_infused(node):
        for attr in node.attrs():
            _check_all_leaders_match_follower(getattr(node, attr))
    pass


def _copy_subnode(descriptor, class_hierarchy_subnode, parent, node_map, leader_map, attr_name, values):
    """
    Helper function for building attrs hierarchy.
    :param descriptor:
    :param class_hierarchy_subnode:
    :param parent:
    :param node_map:
    :param leader_map:
    :param attr_name:
    :param values:
    :return:
    """
    assert(isinstance(parent, AttrLeaf) or is_infused(parent))
    if descriptor.infused:
        # todo: it is questionable if we can pass parent and name arguments to infused class init
        #  perhaps we should keep additional arguments as low as possible
        value = values.pop(attr_name, {})
        instance_hierarch_subnode = descriptor.attrarchy_class(_construction=(attr_name, parent,
                                                               node_map, class_hierarchy_subnode, leader_map),
                                                           **value)
        setattr(parent, descriptor.attrarchy_node_attr, instance_hierarch_subnode)
        node_map[class_hierarchy_subnode] = instance_hierarch_subnode
        if class_hierarchy_subnode._attrarchy_leader is not None:
            leader_map[instance_hierarch_subnode] = class_hierarchy_subnode._attrarchy_leader

        return instance_hierarch_subnode

    # logging.debug("hierarchy duplication %s, class node %s", self, class_hierarchy_node)
    if isinstance(class_hierarchy_subnode, AttrLeaf):
        logging.debug("create AttrLeaf parent %s, class_leaf %s, name %s, class_leaf.leader %s",
                      parent, class_hierarchy_subnode,
                      attr_name, class_hierarchy_subnode._attrarchy_leader)
        # todo: we do not have concerns about extra init arguments for AttrLeaf, but perhaps its handling
        #  should be the same as for infused class
        """
        we might even do something like
        @infuse
        class AttrLeaf:
            def value(self):
                ...
            ...

        to ensure this.
        We would not even need to keep two branches here.
        """
        value = values.pop(attr_name, Unset)
        leaf = AttrLeaf(parent=parent, class_leaf=class_hierarchy_subnode, name=attr_name, value=value)
        setattr(parent, descriptor.attrarchy_node_attr, leaf)
        node_map[class_hierarchy_subnode] = leaf
        if class_hierarchy_subnode._attrarchy_leader is not None:
            leader_map[leaf] = class_hierarchy_subnode._attrarchy_leader
        return leaf

    raise RuntimeError("An attr is neither infused (node) nor a leaf.")



