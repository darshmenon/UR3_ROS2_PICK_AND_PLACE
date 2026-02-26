# generated from rosidl_generator_py/resource/_idl.py.em
# with input from moveit_task_constructor_msgs:msg/StageStatistics.idl
# generated code does not contain a copyright notice


# Import statements for member types

# Member 'solved'
# Member 'failed'
import array  # noqa: E402, I100

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_StageStatistics(type):
    """Metaclass of message 'StageStatistics'."""

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
                'moveit_task_constructor_msgs.msg.StageStatistics')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__stage_statistics
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__stage_statistics
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__stage_statistics
            cls._TYPE_SUPPORT = module.type_support_msg__msg__stage_statistics
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__stage_statistics

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class StageStatistics(metaclass=Metaclass_StageStatistics):
    """Message class 'StageStatistics'."""

    __slots__ = [
        '_id',
        '_solved',
        '_failed',
        '_num_failed',
        '_total_compute_time',
    ]

    _fields_and_field_types = {
        'id': 'uint32',
        'solved': 'sequence<uint32>',
        'failed': 'sequence<uint32>',
        'num_failed': 'uint32',
        'total_compute_time': 'double',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('uint32'),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.BasicType('uint32')),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.BasicType('uint32')),  # noqa: E501
        rosidl_parser.definition.BasicType('uint32'),  # noqa: E501
        rosidl_parser.definition.BasicType('double'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.id = kwargs.get('id', int())
        self.solved = array.array('I', kwargs.get('solved', []))
        self.failed = array.array('I', kwargs.get('failed', []))
        self.num_failed = kwargs.get('num_failed', int())
        self.total_compute_time = kwargs.get('total_compute_time', float())

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
        if self.solved != other.solved:
            return False
        if self.failed != other.failed:
            return False
        if self.num_failed != other.num_failed:
            return False
        if self.total_compute_time != other.total_compute_time:
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
    def solved(self):
        """Message field 'solved'."""
        return self._solved

    @solved.setter
    def solved(self, value):
        if isinstance(value, array.array):
            assert value.typecode == 'I', \
                "The 'solved' array.array() must have the type code of 'I'"
            self._solved = value
            return
        if __debug__:
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
                 all(isinstance(v, int) for v in value) and
                 all(val >= 0 and val < 4294967296 for val in value)), \
                "The 'solved' field must be a set or sequence and each value of type 'int' and each unsigned integer in [0, 4294967295]"
        self._solved = array.array('I', value)

    @builtins.property
    def failed(self):
        """Message field 'failed'."""
        return self._failed

    @failed.setter
    def failed(self, value):
        if isinstance(value, array.array):
            assert value.typecode == 'I', \
                "The 'failed' array.array() must have the type code of 'I'"
            self._failed = value
            return
        if __debug__:
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
                 all(isinstance(v, int) for v in value) and
                 all(val >= 0 and val < 4294967296 for val in value)), \
                "The 'failed' field must be a set or sequence and each value of type 'int' and each unsigned integer in [0, 4294967295]"
        self._failed = array.array('I', value)

    @builtins.property
    def num_failed(self):
        """Message field 'num_failed'."""
        return self._num_failed

    @num_failed.setter
    def num_failed(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'num_failed' field must be of type 'int'"
            assert value >= 0 and value < 4294967296, \
                "The 'num_failed' field must be an unsigned integer in [0, 4294967295]"
        self._num_failed = value

    @builtins.property
    def total_compute_time(self):
        """Message field 'total_compute_time'."""
        return self._total_compute_time

    @total_compute_time.setter
    def total_compute_time(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'total_compute_time' field must be of type 'float'"
            assert not (value < -1.7976931348623157e+308 or value > 1.7976931348623157e+308) or math.isinf(value), \
                "The 'total_compute_time' field must be a double in [-1.7976931348623157e+308, 1.7976931348623157e+308]"
        self._total_compute_time = value
