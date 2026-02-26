// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from moveit_task_constructor_msgs:srv/GetSolution.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__SRV__DETAIL__GET_SOLUTION__BUILDER_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__SRV__DETAIL__GET_SOLUTION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "moveit_task_constructor_msgs/srv/detail/get_solution__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace moveit_task_constructor_msgs
{

namespace srv
{

namespace builder
{

class Init_GetSolution_Request_solution_id
{
public:
  Init_GetSolution_Request_solution_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::moveit_task_constructor_msgs::srv::GetSolution_Request solution_id(::moveit_task_constructor_msgs::srv::GetSolution_Request::_solution_id_type arg)
  {
    msg_.solution_id = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::srv::GetSolution_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::srv::GetSolution_Request>()
{
  return moveit_task_constructor_msgs::srv::builder::Init_GetSolution_Request_solution_id();
}

}  // namespace moveit_task_constructor_msgs


namespace moveit_task_constructor_msgs
{

namespace srv
{

namespace builder
{

class Init_GetSolution_Response_solution
{
public:
  Init_GetSolution_Response_solution()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::moveit_task_constructor_msgs::srv::GetSolution_Response solution(::moveit_task_constructor_msgs::srv::GetSolution_Response::_solution_type arg)
  {
    msg_.solution = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::srv::GetSolution_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::srv::GetSolution_Response>()
{
  return moveit_task_constructor_msgs::srv::builder::Init_GetSolution_Response_solution();
}

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__SRV__DETAIL__GET_SOLUTION__BUILDER_HPP_
