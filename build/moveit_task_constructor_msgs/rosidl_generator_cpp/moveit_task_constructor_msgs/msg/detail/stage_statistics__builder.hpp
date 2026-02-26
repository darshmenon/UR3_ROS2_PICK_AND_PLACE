// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from moveit_task_constructor_msgs:msg/StageStatistics.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_STATISTICS__BUILDER_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_STATISTICS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "moveit_task_constructor_msgs/msg/detail/stage_statistics__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace moveit_task_constructor_msgs
{

namespace msg
{

namespace builder
{

class Init_StageStatistics_total_compute_time
{
public:
  explicit Init_StageStatistics_total_compute_time(::moveit_task_constructor_msgs::msg::StageStatistics & msg)
  : msg_(msg)
  {}
  ::moveit_task_constructor_msgs::msg::StageStatistics total_compute_time(::moveit_task_constructor_msgs::msg::StageStatistics::_total_compute_time_type arg)
  {
    msg_.total_compute_time = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::StageStatistics msg_;
};

class Init_StageStatistics_num_failed
{
public:
  explicit Init_StageStatistics_num_failed(::moveit_task_constructor_msgs::msg::StageStatistics & msg)
  : msg_(msg)
  {}
  Init_StageStatistics_total_compute_time num_failed(::moveit_task_constructor_msgs::msg::StageStatistics::_num_failed_type arg)
  {
    msg_.num_failed = std::move(arg);
    return Init_StageStatistics_total_compute_time(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::StageStatistics msg_;
};

class Init_StageStatistics_failed
{
public:
  explicit Init_StageStatistics_failed(::moveit_task_constructor_msgs::msg::StageStatistics & msg)
  : msg_(msg)
  {}
  Init_StageStatistics_num_failed failed(::moveit_task_constructor_msgs::msg::StageStatistics::_failed_type arg)
  {
    msg_.failed = std::move(arg);
    return Init_StageStatistics_num_failed(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::StageStatistics msg_;
};

class Init_StageStatistics_solved
{
public:
  explicit Init_StageStatistics_solved(::moveit_task_constructor_msgs::msg::StageStatistics & msg)
  : msg_(msg)
  {}
  Init_StageStatistics_failed solved(::moveit_task_constructor_msgs::msg::StageStatistics::_solved_type arg)
  {
    msg_.solved = std::move(arg);
    return Init_StageStatistics_failed(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::StageStatistics msg_;
};

class Init_StageStatistics_id
{
public:
  Init_StageStatistics_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_StageStatistics_solved id(::moveit_task_constructor_msgs::msg::StageStatistics::_id_type arg)
  {
    msg_.id = std::move(arg);
    return Init_StageStatistics_solved(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::StageStatistics msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::msg::StageStatistics>()
{
  return moveit_task_constructor_msgs::msg::builder::Init_StageStatistics_id();
}

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_STATISTICS__BUILDER_HPP_
