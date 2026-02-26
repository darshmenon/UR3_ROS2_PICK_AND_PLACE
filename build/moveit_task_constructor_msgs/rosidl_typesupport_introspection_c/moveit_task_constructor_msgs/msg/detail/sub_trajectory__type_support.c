// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from moveit_task_constructor_msgs:msg/SubTrajectory.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "moveit_task_constructor_msgs/msg/detail/sub_trajectory__rosidl_typesupport_introspection_c.h"
#include "moveit_task_constructor_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "moveit_task_constructor_msgs/msg/detail/sub_trajectory__functions.h"
#include "moveit_task_constructor_msgs/msg/detail/sub_trajectory__struct.h"


// Include directives for member types
// Member `info`
#include "moveit_task_constructor_msgs/msg/solution_info.h"
// Member `info`
#include "moveit_task_constructor_msgs/msg/detail/solution_info__rosidl_typesupport_introspection_c.h"
// Member `execution_info`
#include "moveit_task_constructor_msgs/msg/trajectory_execution_info.h"
// Member `execution_info`
#include "moveit_task_constructor_msgs/msg/detail/trajectory_execution_info__rosidl_typesupport_introspection_c.h"
// Member `trajectory`
#include "moveit_msgs/msg/robot_trajectory.h"
// Member `trajectory`
#include "moveit_msgs/msg/detail/robot_trajectory__rosidl_typesupport_introspection_c.h"
// Member `scene_diff`
#include "moveit_msgs/msg/planning_scene.h"
// Member `scene_diff`
#include "moveit_msgs/msg/detail/planning_scene__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  moveit_task_constructor_msgs__msg__SubTrajectory__init(message_memory);
}

void moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_fini_function(void * message_memory)
{
  moveit_task_constructor_msgs__msg__SubTrajectory__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_message_member_array[4] = {
  {
    "info",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__SubTrajectory, info),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "execution_info",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__SubTrajectory, execution_info),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "trajectory",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__SubTrajectory, trajectory),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "scene_diff",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__SubTrajectory, scene_diff),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_message_members = {
  "moveit_task_constructor_msgs__msg",  // message namespace
  "SubTrajectory",  // message name
  4,  // number of fields
  sizeof(moveit_task_constructor_msgs__msg__SubTrajectory),
  moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_message_member_array,  // message members
  moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_init_function,  // function to initialize message memory (memory has to be allocated)
  moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_message_type_support_handle = {
  0,
  &moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_moveit_task_constructor_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, msg, SubTrajectory)() {
  moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, msg, SolutionInfo)();
  moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, msg, TrajectoryExecutionInfo)();
  moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_message_member_array[2].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_msgs, msg, RobotTrajectory)();
  moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_message_member_array[3].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_msgs, msg, PlanningScene)();
  if (!moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_message_type_support_handle.typesupport_identifier) {
    moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &moveit_task_constructor_msgs__msg__SubTrajectory__rosidl_typesupport_introspection_c__SubTrajectory_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
