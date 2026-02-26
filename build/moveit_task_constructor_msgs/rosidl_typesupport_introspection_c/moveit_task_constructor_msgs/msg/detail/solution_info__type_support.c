// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from moveit_task_constructor_msgs:msg/SolutionInfo.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "moveit_task_constructor_msgs/msg/detail/solution_info__rosidl_typesupport_introspection_c.h"
#include "moveit_task_constructor_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "moveit_task_constructor_msgs/msg/detail/solution_info__functions.h"
#include "moveit_task_constructor_msgs/msg/detail/solution_info__struct.h"


// Include directives for member types
// Member `comment`
// Member `planner_id`
#include "rosidl_runtime_c/string_functions.h"
// Member `markers`
#include "visualization_msgs/msg/marker.h"
// Member `markers`
#include "visualization_msgs/msg/detail/marker__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__SolutionInfo_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  moveit_task_constructor_msgs__msg__SolutionInfo__init(message_memory);
}

void moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__SolutionInfo_fini_function(void * message_memory)
{
  moveit_task_constructor_msgs__msg__SolutionInfo__fini(message_memory);
}

size_t moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__size_function__SolutionInfo__markers(
  const void * untyped_member)
{
  const visualization_msgs__msg__Marker__Sequence * member =
    (const visualization_msgs__msg__Marker__Sequence *)(untyped_member);
  return member->size;
}

const void * moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__get_const_function__SolutionInfo__markers(
  const void * untyped_member, size_t index)
{
  const visualization_msgs__msg__Marker__Sequence * member =
    (const visualization_msgs__msg__Marker__Sequence *)(untyped_member);
  return &member->data[index];
}

void * moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__get_function__SolutionInfo__markers(
  void * untyped_member, size_t index)
{
  visualization_msgs__msg__Marker__Sequence * member =
    (visualization_msgs__msg__Marker__Sequence *)(untyped_member);
  return &member->data[index];
}

void moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__fetch_function__SolutionInfo__markers(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const visualization_msgs__msg__Marker * item =
    ((const visualization_msgs__msg__Marker *)
    moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__get_const_function__SolutionInfo__markers(untyped_member, index));
  visualization_msgs__msg__Marker * value =
    (visualization_msgs__msg__Marker *)(untyped_value);
  *value = *item;
}

void moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__assign_function__SolutionInfo__markers(
  void * untyped_member, size_t index, const void * untyped_value)
{
  visualization_msgs__msg__Marker * item =
    ((visualization_msgs__msg__Marker *)
    moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__get_function__SolutionInfo__markers(untyped_member, index));
  const visualization_msgs__msg__Marker * value =
    (const visualization_msgs__msg__Marker *)(untyped_value);
  *item = *value;
}

bool moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__resize_function__SolutionInfo__markers(
  void * untyped_member, size_t size)
{
  visualization_msgs__msg__Marker__Sequence * member =
    (visualization_msgs__msg__Marker__Sequence *)(untyped_member);
  visualization_msgs__msg__Marker__Sequence__fini(member);
  return visualization_msgs__msg__Marker__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__SolutionInfo_message_member_array[6] = {
  {
    "id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__SolutionInfo, id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "cost",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__SolutionInfo, cost),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "comment",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__SolutionInfo, comment),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "stage_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__SolutionInfo, stage_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "planner_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__SolutionInfo, planner_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "markers",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__SolutionInfo, markers),  // bytes offset in struct
    NULL,  // default value
    moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__size_function__SolutionInfo__markers,  // size() function pointer
    moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__get_const_function__SolutionInfo__markers,  // get_const(index) function pointer
    moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__get_function__SolutionInfo__markers,  // get(index) function pointer
    moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__fetch_function__SolutionInfo__markers,  // fetch(index, &value) function pointer
    moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__assign_function__SolutionInfo__markers,  // assign(index, value) function pointer
    moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__resize_function__SolutionInfo__markers  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__SolutionInfo_message_members = {
  "moveit_task_constructor_msgs__msg",  // message namespace
  "SolutionInfo",  // message name
  6,  // number of fields
  sizeof(moveit_task_constructor_msgs__msg__SolutionInfo),
  moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__SolutionInfo_message_member_array,  // message members
  moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__SolutionInfo_init_function,  // function to initialize message memory (memory has to be allocated)
  moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__SolutionInfo_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__SolutionInfo_message_type_support_handle = {
  0,
  &moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__SolutionInfo_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_moveit_task_constructor_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, msg, SolutionInfo)() {
  moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__SolutionInfo_message_member_array[5].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, visualization_msgs, msg, Marker)();
  if (!moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__SolutionInfo_message_type_support_handle.typesupport_identifier) {
    moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__SolutionInfo_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &moveit_task_constructor_msgs__msg__SolutionInfo__rosidl_typesupport_introspection_c__SolutionInfo_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
