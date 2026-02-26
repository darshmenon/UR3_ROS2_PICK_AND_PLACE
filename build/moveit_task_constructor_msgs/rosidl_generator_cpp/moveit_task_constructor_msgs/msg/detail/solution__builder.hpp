// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from moveit_task_constructor_msgs:msg/Solution.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION__BUILDER_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "moveit_task_constructor_msgs/msg/detail/solution__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace moveit_task_constructor_msgs
{

namespace msg
{

namespace builder
{

class Init_Solution_sub_trajectory
{
public:
  explicit Init_Solution_sub_trajectory(::moveit_task_constructor_msgs::msg::Solution & msg)
  : msg_(msg)
  {}
  ::moveit_task_constructor_msgs::msg::Solution sub_trajectory(::moveit_task_constructor_msgs::msg::Solution::_sub_trajectory_type arg)
  {
    msg_.sub_trajectory = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::Solution msg_;
};

class Init_Solution_sub_solution
{
public:
  explicit Init_Solution_sub_solution(::moveit_task_constructor_msgs::msg::Solution & msg)
  : msg_(msg)
  {}
  Init_Solution_sub_trajectory sub_solution(::moveit_task_constructor_msgs::msg::Solution::_sub_solution_type arg)
  {
    msg_.sub_solution = std::move(arg);
    return Init_Solution_sub_trajectory(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::Solution msg_;
};

class Init_Solution_start_scene
{
public:
  explicit Init_Solution_start_scene(::moveit_task_constructor_msgs::msg::Solution & msg)
  : msg_(msg)
  {}
  Init_Solution_sub_solution start_scene(::moveit_task_constructor_msgs::msg::Solution::_start_scene_type arg)
  {
    msg_.start_scene = std::move(arg);
    return Init_Solution_sub_solution(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::Solution msg_;
};

class Init_Solution_task_id
{
public:
  Init_Solution_task_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Solution_start_scene task_id(::moveit_task_constructor_msgs::msg::Solution::_task_id_type arg)
  {
    msg_.task_id = std::move(arg);
    return Init_Solution_start_scene(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::Solution msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::msg::Solution>()
{
  return moveit_task_constructor_msgs::msg::builder::Init_Solution_task_id();
}

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION__BUILDER_HPP_
