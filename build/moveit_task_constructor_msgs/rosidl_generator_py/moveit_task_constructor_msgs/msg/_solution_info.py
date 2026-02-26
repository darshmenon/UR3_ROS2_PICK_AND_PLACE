# generated from rosidl_generator_py/resource/_idl.py.em
# with input from moveit_task_constructor_msgs:msg/SolutionInfo.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_SolutionInfo(type):
    """Metaclass of message 'SolutionInfo'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('moveit_task_constructor_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'moveit_task_constructor_msgs.msg.SolutionInfo')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__solution_info
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__solution_info
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__solution_info
            cls._TYPE_SUPPORT = module.type_support_msg__msg__solution_info
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__solution_info

            from visualization_msgs.msg import Marker
            if Marker.__class__._TYPE_SUPPORT is None:
                Marker.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class SolutionInfo(metaclass=Metaclass_SolutionInfo):
    """Message class 'SolutionInfo'."""

    __slots__ = [
        '_id',
        '_cost',
        '_comment',
        '_stage_id',
        '_planner_id',
        '_markers',
    ]

    _fields_and_field_types = {
        'id': 'uint32',
        'cost': 'float',
        'comment': 'string',
        'stage_id': 'uint32',
        'planner_id': 'string',
        'markers': 'sequence<visualization_msgs/Marker>',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('uint32'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.BasicType('uint32'),  # noqa: E501
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.NamespacedType(['visualization_msgs', 'msg'], 'Marker')),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.id = kwargs.get('id', int())
        self.cost = kwargs.get('cost', float())
        self.comment = kwargs.get('comment', str())
        self.stage_id = kwargs.get('stage_id', int())
        self.planner_id = kwargs.get('planner_id', str())
        self.markers = kwargs.get('markers', [])

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.id != other.id:
            return False
        if self.cost != other.cost:
            return False
        if self.comment != other.comment:
            return False
        if self.stage_id != other.stage_id:
            return False
        if self.planner_id != other.planner_id:
            return False
        if self.markers != other.markers:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property  # noqa: A003
    def id(self):  # noqa: A003
        """Message field 'id'."""
        return self._id

    @id.setter  # noqa: A003
    def id(self, value):  # noqa: A003
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'id' field must be of type 'int'"
            assert value >= 0 and value < 4294967296, \
                "The 'id' field must be an unsigned integer in [0, 4294967295]"
        self._id = value

    @builtins.property
    def cost(self):
        """Message field 'cost'."""
        return self._cost

    @cost.setter
    def cost(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'cost' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'cost' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._cost = value

    @builtins.property
    def comment(self):
        """Message field 'comment'."""
        return self._comment

    @comment.setter
    def comment(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'comment' field must be of type 'str'"
        self._comment = value

    @builtins.property
    def stage_id(self):
        """Message field 'stage_id'."""
        return self._stage_id

    @stage_id.setter
    def stage_id(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'stage_id' field must be of type 'int'"
            assert value >= 0 and value < 4294967296, \
                "The 'stage_id' field must be an unsigned integer in [0, 4294967295]"
        self._stage_id = value

    @builtins.property
    def planner_id(self):
        """Message field 'planner_id'."""
        return self._planner_id

    @planner_id.setter
    def planner_id(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'planner_id' field must be of type 'str'"
        self._planner_id = value

    @builtins.property
    def markers(self):
        """Message field 'markers'."""
        return self._markers

    @markers.setter
    def markers(self, value):
        if __debug__:
            from visualization_msgs.msg import Marker
            from collections.abc import Sequence
            from collections.abc import Set
            from collections import UserList
            from collections import UserString
            assert \
                ((isinstance(value, Sequence) or
                  isinstance(value, Set) or
                  isinstance(value, UserList)) and
                 not isinstance(value, str) and
                 not isinstance(value, UserString) and
                 all(isinstance(v, Marker) for v in value) and
                 True), \
                "The 'markers' field must be a set or sequence and each value of type 'Marker'"
        self._markers = value
