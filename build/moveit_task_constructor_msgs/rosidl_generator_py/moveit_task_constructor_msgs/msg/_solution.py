# generated from rosidl_generator_py/resource/_idl.py.em
# with input from moveit_task_constructor_msgs:msg/Solution.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_Solution(type):
    """Metaclass of message 'Solution'."""

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
                'moveit_task_constructor_msgs.msg.Solution')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__solution
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__solution
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__solution
            cls._TYPE_SUPPORT = module.type_support_msg__msg__solution
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__solution

            from moveit_msgs.msg import PlanningScene
            if PlanningScene.__class__._TYPE_SUPPORT is None:
                PlanningScene.__class__.__import_type_support__()

            from moveit_task_constructor_msgs.msg import SubSolution
            if SubSolution.__class__._TYPE_SUPPORT is None:
                SubSolution.__class__.__import_type_support__()

            from moveit_task_constructor_msgs.msg import SubTrajectory
            if SubTrajectory.__class__._TYPE_SUPPORT is None:
                SubTrajectory.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class Solution(metaclass=Metaclass_Solution):
    """Message class 'Solution'."""

    __slots__ = [
        '_task_id',
        '_start_scene',
        '_sub_solution',
        '_sub_trajectory',
    ]

    _fields_and_field_types = {
        'task_id': 'string',
        'start_scene': 'moveit_msgs/PlanningScene',
        'sub_solution': 'sequence<moveit_task_constructor_msgs/SubSolution>',
        'sub_trajectory': 'sequence<moveit_task_constructor_msgs/SubTrajectory>',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.UnboundedString(),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['moveit_msgs', 'msg'], 'PlanningScene'),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.NamespacedType(['moveit_task_constructor_msgs', 'msg'], 'SubSolution')),  # noqa: E501
        rosidl_parser.definition.UnboundedSequence(rosidl_parser.definition.NamespacedType(['moveit_task_constructor_msgs', 'msg'], 'SubTrajectory')),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.task_id = kwargs.get('task_id', str())
        from moveit_msgs.msg import PlanningScene
        self.start_scene = kwargs.get('start_scene', PlanningScene())
        self.sub_solution = kwargs.get('sub_solution', [])
        self.sub_trajectory = kwargs.get('sub_trajectory', [])

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
        if self.task_id != other.task_id:
            return False
        if self.start_scene != other.start_scene:
            return False
        if self.sub_solution != other.sub_solution:
            return False
        if self.sub_trajectory != other.sub_trajectory:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def task_id(self):
        """Message field 'task_id'."""
        return self._task_id

    @task_id.setter
    def task_id(self, value):
        if __debug__:
            assert \
                isinstance(value, str), \
                "The 'task_id' field must be of type 'str'"
        self._task_id = value

    @builtins.property
    def start_scene(self):
        """Message field 'start_scene'."""
        return self._start_scene

    @start_scene.setter
    def start_scene(self, value):
        if __debug__:
            from moveit_msgs.msg import PlanningScene
            assert \
                isinstance(value, PlanningScene), \
                "The 'start_scene' field must be a sub message of type 'PlanningScene'"
        self._start_scene = value

    @builtins.property
    def sub_solution(self):
        """Message field 'sub_solution'."""
        return self._sub_solution

    @sub_solution.setter
    def sub_solution(self, value):
        if __debug__:
            from moveit_task_constructor_msgs.msg import SubSolution
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
                 all(isinstance(v, SubSolution) for v in value) and
                 True), \
                "The 'sub_solution' field must be a set or sequence and each value of type 'SubSolution'"
        self._sub_solution = value

    @builtins.property
    def sub_trajectory(self):
        """Message field 'sub_trajectory'."""
        return self._sub_trajectory

    @sub_trajectory.setter
    def sub_trajectory(self, value):
        if __debug__:
            from moveit_task_constructor_msgs.msg import SubTrajectory
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
                 all(isinstance(v, SubTrajectory) for v in value) and
                 True), \
                "The 'sub_trajectory' field must be a set or sequence and each value of type 'SubTrajectory'"
        self._sub_trajectory = value
