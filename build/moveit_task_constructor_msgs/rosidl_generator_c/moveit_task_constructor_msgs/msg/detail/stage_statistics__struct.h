// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from moveit_task_constructor_msgs:msg/StageStatistics.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_STATISTICS__STRUCT_H_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_STATISTICS__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'solved'
// Member 'failed'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in msg/StageStatistics in the package moveit_task_constructor_msgs.
/**
  * dynamically changing information for a stage
 */
typedef struct moveit_task_constructor_msgs__msg__StageStatistics
{
  /// unique id within task
  uint32_t id;
  /// successful solution IDs of this stage, sorted by increasing cost
  rosidl_runtime_c__uint32__Sequence solved;
  /// (optional) failed solution IDs of this stage
  rosidl_runtime_c__uint32__Sequence failed;
  /// number of failed solutions (if failed is empty)
  uint32_t num_failed;
  /// total computation time in seconds
  double total_compute_time;
} moveit_task_constructor_msgs__msg__StageStatistics;

// Struct for a sequence of moveit_task_constructor_msgs__msg__StageStatistics.
typedef struct moveit_task_constructor_msgs__msg__StageStatistics__Sequence
{
  moveit_task_constructor_msgs__msg__StageStatistics * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__msg__StageStatistics__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_STATISTICS__STRUCT_H_
