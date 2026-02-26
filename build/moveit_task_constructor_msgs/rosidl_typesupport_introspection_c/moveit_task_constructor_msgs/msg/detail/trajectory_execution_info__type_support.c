// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from moveit_task_constructor_msgs:msg/TrajectoryExecutionInfo.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "moveit_task_constructor_msgs/msg/detail/trajectory_execution_info__rosidl_typesupport_introspection_c.h"
#include "moveit_task_constructor_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "moveit_task_constructor_msgs/msg/detail/trajectory_execution_info__functions.h"
#include "moveit_task_constructor_msgs/msg/detail/trajectory_execution_info__struct.h"


// Include directives for member types
// Member `controller_names`
#include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__TrajectoryExecutionInfo_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__init(message_memory);
}

void moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__TrajectoryExecutionInfo_fini_function(void * message_memory)
{
  moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__fini(message_memory);
}

size_t moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__size_function__TrajectoryExecutionInfo__controller_names(
  const void * untyped_member)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return member->size;
}

const void * moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__get_const_function__TrajectoryExecutionInfo__controller_names(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void * moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__get_function__TrajectoryExecutionInfo__controller_names(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__fetch_function__TrajectoryExecutionInfo__controller_names(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const rosidl_runtime_c__String * item =
    ((const rosidl_runtime_c__String *)
    moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__get_const_function__TrajectoryExecutionInfo__controller_names(untyped_member, index));
  rosidl_runtime_c__String * value =
    (rosidl_runtime_c__String *)(untyped_value);
  *value = *item;
}

void moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__assign_function__TrajectoryExecutionInfo__controller_names(
  void * untyped_member, size_t index, const void * untyped_value)
{
  rosidl_runtime_c__String * item =
    ((rosidl_runtime_c__String *)
    moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__get_function__TrajectoryExecutionInfo__controller_names(untyped_member, index));
  const rosidl_runtime_c__String * value =
    (const rosidl_runtime_c__String *)(untyped_value);
  *item = *value;
}

bool moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__resize_function__TrajectoryExecutionInfo__controller_names(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  rosidl_runtime_c__String__Sequence__fini(member);
  return rosidl_runtime_c__String__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__TrajectoryExecutionInfo_message_member_array[1] = {
  {
    "controller_names",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo, controller_names),  // bytes offset in struct
    NULL,  // default value
    moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__size_function__TrajectoryExecutionInfo__controller_names,  // size() function pointer
    moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__get_const_function__TrajectoryExecutionInfo__controller_names,  // get_const(index) function pointer
    moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__get_function__TrajectoryExecutionInfo__controller_names,  // get(index) function pointer
    moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__fetch_function__TrajectoryExecutionInfo__controller_names,  // fetch(index, &value) function pointer
    moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__assign_function__TrajectoryExecutionInfo__controller_names,  // assign(index, value) function pointer
    moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__resize_function__TrajectoryExecutionInfo__controller_names  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__TrajectoryExecutionInfo_message_members = {
  "moveit_task_constructor_msgs__msg",  // message namespace
  "TrajectoryExecutionInfo",  // message name
  1,  // number of fields
  sizeof(moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo),
  moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__TrajectoryExecutionInfo_message_member_array,  // message members
  moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__TrajectoryExecutionInfo_init_function,  // function to initialize message memory (memory has to be allocated)
  moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__TrajectoryExecutionInfo_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__TrajectoryExecutionInfo_message_type_support_handle = {
  0,
  &moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__TrajectoryExecutionInfo_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_moveit_task_constructor_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, msg, TrajectoryExecutionInfo)() {
  if (!moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__TrajectoryExecutionInfo_message_type_support_handle.typesupport_identifier) {
    moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__TrajectoryExecutionInfo_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__rosidl_typesupport_introspection_c__TrajectoryExecutionInfo_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
