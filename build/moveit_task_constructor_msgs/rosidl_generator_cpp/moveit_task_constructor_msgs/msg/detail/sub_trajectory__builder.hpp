// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from moveit_task_constructor_msgs:msg/SubTrajectory.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_TRAJECTORY__BUILDER_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_TRAJECTORY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "moveit_task_constructor_msgs/msg/detail/sub_trajectory__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace moveit_task_constructor_msgs
{

namespace msg
{

namespace builder
{

class Init_SubTrajectory_scene_diff
{
public:
  explicit Init_SubTrajectory_scene_diff(::moveit_task_constructor_msgs::msg::SubTrajectory & msg)
  : msg_(msg)
  {}
  ::moveit_task_constructor_msgs::msg::SubTrajectory scene_diff(::moveit_task_constructor_msgs::msg::SubTrajectory::_scene_diff_type arg)
  {
    msg_.scene_diff = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::SubTrajectory msg_;
};

class Init_SubTrajectory_trajectory
{
public:
  explicit Init_SubTrajectory_trajectory(::moveit_task_constructor_msgs::msg::SubTrajectory & msg)
  : msg_(msg)
  {}
  Init_SubTrajectory_scene_diff trajectory(::moveit_task_constructor_msgs::msg::SubTrajectory::_trajectory_type arg)
  {
    msg_.trajectory = std::move(arg);
    return Init_SubTrajectory_scene_diff(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::SubTrajectory msg_;
};

class Init_SubTrajectory_execution_info
{
public:
  explicit Init_SubTrajectory_execution_info(::moveit_task_constructor_msgs::msg::SubTrajectory & msg)
  : msg_(msg)
  {}
  Init_SubTrajectory_trajectory execution_info(::moveit_task_constructor_msgs::msg::SubTrajectory::_execution_info_type arg)
  {
    msg_.execution_info = std::move(arg);
    return Init_SubTrajectory_trajectory(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::SubTrajectory msg_;
};

class Init_SubTrajectory_info
{
public:
  Init_SubTrajectory_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_SubTrajectory_execution_info info(::moveit_task_constructor_msgs::msg::SubTrajectory::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_SubTrajectory_execution_info(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::SubTrajectory msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::msg::SubTrajectory>()
{
  return moveit_task_constructor_msgs::msg::builder::Init_SubTrajectory_info();
}

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_TRAJECTORY__BUILDER_HPP_
