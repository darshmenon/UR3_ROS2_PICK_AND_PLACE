// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from moveit_task_constructor_msgs:msg/Property.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__PROPERTY__BUILDER_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__PROPERTY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "moveit_task_constructor_msgs/msg/detail/property__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace moveit_task_constructor_msgs
{

namespace msg
{

namespace builder
{

class Init_Property_value
{
public:
  explicit Init_Property_value(::moveit_task_constructor_msgs::msg::Property & msg)
  : msg_(msg)
  {}
  ::moveit_task_constructor_msgs::msg::Property value(::moveit_task_constructor_msgs::msg::Property::_value_type arg)
  {
    msg_.value = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::Property msg_;
};

class Init_Property_type
{
public:
  explicit Init_Property_type(::moveit_task_constructor_msgs::msg::Property & msg)
  : msg_(msg)
  {}
  Init_Property_value type(::moveit_task_constructor_msgs::msg::Property::_type_type arg)
  {
    msg_.type = std::move(arg);
    return Init_Property_value(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::Property msg_;
};

class Init_Property_description
{
public:
  explicit Init_Property_description(::moveit_task_constructor_msgs::msg::Property & msg)
  : msg_(msg)
  {}
  Init_Property_type description(::moveit_task_constructor_msgs::msg::Property::_description_type arg)
  {
    msg_.description = std::move(arg);
    return Init_Property_type(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::Property msg_;
};

class Init_Property_name
{
public:
  Init_Property_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Property_description name(::moveit_task_constructor_msgs::msg::Property::_name_type arg)
  {
    msg_.name = std::move(arg);
    return Init_Property_description(msg_);
  }

private:
  ::moveit_task_constructor_msgs::msg::Property msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::msg::Property>()
{
  return moveit_task_constructor_msgs::msg::builder::Init_Property_name();
}

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__PROPERTY__BUILDER_HPP_
