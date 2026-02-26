// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from moveit_task_constructor_msgs:msg/SubSolution.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_SOLUTION__BUILDER_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_SOLUTION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "moveit_task_constructor_msgs/msg/detail/sub_solution__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace moveit_task_constructor_msgs
{

namespace msg
{

namespace builder
{

class Init_SubSolution_sub_solution_id
{
public:
  explicit Init_SubSolution_sub_solution_id(::moveit_task_constructor_msgs::msg::SubSolution & msg)
  : msg_(msg)
  {}
  ::moveit_task_constructor_msgs::msg::SubSolution sub_solution_id(::moveit_task_constructor_msgs::msg::SubSolution::_sub_solution_id_type arg)
  {
    msg_.sub_solution_id = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::SubSolution msg_;
};

class Init_SubSolution_info
{
public:
  Init_SubSolution_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_SubSolution_sub_solution_id info(::moveit_task_constructor_msgs::msg::SubSolution::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_SubSolution_sub_solution_id(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::SubSolution msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::msg::SubSolution>()
{
  return moveit_task_constructor_msgs::msg::builder::Init_SubSolution_info();
}

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_SOLUTION__BUILDER_HPP_
