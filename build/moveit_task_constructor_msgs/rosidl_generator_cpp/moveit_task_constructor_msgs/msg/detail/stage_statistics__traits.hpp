// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from moveit_task_constructor_msgs:msg/StageStatistics.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_STATISTICS__TRAITS_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_STATISTICS__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "moveit_task_constructor_msgs/msg/detail/stage_statistics__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace moveit_task_constructor_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const StageStatistics & msg,
  std::ostream & out)
{
  out << "{";
  // member: id
  {
    out << "id: ";
    rosidl_generator_traits::value_to_yaml(msg.id, out);
    out << ", ";
  }

  // member: solved
  {
    if (msg.solved.size() == 0) {
      out << "solved: []";
    } else {
      out << "solved: [";
      size_t pending_items = msg.solved.size();
      for (auto item : msg.solved) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: failed
  {
    if (msg.failed.size() == 0) {
      out << "failed: []";
    } else {
      out << "failed: [";
      size_t pending_items = msg.failed.size();
      for (auto item : msg.failed) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: num_failed
  {
    out << "num_failed: ";
    rosidl_generator_traits::value_to_yaml(msg.num_failed, out);
    out << ", ";
  }

  // member: total_compute_time
  {
    out << "total_compute_time: ";
    rosidl_generator_traits::value_to_yaml(msg.total_compute_time, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const StageStatistics & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "id: ";
    rosidl_generator_traits::value_to_yaml(msg.id, out);
    out << "\n";
  }

  // member: solved
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.solved.size() == 0) {
      out << "solved: []\n";
    } else {
      out << "solved:\n";
      for (auto item : msg.solved) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: failed
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.failed.size() == 0) {
      out << "failed: []\n";
    } else {
      out << "failed:\n";
      for (auto item : msg.failed) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: num_failed
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "num_failed: ";
    rosidl_generator_traits::value_to_yaml(msg.num_failed, out);
    out << "\n";
  }

  // member: total_compute_time
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "total_compute_time: ";
    rosidl_generator_traits::value_to_yaml(msg.total_compute_time, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const StageStatistics & msg, bool use_flow_style = false)
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
  const moveit_task_constructor_msgs::msg::StageStatistics & msg,
  std::ostream & out, size_t indentation = 0)
{
  moveit_task_constructor_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use moveit_task_constructor_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const moveit_task_constructor_msgs::msg::StageStatistics & msg)
{
  return moveit_task_constructor_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<moveit_task_constructor_msgs::msg::StageStatistics>()
{
  return "moveit_task_constructor_msgs::msg::StageStatistics";
}

template<>
inline const char * name<moveit_task_constructor_msgs::msg::StageStatistics>()
{
  return "moveit_task_constructor_msgs/msg/StageStatistics";
}

template<>
struct has_fixed_size<moveit_task_constructor_msgs::msg::StageStatistics>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<moveit_task_constructor_msgs::msg::StageStatistics>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<moveit_task_constructor_msgs::msg::StageStatistics>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_STATISTICS__TRAITS_HPP_
