# generated from rosidl_generator_py/resource/_idl.py.em
# with input from moveit_task_constructor_msgs:msg/SubTrajectory.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_SubTrajectory(type):
    """Metaclass of message 'SubTrajectory'."""

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
                'moveit_task_constructor_msgs.msg.SubTrajectory')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__sub_trajectory
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__sub_trajectory
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__sub_trajectory
            cls._TYPE_SUPPORT = module.type_support_msg__msg__sub_trajectory
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__sub_trajectory

            from moveit_msgs.msg import PlanningScene
            if PlanningScene.__class__._TYPE_SUPPORT is None:
                PlanningScene.__class__.__import_type_support__()

            from moveit_msgs.msg import RobotTrajectory
            if RobotTrajectory.__class__._TYPE_SUPPORT is None:
                RobotTrajectory.__class__.__import_type_support__()

            from moveit_task_constructor_msgs.msg import SolutionInfo
            if SolutionInfo.__class__._TYPE_SUPPORT is None:
                SolutionInfo.__class__.__import_type_support__()

            from moveit_task_constructor_msgs.msg import TrajectoryExecutionInfo
            if TrajectoryExecutionInfo.__class__._TYPE_SUPPORT is None:
                TrajectoryExecutionInfo.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class SubTrajectory(metaclass=Metaclass_SubTrajectory):
    """Message class 'SubTrajectory'."""

    __slots__ = [
        '_info',
        '_execution_info',
        '_trajectory',
        '_scene_diff',
    ]

    _fields_and_field_types = {
        'info': 'moveit_task_constructor_msgs/SolutionInfo',
        'execution_info': 'moveit_task_constructor_msgs/TrajectoryExecutionInfo',
        'trajectory': 'moveit_msgs/RobotTrajectory',
        'scene_diff': 'moveit_msgs/PlanningScene',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.NamespacedType(['moveit_task_constructor_msgs', 'msg'], 'SolutionInfo'),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['moveit_task_constructor_msgs', 'msg'], 'TrajectoryExecutionInfo'),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['moveit_msgs', 'msg'], 'RobotTrajectory'),  # noqa: E501
        rosidl_parser.definition.NamespacedType(['moveit_msgs', 'msg'], 'PlanningScene'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        from moveit_task_constructor_msgs.msg import SolutionInfo
        self.info = kwargs.get('info', SolutionInfo())
        from moveit_task_constructor_msgs.msg import TrajectoryExecutionInfo
        self.execution_info = kwargs.get('execution_info', TrajectoryExecutionInfo())
        from moveit_msgs.msg import RobotTrajectory
        self.trajectory = kwargs.get('trajectory', RobotTrajectory())
        from moveit_msgs.msg import PlanningScene
        self.scene_diff = kwargs.get('scene_diff', PlanningScene())

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
        if self.execution_info != other.execution_info:
            return False
        if self.trajectory != other.trajectory:
            return False
        if self.scene_diff != other.scene_diff:
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
    def execution_info(self):
        """Message field 'execution_info'."""
        return self._execution_info

    @execution_info.setter
    def execution_info(self, value):
        if __debug__:
            from moveit_task_constructor_msgs.msg import TrajectoryExecutionInfo
            assert \
                isinstance(value, TrajectoryExecutionInfo), \
                "The 'execution_info' field must be a sub message of type 'TrajectoryExecutionInfo'"
        self._execution_info = value

    @builtins.property
    def trajectory(self):
        """Message field 'trajectory'."""
        return self._trajectory

    @trajectory.setter
    def trajectory(self, value):
        if __debug__:
            from moveit_msgs.msg import RobotTrajectory
            assert \
                isinstance(value, RobotTrajectory), \
                "The 'trajectory' field must be a sub message of type 'RobotTrajectory'"
        self._trajectory = value

    @builtins.property
    def scene_diff(self):
        """Message field 'scene_diff'."""
        return self._scene_diff

    @scene_diff.setter
    def scene_diff(self, value):
        if __debug__:
            from moveit_msgs.msg import PlanningScene
            assert \
                isinstance(value, PlanningScene), \
                "The 'scene_diff' field must be a sub message of type 'PlanningScene'"
        self._scene_diff = value
