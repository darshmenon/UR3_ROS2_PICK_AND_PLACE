// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from moveit_task_constructor_msgs:msg/TaskStatistics.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TASK_STATISTICS__STRUCT_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TASK_STATISTICS__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'stages'
#include "moveit_task_constructor_msgs/msg/detail/stage_statistics__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__moveit_task_constructor_msgs__msg__TaskStatistics __attribute__((deprecated))
#else
# define DEPRECATED__moveit_task_constructor_msgs__msg__TaskStatistics __declspec(deprecated)
#endif

namespace moveit_task_constructor_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct TaskStatistics_
{
  using Type = TaskStatistics_<ContainerAllocator>;

  explicit TaskStatistics_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->task_id = "";
    }
  }

  explicit TaskStatistics_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : task_id(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->task_id = "";
    }
  }

  // field types and members
  using _task_id_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _task_id_type task_id;
  using _stages_type =
    std::vector<moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator>>>;
  _stages_type stages;

  // setters for named parameter idiom
  Type & set__task_id(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->task_id = _arg;
    return *this;
  }
  Type & set__stages(
    const std::vector<moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator>>> & _arg)
  {
    this->stages = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    moveit_task_constructor_msgs::msg::TaskStatistics_<ContainerAllocator> *;
  using ConstRawPtr =
    const moveit_task_constructor_msgs::msg::TaskStatistics_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::msg::TaskStatistics_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::msg::TaskStatistics_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::msg::TaskStatistics_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::msg::TaskStatistics_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::msg::TaskStatistics_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::msg::TaskStatistics_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::msg::TaskStatistics_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::msg::TaskStatistics_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__moveit_task_constructor_msgs__msg__TaskStatistics
    std::shared_ptr<moveit_task_constructor_msgs::msg::TaskStatistics_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__moveit_task_constructor_msgs__msg__TaskStatistics
    std::shared_ptr<moveit_task_constructor_msgs::msg::TaskStatistics_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const TaskStatistics_ & other) const
  {
    if (this->task_id != other.task_id) {
      return false;
    }
    if (this->stages != other.stages) {
      return false;
    }
    return true;
  }
  bool operator!=(const TaskStatistics_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct TaskStatistics_

// alias to use template instance with default allocator
using TaskStatistics =
  moveit_task_constructor_msgs::msg::TaskStatistics_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__TASK_STATISTICS__STRUCT_HPP_
