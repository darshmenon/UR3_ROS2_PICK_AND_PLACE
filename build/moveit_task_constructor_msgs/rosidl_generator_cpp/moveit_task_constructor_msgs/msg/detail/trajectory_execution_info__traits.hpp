// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from moveit_task_constructor_msgs:msg/TrajectoryExecutionInfo.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TRAJECTORY_EXECUTION_INFO__TRAITS_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TRAJECTORY_EXECUTION_INFO__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "moveit_task_constructor_msgs/msg/detail/trajectory_execution_info__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace moveit_task_constructor_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const TrajectoryExecutionInfo & msg,
  std::ostream & out)
{
  out << "{";
  // member: controller_names
  {
    if (msg.controller_names.size() == 0) {
      out << "controller_names: []";
    } else {
      out << "controller_names: [";
      size_t pending_items = msg.controller_names.size();
      for (auto item : msg.controller_names) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const TrajectoryExecutionInfo & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: controller_names
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.controller_names.size() == 0) {
      out << "controller_names: []\n";
    } else {
      out << "controller_names:\n";
      for (auto item : msg.controller_names) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const TrajectoryExecutionInfo & msg, bool use_flow_style = false)
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
  const moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo & msg,
  std::ostream & out, size_t indentation = 0)
{
  moveit_task_constructor_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use moveit_task_constructor_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo & msg)
{
  return moveit_task_constructor_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo>()
{
  return "moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo";
}

template<>
inline const char * name<moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo>()
{
  return "moveit_task_constructor_msgs/msg/TrajectoryExecutionInfo";
}

template<>
struct has_fixed_size<moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TRAJECTORY_EXECUTION_INFO__TRAITS_HPP_
