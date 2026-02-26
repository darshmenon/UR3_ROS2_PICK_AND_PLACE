// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from moveit_task_constructor_msgs:srv/GetSolution.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__SRV__DETAIL__GET_SOLUTION__TRAITS_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__SRV__DETAIL__GET_SOLUTION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "moveit_task_constructor_msgs/srv/detail/get_solution__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace moveit_task_constructor_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const GetSolution_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: solution_id
  {
    out << "solution_id: ";
    rosidl_generator_traits::value_to_yaml(msg.solution_id, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const GetSolution_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: solution_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "solution_id: ";
    rosidl_generator_traits::value_to_yaml(msg.solution_id, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const GetSolution_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace moveit_task_constructor_msgs

namespace rosidl_generator_traits
{

[[deprecated("use moveit_task_constructor_msgs::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const moveit_task_constructor_msgs::srv::GetSolution_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  moveit_task_constructor_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use moveit_task_constructor_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const moveit_task_constructor_msgs::srv::GetSolution_Request & msg)
{
  return moveit_task_constructor_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<moveit_task_constructor_msgs::srv::GetSolution_Request>()
{
  return "moveit_task_constructor_msgs::srv::GetSolution_Request";
}

template<>
inline const char * name<moveit_task_constructor_msgs::srv::GetSolution_Request>()
{
  return "moveit_task_constructor_msgs/srv/GetSolution_Request";
}

template<>
struct has_fixed_size<moveit_task_constructor_msgs::srv::GetSolution_Request>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<moveit_task_constructor_msgs::srv::GetSolution_Request>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<moveit_task_constructor_msgs::srv::GetSolution_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'solution'
#include "moveit_task_constructor_msgs/msg/detail/solution__traits.hpp"

namespace moveit_task_constructor_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const GetSolution_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: solution
  {
    out << "solution: ";
    to_flow_style_yaml(msg.solution, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const GetSolution_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: solution
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "solution:\n";
    to_block_style_yaml(msg.solution, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const GetSolution_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace moveit_task_constructor_msgs

namespace rosidl_generator_traits
{

[[deprecated("use moveit_task_constructor_msgs::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const moveit_task_constructor_msgs::srv::GetSolution_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  moveit_task_constructor_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use moveit_task_constructor_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const moveit_task_constructor_msgs::srv::GetSolution_Response & msg)
{
  return moveit_task_constructor_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<moveit_task_constructor_msgs::srv::GetSolution_Response>()
{
  return "moveit_task_constructor_msgs::srv::GetSolution_Response";
}

template<>
inline const char * name<moveit_task_constructor_msgs::srv::GetSolution_Response>()
{
  return "moveit_task_constructor_msgs/srv/GetSolution_Response";
}

template<>
struct has_fixed_size<moveit_task_constructor_msgs::srv::GetSolution_Response>
  : std::integral_constant<bool, has_fixed_size<moveit_task_constructor_msgs::msg::Solution>::value> {};

template<>
struct has_bounded_size<moveit_task_constructor_msgs::srv::GetSolution_Response>
  : std::integral_constant<bool, has_bounded_size<moveit_task_constructor_msgs::msg::Solution>::value> {};

template<>
struct is_message<moveit_task_constructor_msgs::srv::GetSolution_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<moveit_task_constructor_msgs::srv::GetSolution>()
{
  return "moveit_task_constructor_msgs::srv::GetSolution";
}

template<>
inline const char * name<moveit_task_constructor_msgs::srv::GetSolution>()
{
  return "moveit_task_constructor_msgs/srv/GetSolution";
}

template<>
struct has_fixed_size<moveit_task_constructor_msgs::srv::GetSolution>
  : std::integral_constant<
    bool,
    has_fixed_size<moveit_task_constructor_msgs::srv::GetSolution_Request>::value &&
    has_fixed_size<moveit_task_constructor_msgs::srv::GetSolution_Response>::value
  >
{
};

template<>
struct has_bounded_size<moveit_task_constructor_msgs::srv::GetSolution>
  : std::integral_constant<
    bool,
    has_bounded_size<moveit_task_constructor_msgs::srv::GetSolution_Request>::value &&
    has_bounded_size<moveit_task_constructor_msgs::srv::GetSolution_Response>::value
  >
{
};

template<>
struct is_service<moveit_task_constructor_msgs::srv::GetSolution>
  : std::true_type
{
};

template<>
struct is_service_request<moveit_task_constructor_msgs::srv::GetSolution_Request>
  : std::true_type
{
};

template<>
struct is_service_response<moveit_task_constructor_msgs::srv::GetSolution_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__SRV__DETAIL__GET_SOLUTION__TRAITS_HPP_
