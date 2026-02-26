// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from moveit_task_constructor_msgs:msg/StageDescription.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_DESCRIPTION__BUILDER_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_DESCRIPTION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "moveit_task_constructor_msgs/msg/detail/stage_description__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace moveit_task_constructor_msgs
{

namespace msg
{

namespace builder
{

class Init_StageDescription_properties
{
public:
  explicit Init_StageDescription_properties(::moveit_task_constructor_msgs::msg::StageDescription & msg)
  : msg_(msg)
  {}
  ::moveit_task_constructor_msgs::msg::StageDescription properties(::moveit_task_constructor_msgs::msg::StageDescription::_properties_type arg)
  {
    msg_.properties = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::StageDescription msg_;
};

class Init_StageDescription_flags
{
public:
  explicit Init_StageDescription_flags(::moveit_task_constructor_msgs::msg::StageDescription & msg)
  : msg_(msg)
  {}
  Init_StageDescription_properties flags(::moveit_task_constructor_msgs::msg::StageDescription::_flags_type arg)
  {
    msg_.flags = std::move(arg);
    return Init_StageDescription_properties(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::StageDescription msg_;
};

class Init_StageDescription_name
{
public:
  explicit Init_StageDescription_name(::moveit_task_constructor_msgs::msg::StageDescription & msg)
  : msg_(msg)
  {}
  Init_StageDescription_flags name(::moveit_task_constructor_msgs::msg::StageDescription::_name_type arg)
  {
    msg_.name = std::move(arg);
    return Init_StageDescription_flags(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::StageDescription msg_;
};

class Init_StageDescription_parent_id
{
public:
  explicit Init_StageDescription_parent_id(::moveit_task_constructor_msgs::msg::StageDescription & msg)
  : msg_(msg)
  {}
  Init_StageDescription_name parent_id(::moveit_task_constructor_msgs::msg::StageDescription::_parent_id_type arg)
  {
    msg_.parent_id = std::move(arg);
    return Init_StageDescription_name(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::StageDescription msg_;
};

class Init_StageDescription_id
{
public:
  Init_StageDescription_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_StageDescription_parent_id id(::moveit_task_constructor_msgs::msg::StageDescription::_id_type arg)
  {
    msg_.id = std::move(arg);
    return Init_StageDescription_parent_id(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::StageDescription msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::msg::StageDescription>()
{
  return moveit_task_constructor_msgs::msg::builder::Init_StageDescription_id();
}

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_DESCRIPTION__BUILDER_HPP_
