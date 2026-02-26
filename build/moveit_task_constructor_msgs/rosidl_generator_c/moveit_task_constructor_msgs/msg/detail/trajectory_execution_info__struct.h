// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from moveit_task_constructor_msgs:msg/TrajectoryExecutionInfo.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TRAJECTORY_EXECUTION_INFO__STRUCT_H_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TRAJECTORY_EXECUTION_INFO__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'controller_names'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/TrajectoryExecutionInfo in the package moveit_task_constructor_msgs.
/**
  * List of controllers to use when executing the trajectory
 */
typedef struct moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo
{
  rosidl_runtime_c__String__Sequence controller_names;
} moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo;

// Struct for a sequence of moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo.
typedef struct moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__Sequence
{
  moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TRAJECTORY_EXECUTION_INFO__STRUCT_H_
