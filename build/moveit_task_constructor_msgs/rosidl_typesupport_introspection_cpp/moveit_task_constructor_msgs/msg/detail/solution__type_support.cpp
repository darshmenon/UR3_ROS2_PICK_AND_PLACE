// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from moveit_task_constructor_msgs:msg/Solution.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "moveit_task_constructor_msgs/msg/detail/solution__struct.hpp"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace moveit_task_constructor_msgs
{

namespace msg
{

namespace rosidl_typesupport_introspection_cpp
{

void Solution_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) moveit_task_constructor_msgs::msg::Solution(_init);
}

void Solution_fini_function(void * message_memory)
{
  auto typed_message = static_cast<moveit_task_constructor_msgs::msg::Solution *>(message_memory);
  typed_message->~Solution();
}

size_t size_function__Solution__sub_solution(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<moveit_task_constructor_msgs::msg::SubSolution> *>(untyped_member);
  return member->size();
}

const void * get_const_function__Solution__sub_solution(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<moveit_task_constructor_msgs::msg::SubSolution> *>(untyped_member);
  return &member[index];
}

void * get_function__Solution__sub_solution(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<moveit_task_constructor_msgs::msg::SubSolution> *>(untyped_member);
  return &member[index];
}

void fetch_function__Solution__sub_solution(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const moveit_task_constructor_msgs::msg::SubSolution *>(
    get_const_function__Solution__sub_solution(untyped_member, index));
  auto & value = *reinterpret_cast<moveit_task_constructor_msgs::msg::SubSolution *>(untyped_value);
  value = item;
}

void assign_function__Solution__sub_solution(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<moveit_task_constructor_msgs::msg::SubSolution *>(
    get_function__Solution__sub_solution(untyped_member, index));
  const auto & value = *reinterpret_cast<const moveit_task_constructor_msgs::msg::SubSolution *>(untyped_value);
  item = value;
}

void resize_function__Solution__sub_solution(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<moveit_task_constructor_msgs::msg::SubSolution> *>(untyped_member);
  member->resize(size);
}

size_t size_function__Solution__sub_trajectory(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<moveit_task_constructor_msgs::msg::SubTrajectory> *>(untyped_member);
  return member->size();
}

const void * get_const_function__Solution__sub_trajectory(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<moveit_task_constructor_msgs::msg::SubTrajectory> *>(untyped_member);
  return &member[index];
}

void * get_function__Solution__sub_trajectory(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<moveit_task_constructor_msgs::msg::SubTrajectory> *>(untyped_member);
  return &member[index];
}

void fetch_function__Solution__sub_trajectory(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const moveit_task_constructor_msgs::msg::SubTrajectory *>(
    get_const_function__Solution__sub_trajectory(untyped_member, index));
  auto & value = *reinterpret_cast<moveit_task_constructor_msgs::msg::SubTrajectory *>(untyped_value);
  value = item;
}

void assign_function__Solution__sub_trajectory(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<moveit_task_constructor_msgs::msg::SubTrajectory *>(
    get_function__Solution__sub_trajectory(untyped_member, index));
  const auto & value = *reinterpret_cast<const moveit_task_constructor_msgs::msg::SubTrajectory *>(untyped_value);
  item = value;
}

void resize_function__Solution__sub_trajectory(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<moveit_task_constructor_msgs::msg::SubTrajectory> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember Solution_message_member_array[4] = {
  {
    "task_id",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs::msg::Solution, task_id),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "start_scene",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<moveit_msgs::msg::PlanningScene>(),  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs::msg::Solution, start_scene),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "sub_solution",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<moveit_task_constructor_msgs::msg::SubSolution>(),  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs::msg::Solution, sub_solution),  // bytes offset in struct
    nullptr,  // default value
    size_function__Solution__sub_solution,  // size() function pointer
    get_const_function__Solution__sub_solution,  // get_const(index) function pointer
    get_function__Solution__sub_solution,  // get(index) function pointer
    fetch_function__Solution__sub_solution,  // fetch(index, &value) function pointer
    assign_function__Solution__sub_solution,  // assign(index, value) function pointer
    resize_function__Solution__sub_solution  // resize(index) function pointer
  },
  {
    "sub_trajectory",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<moveit_task_constructor_msgs::msg::SubTrajectory>(),  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs::msg::Solution, sub_trajectory),  // bytes offset in struct
    nullptr,  // default value
    size_function__Solution__sub_trajectory,  // size() function pointer
    get_const_function__Solution__sub_trajectory,  // get_const(index) function pointer
    get_function__Solution__sub_trajectory,  // get(index) function pointer
    fetch_function__Solution__sub_trajectory,  // fetch(index, &value) function pointer
    assign_function__Solution__sub_trajectory,  // assign(index, value) function pointer
    resize_function__Solution__sub_trajectory  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers Solution_message_members = {
  "moveit_task_constructor_msgs::msg",  // message namespace
  "Solution",  // message name
  4,  // number of fields
  sizeof(moveit_task_constructor_msgs::msg::Solution),
  Solution_message_member_array,  // message members
  Solution_init_function,  // function to initialize message memory (memory has to be allocated)
  Solution_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t Solution_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &Solution_message_members,
  get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace moveit_task_constructor_msgs


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<moveit_task_constructor_msgs::msg::Solution>()
{
  return &::moveit_task_constructor_msgs::msg::rosidl_typesupport_introspection_cpp::Solution_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, moveit_task_constructor_msgs, msg, Solution)() {
  return &::moveit_task_constructor_msgs::msg::rosidl_typesupport_introspection_cpp::Solution_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
