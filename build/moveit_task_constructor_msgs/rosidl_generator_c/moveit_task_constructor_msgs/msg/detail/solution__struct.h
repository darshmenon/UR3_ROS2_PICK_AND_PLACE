// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from moveit_task_constructor_msgs:msg/Solution.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION__STRUCT_H_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION__STRUCT_H_

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
// Member 'start_scene'
#include "moveit_msgs/msg/detail/planning_scene__struct.h"
// Member 'sub_solution'
#include "moveit_task_constructor_msgs/msg/detail/sub_solution__struct.h"
// Member 'sub_trajectory'
#include "moveit_task_constructor_msgs/msg/detail/sub_trajectory__struct.h"

/// Struct defined in msg/Solution in the package moveit_task_constructor_msgs.
/**
  * id of generating task
 */
typedef struct moveit_task_constructor_msgs__msg__Solution
{
  rosidl_runtime_c__String task_id;
  /// planning scene of start state
  moveit_msgs__msg__PlanningScene start_scene;
  /// set of all sub solutions involved
  moveit_task_constructor_msgs__msg__SubSolution__Sequence sub_solution;
  /// (ordered) sequence of actual trajectories
  moveit_task_constructor_msgs__msg__SubTrajectory__Sequence sub_trajectory;
} moveit_task_constructor_msgs__msg__Solution;

// Struct for a sequence of moveit_task_constructor_msgs__msg__Solution.
typedef struct moveit_task_constructor_msgs__msg__Solution__Sequence
{
  moveit_task_constructor_msgs__msg__Solution * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__msg__Solution__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION__STRUCT_H_
