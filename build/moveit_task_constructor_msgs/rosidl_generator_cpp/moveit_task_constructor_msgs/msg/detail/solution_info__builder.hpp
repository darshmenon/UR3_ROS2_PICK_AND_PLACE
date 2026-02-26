// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from moveit_task_constructor_msgs:msg/SolutionInfo.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION_INFO__BUILDER_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION_INFO__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "moveit_task_constructor_msgs/msg/detail/solution_info__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace moveit_task_constructor_msgs
{

namespace msg
{

namespace builder
{

class Init_SolutionInfo_markers
{
public:
  explicit Init_SolutionInfo_markers(::moveit_task_constructor_msgs::msg::SolutionInfo & msg)
  : msg_(msg)
  {}
  ::moveit_task_constructor_msgs::msg::SolutionInfo markers(::moveit_task_constructor_msgs::msg::SolutionInfo::_markers_type arg)
  {
    msg_.markers = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::SolutionInfo msg_;
};

class Init_SolutionInfo_planner_id
{
public:
  explicit Init_SolutionInfo_planner_id(::moveit_task_constructor_msgs::msg::SolutionInfo & msg)
  : msg_(msg)
  {}
  Init_SolutionInfo_markers planner_id(::moveit_task_constructor_msgs::msg::SolutionInfo::_planner_id_type arg)
  {
    msg_.planner_id = std::move(arg);
    return Init_SolutionInfo_markers(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::SolutionInfo msg_;
};

class Init_SolutionInfo_stage_id
{
public:
  explicit Init_SolutionInfo_stage_id(::moveit_task_constructor_msgs::msg::SolutionInfo & msg)
  : msg_(msg)
  {}
  Init_SolutionInfo_planner_id stage_id(::moveit_task_constructor_msgs::msg::SolutionInfo::_stage_id_type arg)
  {
    msg_.stage_id = std::move(arg);
    return Init_SolutionInfo_planner_id(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::SolutionInfo msg_;
};

class Init_SolutionInfo_comment
{
public:
  explicit Init_SolutionInfo_comment(::moveit_task_constructor_msgs::msg::SolutionInfo & msg)
  : msg_(msg)
  {}
  Init_SolutionInfo_stage_id comment(::moveit_task_constructor_msgs::msg::SolutionInfo::_comment_type arg)
  {
    msg_.comment = std::move(arg);
    return Init_SolutionInfo_stage_id(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::SolutionInfo msg_;
};

class Init_SolutionInfo_cost
{
public:
  explicit Init_SolutionInfo_cost(::moveit_task_constructor_msgs::msg::SolutionInfo & msg)
  : msg_(msg)
  {}
  Init_SolutionInfo_comment cost(::moveit_task_constructor_msgs::msg::SolutionInfo::_cost_type arg)
  {
    msg_.cost = std::move(arg);
    return Init_SolutionInfo_comment(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::SolutionInfo msg_;
};

class Init_SolutionInfo_id
{
public:
  Init_SolutionInfo_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_SolutionInfo_cost id(::moveit_task_constructor_msgs::msg::SolutionInfo::_id_type arg)
  {
    msg_.id = std::move(arg);
    return Init_SolutionInfo_cost(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::SolutionInfo msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::msg::SolutionInfo>()
{
  return moveit_task_constructor_msgs::msg::builder::Init_SolutionInfo_id();
}

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION_INFO__BUILDER_HPP_
