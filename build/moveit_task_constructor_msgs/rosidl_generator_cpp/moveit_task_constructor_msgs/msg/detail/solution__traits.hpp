// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from moveit_task_constructor_msgs:msg/Solution.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION__TRAITS_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "moveit_task_constructor_msgs/msg/detail/solution__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'start_scene'
#include "moveit_msgs/msg/detail/planning_scene__traits.hpp"
// Member 'sub_solution'
#include "moveit_task_constructor_msgs/msg/detail/sub_solution__traits.hpp"
// Member 'sub_trajectory'
#include "moveit_task_constructor_msgs/msg/detail/sub_trajectory__traits.hpp"

namespace moveit_task_constructor_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const Solution & msg,
  std::ostream & out)
{
  out << "{";
  // member: task_id
  {
    out << "task_id: ";
    rosidl_generator_traits::value_to_yaml(msg.task_id, out);
    out << ", ";
  }

  // member: start_scene
  {
    out << "start_scene: ";
    to_flow_style_yaml(msg.start_scene, out);
    out << ", ";
  }

  // member: sub_solution
  {
    if (msg.sub_solution.size() == 0) {
      out << "sub_solution: []";
    } else {
      out << "sub_solution: [";
      size_t pending_items = msg.sub_solution.size();
      for (auto item : msg.sub_solution) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: sub_trajectory
  {
    if (msg.sub_trajectory.size() == 0) {
      out << "sub_trajectory: []";
    } else {
      out << "sub_trajectory: [";
      size_t pending_items = msg.sub_trajectory.size();
      for (auto item : msg.sub_trajectory) {
        to_flow_style_yaml(item, out);
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
  const Solution & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: task_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "task_id: ";
    rosidl_generator_traits::value_to_yaml(msg.task_id, out);
    out << "\n";
  }

  // member: start_scene
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "start_scene:\n";
    to_block_style_yaml(msg.start_scene, out, indentation + 2);
  }

  // member: sub_solution
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.sub_solution.size() == 0) {
      out << "sub_solution: []\n";
    } else {
      out << "sub_solution:\n";
      for (auto item : msg.sub_solution) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }

  // member: sub_trajectory
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.sub_trajectory.size() == 0) {
      out << "sub_trajectory: []\n";
    } else {
      out << "sub_trajectory:\n";
      for (auto item : msg.sub_trajectory) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Solution & msg, bool use_flow_style = false)
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
  const moveit_task_constructor_msgs::msg::Solution & msg,
  std::ostream & out, size_t indentation = 0)
{
  moveit_task_constructor_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use moveit_task_constructor_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const moveit_task_constructor_msgs::msg::Solution & msg)
{
  return moveit_task_constructor_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<moveit_task_constructor_msgs::msg::Solution>()
{
  return "moveit_task_constructor_msgs::msg::Solution";
}

template<>
inline const char * name<moveit_task_constructor_msgs::msg::Solution>()
{
  return "moveit_task_constructor_msgs/msg/Solution";
}

template<>
struct has_fixed_size<moveit_task_constructor_msgs::msg::Solution>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<moveit_task_constructor_msgs::msg::Solution>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<moveit_task_constructor_msgs::msg::Solution>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION__TRAITS_HPP_
