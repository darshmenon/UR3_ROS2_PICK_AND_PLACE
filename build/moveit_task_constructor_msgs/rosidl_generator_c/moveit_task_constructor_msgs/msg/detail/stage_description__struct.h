// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from moveit_task_constructor_msgs:msg/StageDescription.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_DESCRIPTION__STRUCT_H_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_DESCRIPTION__STRUCT_H_

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
#include "rosidl_runtime_c/string.h"
// Member 'properties'
#include "moveit_task_constructor_msgs/msg/detail/property__struct.h"

/// Struct defined in msg/StageDescription in the package moveit_task_constructor_msgs.
/**
  * static description of a stage
 */
typedef struct moveit_task_constructor_msgs__msg__StageDescription
{
  /// unique id within task
  uint32_t id;
  /// parent id, parent_id == id means root
  uint32_t parent_id;
  /// name of this stage
  rosidl_runtime_c__String name;
  /// flags: interface, ...
  uint32_t flags;
  /// properties
  moveit_task_constructor_msgs__msg__Property__Sequence properties;
} moveit_task_constructor_msgs__msg__StageDescription;

// Struct for a sequence of moveit_task_constructor_msgs__msg__StageDescription.
typedef struct moveit_task_constructor_msgs__msg__StageDescription__Sequence
{
  moveit_task_constructor_msgs__msg__StageDescription * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__msg__StageDescription__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_DESCRIPTION__STRUCT_H_
