// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from moveit_task_constructor_msgs:msg/TaskStatistics.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TASK_STATISTICS__BUILDER_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TASK_STATISTICS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "moveit_task_constructor_msgs/msg/detail/task_statistics__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace moveit_task_constructor_msgs
{

namespace msg
{

namespace builder
{

class Init_TaskStatistics_stages
{
public:
  explicit Init_TaskStatistics_stages(::moveit_task_constructor_msgs::msg::TaskStatistics & msg)
  : msg_(msg)
  {}
  ::moveit_task_constructor_msgs::msg::TaskStatistics stages(::moveit_task_constructor_msgs::msg::TaskStatistics::_stages_type arg)
  {
    msg_.stages = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::TaskStatistics msg_;
};

class Init_TaskStatistics_task_id
{
public:
  Init_TaskStatistics_task_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_TaskStatistics_stages task_id(::moveit_task_constructor_msgs::msg::TaskStatistics::_task_id_type arg)
  {
    msg_.task_id = std::move(arg);
    return Init_TaskStatistics_stages(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::TaskStatistics msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::msg::TaskStatistics>()
{
  return moveit_task_constructor_msgs::msg::builder::Init_TaskStatistics_task_id();
}

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TASK_STATISTICS__BUILDER_HPP_
