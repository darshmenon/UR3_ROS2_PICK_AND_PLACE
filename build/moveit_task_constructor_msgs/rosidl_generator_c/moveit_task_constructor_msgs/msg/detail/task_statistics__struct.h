// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from moveit_task_constructor_msgs:msg/TaskStatistics.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TASK_STATISTICS__STRUCT_H_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TASK_STATISTICS__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'task_id'
#include "rosidl_runtime_c/string.h"
// Member 'stages'
#include "moveit_task_constructor_msgs/msg/detail/stage_statistics__struct.h"

/// Struct defined in msg/TaskStatistics in the package moveit_task_constructor_msgs.
/**
  * unique id of generating task
 */
typedef struct moveit_task_constructor_msgs__msg__TaskStatistics
{
  rosidl_runtime_c__String task_id;
  /// list of all stages, including the task stage itself
  moveit_task_constructor_msgs__msg__StageStatistics__Sequence stages;
} moveit_task_constructor_msgs__msg__TaskStatistics;

// Struct for a sequence of moveit_task_constructor_msgs__msg__TaskStatistics.
typedef struct moveit_task_constructor_msgs__msg__TaskStatistics__Sequence
{
  moveit_task_constructor_msgs__msg__TaskStatistics * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__msg__TaskStatistics__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TASK_STATISTICS__STRUCT_H_
