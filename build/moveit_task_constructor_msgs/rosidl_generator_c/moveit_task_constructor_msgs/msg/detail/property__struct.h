// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from moveit_task_constructor_msgs:msg/Property.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__PROPERTY__STRUCT_H_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__PROPERTY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'name'
// Member 'description'
// Member 'type'
// Member 'value'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/Property in the package moveit_task_constructor_msgs.
typedef struct moveit_task_constructor_msgs__msg__Property
{
  rosidl_runtime_c__String name;
  rosidl_runtime_c__String description;
  rosidl_runtime_c__String type;
  rosidl_runtime_c__String value;
} moveit_task_constructor_msgs__msg__Property;

// Struct for a sequence of moveit_task_constructor_msgs__msg__Property.
typedef struct moveit_task_constructor_msgs__msg__Property__Sequence
{
  moveit_task_constructor_msgs__msg__Property * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__msg__Property__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__PROPERTY__STRUCT_H_
