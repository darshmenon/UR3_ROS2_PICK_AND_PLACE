// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from moveit_task_constructor_msgs:msg/SolutionInfo.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION_INFO__STRUCT_H_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION_INFO__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'comment'
// Member 'planner_id'
#include "rosidl_runtime_c/string.h"
// Member 'markers'
#include "visualization_msgs/msg/detail/marker__struct.h"

/// Struct defined in msg/SolutionInfo in the package moveit_task_constructor_msgs.
/**
  * unique id within task
 */
typedef struct moveit_task_constructor_msgs__msg__SolutionInfo
{
  uint32_t id;
  /// associated cost
  float cost;
  /// associated comment, usually providing failure hint
  rosidl_runtime_c__String comment;
  /// id of stage that created this trajectory
  uint32_t stage_id;
  /// name of the planner that created this solution
  rosidl_runtime_c__String planner_id;
  /// markers, e.g. providing additional hints or illustrating failure
  visualization_msgs__msg__Marker__Sequence markers;
} moveit_task_constructor_msgs__msg__SolutionInfo;

// Struct for a sequence of moveit_task_constructor_msgs__msg__SolutionInfo.
typedef struct moveit_task_constructor_msgs__msg__SolutionInfo__Sequence
{
  moveit_task_constructor_msgs__msg__SolutionInfo * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__msg__SolutionInfo__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION_INFO__STRUCT_H_
