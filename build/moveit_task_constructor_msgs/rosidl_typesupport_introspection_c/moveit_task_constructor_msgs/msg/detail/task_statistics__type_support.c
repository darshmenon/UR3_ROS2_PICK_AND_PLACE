// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from moveit_task_constructor_msgs:msg/TaskStatistics.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "moveit_task_constructor_msgs/msg/detail/task_statistics__rosidl_typesupport_introspection_c.h"
#include "moveit_task_constructor_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "moveit_task_constructor_msgs/msg/detail/task_statistics__functions.h"
#include "moveit_task_constructor_msgs/msg/detail/task_statistics__struct.h"


// Include directives for member types
// Member `task_id`
#include "rosidl_runtime_c/string_functions.h"
// Member `stages`
#include "moveit_task_constructor_msgs/msg/stage_statistics.h"
// Member `stages`
#include "moveit_task_constructor_msgs/msg/detail/stage_statistics__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__TaskStatistics_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  moveit_task_constructor_msgs__msg__TaskStatistics__init(message_memory);
}

void moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__TaskStatistics_fini_function(void * message_memory)
{
  moveit_task_constructor_msgs__msg__TaskStatistics__fini(message_memory);
}

size_t moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__size_function__TaskStatistics__stages(
  const void * untyped_member)
{
  const moveit_task_constructor_msgs__msg__StageStatistics__Sequence * member =
    (const moveit_task_constructor_msgs__msg__StageStatistics__Sequence *)(untyped_member);
  return member->size;
}

const void * moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__get_const_function__TaskStatistics__stages(
  const void * untyped_member, size_t index)
{
  const moveit_task_constructor_msgs__msg__StageStatistics__Sequence * member =
    (const moveit_task_constructor_msgs__msg__StageStatistics__Sequence *)(untyped_member);
  return &member->data[index];
}

void * moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__get_function__TaskStatistics__stages(
  void * untyped_member, size_t index)
{
  moveit_task_constructor_msgs__msg__StageStatistics__Sequence * member =
    (moveit_task_constructor_msgs__msg__StageStatistics__Sequence *)(untyped_member);
  return &member->data[index];
}

void moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__fetch_function__TaskStatistics__stages(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const moveit_task_constructor_msgs__msg__StageStatistics * item =
    ((const moveit_task_constructor_msgs__msg__StageStatistics *)
    moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__get_const_function__TaskStatistics__stages(untyped_member, index));
  moveit_task_constructor_msgs__msg__StageStatistics * value =
    (moveit_task_constructor_msgs__msg__StageStatistics *)(untyped_value);
  *value = *item;
}

void moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__assign_function__TaskStatistics__stages(
  void * untyped_member, size_t index, const void * untyped_value)
{
  moveit_task_constructor_msgs__msg__StageStatistics * item =
    ((moveit_task_constructor_msgs__msg__StageStatistics *)
    moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__get_function__TaskStatistics__stages(untyped_member, index));
  const moveit_task_constructor_msgs__msg__StageStatistics * value =
    (const moveit_task_constructor_msgs__msg__StageStatistics *)(untyped_value);
  *item = *value;
}

bool moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__resize_function__TaskStatistics__stages(
  void * untyped_member, size_t size)
{
  moveit_task_constructor_msgs__msg__StageStatistics__Sequence * member =
    (moveit_task_constructor_msgs__msg__StageStatistics__Sequence *)(untyped_member);
  moveit_task_constructor_msgs__msg__StageStatistics__Sequence__fini(member);
  return moveit_task_constructor_msgs__msg__StageStatistics__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__TaskStatistics_message_member_array[2] = {
  {
    "task_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__TaskStatistics, task_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "stages",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__TaskStatistics, stages),  // bytes offset in struct
    NULL,  // default value
    moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__size_function__TaskStatistics__stages,  // size() function pointer
    moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__get_const_function__TaskStatistics__stages,  // get_const(index) function pointer
    moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__get_function__TaskStatistics__stages,  // get(index) function pointer
    moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__fetch_function__TaskStatistics__stages,  // fetch(index, &value) function pointer
    moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__assign_function__TaskStatistics__stages,  // assign(index, value) function pointer
    moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__resize_function__TaskStatistics__stages  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__TaskStatistics_message_members = {
  "moveit_task_constructor_msgs__msg",  // message namespace
  "TaskStatistics",  // message name
  2,  // number of fields
  sizeof(moveit_task_constructor_msgs__msg__TaskStatistics),
  moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__TaskStatistics_message_member_array,  // message members
  moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__TaskStatistics_init_function,  // function to initialize message memory (memory has to be allocated)
  moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__TaskStatistics_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__TaskStatistics_message_type_support_handle = {
  0,
  &moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__TaskStatistics_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_moveit_task_constructor_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, msg, TaskStatistics)() {
  moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__TaskStatistics_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, msg, StageStatistics)();
  if (!moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__TaskStatistics_message_type_support_handle.typesupport_identifier) {
    moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__TaskStatistics_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &moveit_task_constructor_msgs__msg__TaskStatistics__rosidl_typesupport_introspection_c__TaskStatistics_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
