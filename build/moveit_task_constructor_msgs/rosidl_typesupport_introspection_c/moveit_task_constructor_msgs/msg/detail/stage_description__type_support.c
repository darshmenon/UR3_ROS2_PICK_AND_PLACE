// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from moveit_task_constructor_msgs:msg/StageDescription.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "moveit_task_constructor_msgs/msg/detail/stage_description__rosidl_typesupport_introspection_c.h"
#include "moveit_task_constructor_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "moveit_task_constructor_msgs/msg/detail/stage_description__functions.h"
#include "moveit_task_constructor_msgs/msg/detail/stage_description__struct.h"


// Include directives for member types
// Member `name`
#include "rosidl_runtime_c/string_functions.h"
// Member `properties`
#include "moveit_task_constructor_msgs/msg/property.h"
// Member `properties`
#include "moveit_task_constructor_msgs/msg/detail/property__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__StageDescription_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  moveit_task_constructor_msgs__msg__StageDescription__init(message_memory);
}

void moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__StageDescription_fini_function(void * message_memory)
{
  moveit_task_constructor_msgs__msg__StageDescription__fini(message_memory);
}

size_t moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__size_function__StageDescription__properties(
  const void * untyped_member)
{
  const moveit_task_constructor_msgs__msg__Property__Sequence * member =
    (const moveit_task_constructor_msgs__msg__Property__Sequence *)(untyped_member);
  return member->size;
}

const void * moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__get_const_function__StageDescription__properties(
  const void * untyped_member, size_t index)
{
  const moveit_task_constructor_msgs__msg__Property__Sequence * member =
    (const moveit_task_constructor_msgs__msg__Property__Sequence *)(untyped_member);
  return &member->data[index];
}

void * moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__get_function__StageDescription__properties(
  void * untyped_member, size_t index)
{
  moveit_task_constructor_msgs__msg__Property__Sequence * member =
    (moveit_task_constructor_msgs__msg__Property__Sequence *)(untyped_member);
  return &member->data[index];
}

void moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__fetch_function__StageDescription__properties(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const moveit_task_constructor_msgs__msg__Property * item =
    ((const moveit_task_constructor_msgs__msg__Property *)
    moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__get_const_function__StageDescription__properties(untyped_member, index));
  moveit_task_constructor_msgs__msg__Property * value =
    (moveit_task_constructor_msgs__msg__Property *)(untyped_value);
  *value = *item;
}

void moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__assign_function__StageDescription__properties(
  void * untyped_member, size_t index, const void * untyped_value)
{
  moveit_task_constructor_msgs__msg__Property * item =
    ((moveit_task_constructor_msgs__msg__Property *)
    moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__get_function__StageDescription__properties(untyped_member, index));
  const moveit_task_constructor_msgs__msg__Property * value =
    (const moveit_task_constructor_msgs__msg__Property *)(untyped_value);
  *item = *value;
}

bool moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__resize_function__StageDescription__properties(
  void * untyped_member, size_t size)
{
  moveit_task_constructor_msgs__msg__Property__Sequence * member =
    (moveit_task_constructor_msgs__msg__Property__Sequence *)(untyped_member);
  moveit_task_constructor_msgs__msg__Property__Sequence__fini(member);
  return moveit_task_constructor_msgs__msg__Property__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__StageDescription_message_member_array[5] = {
  {
    "id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__StageDescription, id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "parent_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__StageDescription, parent_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "name",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__StageDescription, name),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "flags",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__StageDescription, flags),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "properties",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__msg__StageDescription, properties),  // bytes offset in struct
    NULL,  // default value
    moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__size_function__StageDescription__properties,  // size() function pointer
    moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__get_const_function__StageDescription__properties,  // get_const(index) function pointer
    moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__get_function__StageDescription__properties,  // get(index) function pointer
    moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__fetch_function__StageDescription__properties,  // fetch(index, &value) function pointer
    moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__assign_function__StageDescription__properties,  // assign(index, value) function pointer
    moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__resize_function__StageDescription__properties  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__StageDescription_message_members = {
  "moveit_task_constructor_msgs__msg",  // message namespace
  "StageDescription",  // message name
  5,  // number of fields
  sizeof(moveit_task_constructor_msgs__msg__StageDescription),
  moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__StageDescription_message_member_array,  // message members
  moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__StageDescription_init_function,  // function to initialize message memory (memory has to be allocated)
  moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__StageDescription_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__StageDescription_message_type_support_handle = {
  0,
  &moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__StageDescription_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_moveit_task_constructor_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, msg, StageDescription)() {
  moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__StageDescription_message_member_array[4].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, msg, Property)();
  if (!moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__StageDescription_message_type_support_handle.typesupport_identifier) {
    moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__StageDescription_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &moveit_task_constructor_msgs__msg__StageDescription__rosidl_typesupport_introspection_c__StageDescription_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
