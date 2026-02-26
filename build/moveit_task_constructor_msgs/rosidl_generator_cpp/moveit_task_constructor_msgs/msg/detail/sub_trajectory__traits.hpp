// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from moveit_task_constructor_msgs:msg/SubTrajectory.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_TRAJECTORY__TRAITS_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_TRAJECTORY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "moveit_task_constructor_msgs/msg/detail/sub_trajectory__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'info'
#include "moveit_task_constructor_msgs/msg/detail/solution_info__traits.hpp"
// Member 'execution_info'
#include "moveit_task_constructor_msgs/msg/detail/trajectory_execution_info__traits.hpp"
// Member 'trajectory'
#include "moveit_msgs/msg/detail/robot_trajectory__traits.hpp"
// Member 'scene_diff'
#include "moveit_msgs/msg/detail/planning_scene__traits.hpp"

namespace moveit_task_constructor_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const SubTrajectory & msg,
  std::ostream & out)
{
  out << "{";
  // member: info
  {
    out << "info: ";
    to_flow_style_yaml(msg.info, out);
    out << ", ";
  }

  // member: execution_info
  {
    out << "execution_info: ";
    to_flow_style_yaml(msg.execution_info, out);
    out << ", ";
  }

  // member: trajectory
  {
    out << "trajectory: ";
    to_flow_style_yaml(msg.trajectory, out);
    out << ", ";
  }

  // member: scene_diff
  {
    out << "scene_diff: ";
    to_flow_style_yaml(msg.scene_diff, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const SubTrajectory & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: info
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "info:\n";
    to_block_style_yaml(msg.info, out, indentation + 2);
  }

  // member: execution_info
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "execution_info:\n";
    to_block_style_yaml(msg.execution_info, out, indentation + 2);
  }

  // member: trajectory
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "trajectory:\n";
    to_block_style_yaml(msg.trajectory, out, indentation + 2);
  }

  // member: scene_diff
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "scene_diff:\n";
    to_block_style_yaml(msg.scene_diff, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const SubTrajectory & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace moveit_task_constructor_msgs

namespace rosidl_generator_traits
{

[[deprecated("use moveit_task_constructor_msgs::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const moveit_task_constructor_msgs::msg::SubTrajectory & msg,
  std::ostream & out, size_t indentation = 0)
{
  moveit_task_constructor_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use moveit_task_constructor_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const moveit_task_constructor_msgs::msg::SubTrajectory & msg)
{
  return moveit_task_constructor_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<moveit_task_constructor_msgs::msg::SubTrajectory>()
{
  return "moveit_task_constructor_msgs::msg::SubTrajectory";
}

template<>
inline const char * name<moveit_task_constructor_msgs::msg::SubTrajectory>()
{
  return "moveit_task_constructor_msgs/msg/SubTrajectory";
}

template<>
struct has_fixed_size<moveit_task_constructor_msgs::msg::SubTrajectory>
  : std::integral_constant<bool, has_fixed_size<moveit_msgs::msg::PlanningScene>::value && has_fixed_size<moveit_msgs::msg::RobotTrajectory>::value && has_fixed_size<moveit_task_constructor_msgs::msg::SolutionInfo>::value && has_fixed_size<moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo>::value> {};

template<>
struct has_bounded_size<moveit_task_constructor_msgs::msg::SubTrajectory>
  : std::integral_constant<bool, has_bounded_size<moveit_msgs::msg::PlanningScene>::value && has_bounded_size<moveit_msgs::msg::RobotTrajectory>::value && has_bounded_size<moveit_task_constructor_msgs::msg::SolutionInfo>::value && has_bounded_size<moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo>::value> {};

template<>
struct is_message<moveit_task_constructor_msgs::msg::SubTrajectory>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_TRAJECTORY__TRAITS_HPP_
