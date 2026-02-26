// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from moveit_task_constructor_msgs:msg/SubTrajectory.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_TRAJECTORY__STRUCT_H_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_TRAJECTORY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "moveit_task_constructor_msgs/msg/detail/solution_info__struct.h"
// Member 'execution_info'
#include "moveit_task_constructor_msgs/msg/detail/trajectory_execution_info__struct.h"
// Member 'trajectory'
#include "moveit_msgs/msg/detail/robot_trajectory__struct.h"
// Member 'scene_diff'
#include "moveit_msgs/msg/detail/planning_scene__struct.h"

/// Struct defined in msg/SubTrajectory in the package moveit_task_constructor_msgs.
/**
  * generic solution information
 */
typedef struct moveit_task_constructor_msgs__msg__SubTrajectory
{
  moveit_task_constructor_msgs__msg__SolutionInfo info;
  /// trajectory execution information, like controller configuration
  moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo execution_info;
  /// trajectory
  moveit_msgs__msg__RobotTrajectory trajectory;
  /// planning scene of end state as diff w.r.t. start state
  moveit_msgs__msg__PlanningScene scene_diff;
} moveit_task_constructor_msgs__msg__SubTrajectory;

// Struct for a sequence of moveit_task_constructor_msgs__msg__SubTrajectory.
typedef struct moveit_task_constructor_msgs__msg__SubTrajectory__Sequence
{
  moveit_task_constructor_msgs__msg__SubTrajectory * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__msg__SubTrajectory__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_TRAJECTORY__STRUCT_H_
