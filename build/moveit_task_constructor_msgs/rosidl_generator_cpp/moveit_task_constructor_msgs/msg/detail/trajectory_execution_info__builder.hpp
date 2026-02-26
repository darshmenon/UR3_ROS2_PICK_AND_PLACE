// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from moveit_task_constructor_msgs:msg/TrajectoryExecutionInfo.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TRAJECTORY_EXECUTION_INFO__BUILDER_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TRAJECTORY_EXECUTION_INFO__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "moveit_task_constructor_msgs/msg/detail/trajectory_execution_info__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace moveit_task_constructor_msgs
{

namespace msg
{

namespace builder
{

class Init_TrajectoryExecutionInfo_controller_names
{
public:
  Init_TrajectoryExecutionInfo_controller_names()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo controller_names(::moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo::_controller_names_type arg)
  {
    msg_.controller_names = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo>()
{
  return moveit_task_constructor_msgs::msg::builder::Init_TrajectoryExecutionInfo_controller_names();
}

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TRAJECTORY_EXECUTION_INFO__BUILDER_HPP_
