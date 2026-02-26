// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from moveit_task_constructor_msgs:msg/SubSolution.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "moveit_task_constructor_msgs/msg/detail/sub_solution__rosidl_typesupport_introspection_c.h"
#include "moveit_task_constructor_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "moveit_task_constructor_msgs/msg/detail/sub_solution__functions.h"
#include "moveit_task_constructor_msgs/msg/detail/sub_solution__struct.h"


// Include directives for member types
// Member `info`
#include "moveit_task_constructor_msgs/msg/solution_info.h"
// Member `info`
#include "moveit_task_constructor_msgs/msg/detail/solution_info__rosidl_typesupport_introspection_c.h"
// Member `sub_solution_id`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__SubSolution_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  moveit_task_constructor_msgs__msg__SubSolution__init(message_memory);
}

void moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__SubSolution_fini_function(void * message_memory)
{
  moveit_task_constructor_msgs__msg__SubSolution__fini(message_memory);
}

size_t moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__size_function__SubSolution__sub_solution_id(
  const void * untyped_member)
{
  const rosidl_runtime_c__uint32__Sequence * member =
    (const rosidl_runtime_c__uint32__Sequence *)(untyped_member);
  return member->size;
}

const void * moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__get_const_function__SubSolution__sub_solution_id(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__uint32__Sequence * member =
    (const rosidl_runtime_c__uint32__Sequence *)(untyped_member);
  return &member->data[index];
}

void * moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__get_function__SubSolution__sub_solution_id(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__uint32__Sequence * member =
    (rosidl_runtime_c__uint32__Sequence *)(untyped_member);
  return &member->data[index];
}

void moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__fetch_function__SubSolution__sub_solution_id(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const uint32_t * item =
    ((const uint32_t *)
    moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__get_const_function__SubSolution__sub_solution_id(untyped_member, index));
  uint32_t * value =
    (uint32_t *)(untyped_value);
  *value = *item;
}

void moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__assign_function__SubSolution__sub_solution_id(
  void * untyped_member, size_t index, const void * untyped_value)
{
  uint32_t * item =
    ((uint32_t *)
    moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__get_function__SubSolution__sub_solution_id(untyped_member, index));
  const uint32_t * value =
    (const uint32_t *)(untyped_value);
  *item = *value;
}

bool moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__resize_function__SubSolution__sub_solution_id(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__uint32__Sequence * member =
    (rosidl_runtime_c__uint32__Sequence *)(untyped_member);
  rosidl_runtime_c__uint32__Sequence__fini(member);
  return rosidl_runtime_c__uint32__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__SubSolution_message_member_array[2] = {
  {
    "info",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__SubSolution, info),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "sub_solution_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__SubSolution, sub_solution_id),  // bytes offset in struct
    NULL,  // default value
    moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__size_function__SubSolution__sub_solution_id,  // size() function pointer
    moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__get_const_function__SubSolution__sub_solution_id,  // get_const(index) function pointer
    moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__get_function__SubSolution__sub_solution_id,  // get(index) function pointer
    moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__fetch_function__SubSolution__sub_solution_id,  // fetch(index, &value) function pointer
    moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__assign_function__SubSolution__sub_solution_id,  // assign(index, value) function pointer
    moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__resize_function__SubSolution__sub_solution_id  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__SubSolution_message_members = {
  "moveit_task_constructor_msgs__msg",  // message namespace
  "SubSolution",  // message name
  2,  // number of fields
  sizeof(moveit_task_constructor_msgs__msg__SubSolution),
  moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__SubSolution_message_member_array,  // message members
  moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__SubSolution_init_function,  // function to initialize message memory (memory has to be allocated)
  moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__SubSolution_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__SubSolution_message_type_support_handle = {
  0,
  &moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__SubSolution_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_moveit_task_constructor_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, msg, SubSolution)() {
  moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__SubSolution_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, msg, SolutionInfo)();
  if (!moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__SubSolution_message_type_support_handle.typesupport_identifier) {
    moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__SubSolution_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &moveit_task_constructor_msgs__msg__SubSolution__rosidl_typesupport_introspection_c__SubSolution_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
