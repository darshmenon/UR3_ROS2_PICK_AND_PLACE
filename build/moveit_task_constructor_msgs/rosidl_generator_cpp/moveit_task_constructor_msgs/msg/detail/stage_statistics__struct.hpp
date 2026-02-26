// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from moveit_task_constructor_msgs:msg/StageStatistics.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_STATISTICS__STRUCT_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_STATISTICS__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__moveit_task_constructor_msgs__msg__StageStatistics __attribute__((deprecated))
#else
# define DEPRECATED__moveit_task_constructor_msgs__msg__StageStatistics __declspec(deprecated)
#endif

namespace moveit_task_constructor_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct StageStatistics_
{
  using Type = StageStatistics_<ContainerAllocator>;

  explicit StageStatistics_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->id = 0ul;
      this->num_failed = 0ul;
      this->total_compute_time = 0.0;
    }
  }

  explicit StageStatistics_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->id = 0ul;
      this->num_failed = 0ul;
      this->total_compute_time = 0.0;
    }
  }

  // field types and members
  using _id_type =
    uint32_t;
  _id_type id;
  using _solved_type =
    std::vector<uint32_t, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<uint32_t>>;
  _solved_type solved;
  using _failed_type =
    std::vector<uint32_t, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<uint32_t>>;
  _failed_type failed;
  using _num_failed_type =
    uint32_t;
  _num_failed_type num_failed;
  using _total_compute_time_type =
    double;
  _total_compute_time_type total_compute_time;

  // setters for named parameter idiom
  Type & set__id(
    const uint32_t & _arg)
  {
    this->id = _arg;
    return *this;
  }
  Type & set__solved(
    const std::vector<uint32_t, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<uint32_t>> & _arg)
  {
    this->solved = _arg;
    return *this;
  }
  Type & set__failed(
    const std::vector<uint32_t, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<uint32_t>> & _arg)
  {
    this->failed = _arg;
    return *this;
  }
  Type & set__num_failed(
    const uint32_t & _arg)
  {
    this->num_failed = _arg;
    return *this;
  }
  Type & set__total_compute_time(
    const double & _arg)
  {
    this->total_compute_time = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator> *;
  using ConstRawPtr =
    const moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__moveit_task_constructor_msgs__msg__StageStatistics
    std::shared_ptr<moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__moveit_task_constructor_msgs__msg__StageStatistics
    std::shared_ptr<moveit_task_constructor_msgs::msg::StageStatistics_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const StageStatistics_ & other) const
  {
    if (this->id != other.id) {
      return false;
    }
    if (this->solved != other.solved) {
      return false;
    }
    if (this->failed != other.failed) {
      return false;
    }
    if (this->num_failed != other.num_failed) {
      return false;
    }
    if (this->total_compute_time != other.total_compute_time) {
      return false;
    }
    return true;
  }
  bool operator!=(const StageStatistics_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct StageStatistics_

// alias to use template instance with default allocator
using StageStatistics =
  moveit_task_constructor_msgs::msg::StageStatistics_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_STATISTICS__STRUCT_HPP_
