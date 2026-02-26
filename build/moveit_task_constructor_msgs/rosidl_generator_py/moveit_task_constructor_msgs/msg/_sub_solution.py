# generated from rosidl_generator_py/resource/_idl.py.em
# with input from moveit_task_constructor_msgs:msg/SubSolution.idl
# generated code does not contain a copyright notice


# Import statements for member types

# Member 'sub_solution_id'
import array  # noqa: E402, I100

import builtins  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_SubSolution(type):
    """Metaclass of message 'SubSolution'."""

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
                'moveit_task_constructor_msgs.msg.SubSolution')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__sub_solution
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__sub_solution
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__sub_solution
            cls._TYPE_SUPPORT = module.type_support_msg__msg__sub_solution
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__sub_solution

            from moveit_task_constructor_msgs.msg import SolutionInfo
            if SolutionInfo.__class__._TYPE_SUPPORT is None:
                SolutionInfo.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class SubSolution(metaclass=Metaclass_SubSolution):
    """Message class 'SubSolution'."""

    __slots__ = [
        '_info',
        '_sub_solution_id',
    ]

    _fields_and_field_types = {
        'info': 'moveit_task_constructor_msgs/SolutionInfo',
        'sub_solution_id': 'sequence<uint32>',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.NamespacedType(['moveit_task_constructor_msgs', 'msg'], 'SolutionInfo'),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.BasicType('uint32')),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        from moveit_task_constructor_msgs.msg import SolutionInfo
        self.info = kwargs.get('info', SolutionInfo())
        self.sub_solution_id = array.array('I', kwargs.get('sub_solution_id', []))

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
        if self.info != other.info:
            return False
        if self.sub_solution_id != other.sub_solution_id:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def info(self):
        """Message field 'info'."""
        return self._info

    @info.setter
    def info(self, value):
        if __debug__:
            from moveit_task_constructor_msgs.msg import SolutionInfo
            assert \
                isinstance(value, SolutionInfo), \
                "The 'info' field must be a sub message of type 'SolutionInfo'"
        self._info = value

    @builtins.property
    def sub_solution_id(self):
        """Message field 'sub_solution_id'."""
        return self._sub_solution_id

    @sub_solution_id.setter
    def sub_solution_id(self, value):
        if isinstance(value, array.array):
            assert value.typecode == 'I', \
                "The 'sub_solution_id' array.array() must have the type code of 'I'"
            self._sub_solution_id = value
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
                "The 'sub_solution_id' field must be a set or sequence and each value of type 'int' and each unsigned integer in [0, 4294967295]"
        self._sub_solution_id = array.array('I', value)
