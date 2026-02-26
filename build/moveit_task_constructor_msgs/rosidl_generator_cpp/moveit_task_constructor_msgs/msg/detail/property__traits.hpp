// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from moveit_task_constructor_msgs:msg/Property.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__PROPERTY__TRAITS_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__PROPERTY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "moveit_task_constructor_msgs/msg/detail/property__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace moveit_task_constructor_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const Property & msg,
  std::ostream & out)
{
  out << "{";
  // member: name
  {
    out << "name: ";
    rosidl_generator_traits::value_to_yaml(msg.name, out);
    out << ", ";
  }

  // member: description
  {
    out << "description: ";
    rosidl_generator_traits::value_to_yaml(msg.description, out);
    out << ", ";
  }

  // member: type
  {
    out << "type: ";
    rosidl_generator_traits::value_to_yaml(msg.type, out);
    out << ", ";
  }

  // member: value
  {
    out << "value: ";
    rosidl_generator_traits::value_to_yaml(msg.value, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const Property & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: name
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "name: ";
    rosidl_generator_traits::value_to_yaml(msg.name, out);
    out << "\n";
  }

  // member: description
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "description: ";
    rosidl_generator_traits::value_to_yaml(msg.description, out);
    out << "\n";
  }

  // member: type
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "type: ";
    rosidl_generator_traits::value_to_yaml(msg.type, out);
    out << "\n";
  }

  // member: value
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "value: ";
    rosidl_generator_traits::value_to_yaml(msg.value, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Property & msg, bool use_flow_style = false)
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
  const moveit_task_constructor_msgs::msg::Property & msg,
  std::ostream & out, size_t indentation = 0)
{
  moveit_task_constructor_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use moveit_task_constructor_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const moveit_task_constructor_msgs::msg::Property & msg)
{
  return moveit_task_constructor_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<moveit_task_constructor_msgs::msg::Property>()
{
  return "moveit_task_constructor_msgs::msg::Property";
}

template<>
inline const char * name<moveit_task_constructor_msgs::msg::Property>()
{
  return "moveit_task_constructor_msgs/msg/Property";
}

template<>
struct has_fixed_size<moveit_task_constructor_msgs::msg::Property>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<moveit_task_constructor_msgs::msg::Property>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<moveit_task_constructor_msgs::msg::Property>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__PROPERTY__TRAITS_HPP_
