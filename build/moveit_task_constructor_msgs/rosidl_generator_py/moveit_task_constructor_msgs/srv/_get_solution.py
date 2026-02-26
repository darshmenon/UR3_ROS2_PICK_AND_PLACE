# generated from rosidl_generator_py/resource/_idl.py.em
# with input from moveit_task_constructor_msgs:srv/GetSolution.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_GetSolution_Request(type):
    """Metaclass of message 'GetSolution_Request'."""

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
                'moveit_task_constructor_msgs.srv.GetSolution_Request')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__srv__get_solution__request
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__srv__get_solution__request
            cls._CONVERT_TO_PY = module.convert_to_py_msg__srv__get_solution__request
            cls._TYPE_SUPPORT = module.type_support_msg__srv__get_solution__request
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__srv__get_solution__request

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class GetSolution_Request(metaclass=Metaclass_GetSolution_Request):
    """Message class 'GetSolution_Request'."""

    __slots__ = [
        '_solution_id',
    ]

    _fields_and_field_types = {
        'solution_id': 'uint32',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('uint32'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.solution_id = kwargs.get('solution_id', int())

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
        if self.solution_id != other.solution_id:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def solution_id(self):
        """Message field 'solution_id'."""
        return self._solution_id

    @solution_id.setter
    def solution_id(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'solution_id' field must be of type 'int'"
            assert value >= 0 and value < 4294967296, \
                "The 'solution_id' field must be an unsigned integer in [0, 4294967295]"
        self._solution_id = value


# Import statements for member types

# already imported above
# import builtins

# already imported above
# import rosidl_parser.definition


class Metaclass_GetSolution_Response(type):
    """Metaclass of message 'GetSolution_Response'."""

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
                'moveit_task_constructor_msgs.srv.GetSolution_Response')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__srv__get_solution__response
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__srv__get_solution__response
            cls._CONVERT_TO_PY = module.convert_to_py_msg__srv__get_solution__response
            cls._TYPE_SUPPORT = module.type_support_msg__srv__get_solution__response
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__srv__get_solution__response

            from moveit_task_constructor_msgs.msg import Solution
            if Solution.__class__._TYPE_SUPPORT is None:
                Solution.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class GetSolution_Response(metaclass=Metaclass_GetSolution_Response):
    """Message class 'GetSolution_Response'."""

    __slots__ = [
        '_solution',
    ]

    _fields_and_field_types = {
        'solution': 'moveit_task_constructor_msgs/Solution',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.NamespacedType(['moveit_task_constructor_msgs', 'msg'], 'Solution'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        from moveit_task_constructor_msgs.msg import Solution
        self.solution = kwargs.get('solution', Solution())

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
        if self.solution != other.solution:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def solution(self):
        """Message field 'solution'."""
        return self._solution

    @solution.setter
    def solution(self, value):
        if __debug__:
            from moveit_task_constructor_msgs.msg import Solution
            assert \
                isinstance(value, Solution), \
                "The 'solution' field must be a sub message of type 'Solution'"
        self._solution = value


class Metaclass_GetSolution(type):
    """Metaclass of service 'GetSolution'."""

    _TYPE_SUPPORT = None

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('moveit_task_constructor_msgs')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'moveit_task_constructor_msgs.srv.GetSolution')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._TYPE_SUPPORT = module.type_support_srv__srv__get_solution

            from moveit_task_constructor_msgs.srv import _get_solution
            if _get_solution.Metaclass_GetSolution_Request._TYPE_SUPPORT is None:
                _get_solution.Metaclass_GetSolution_Request.__import_type_support__()
            if _get_solution.Metaclass_GetSolution_Response._TYPE_SUPPORT is None:
                _get_solution.Metaclass_GetSolution_Response.__import_type_support__()


class GetSolution(metaclass=Metaclass_GetSolution):
    from moveit_task_constructor_msgs.srv._get_solution import GetSolution_Request as Request
    from moveit_task_constructor_msgs.srv._get_solution import GetSolution_Response as Response

    def __init__(self):
        raise NotImplementedError('Service classes can not be instantiated')
