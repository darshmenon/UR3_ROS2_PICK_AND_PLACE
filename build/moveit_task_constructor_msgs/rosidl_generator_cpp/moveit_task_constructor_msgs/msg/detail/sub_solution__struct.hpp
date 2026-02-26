// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from moveit_task_constructor_msgs:msg/SubSolution.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_SOLUTION__STRUCT_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_SOLUTION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'info'
#include "moveit_task_constructor_msgs/msg/detail/solution_info__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__moveit_task_constructor_msgs__msg__SubSolution __attribute__((deprecated))
#else
# define DEPRECATED__moveit_task_constructor_msgs__msg__SubSolution __declspec(deprecated)
#endif

namespace moveit_task_constructor_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct SubSolution_
{
  using Type = SubSolution_<ContainerAllocator>;

  explicit SubSolution_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_init)
  {
    (void)_init;
  }

  explicit SubSolution_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _info_type =
    moveit_task_constructor_msgs::msg::SolutionInfo_<ContainerAllocator>;
  _info_type info;
  using _sub_solution_id_type =
    std::vector<uint32_t, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<uint32_t>>;
  _sub_solution_id_type sub_solution_id;

  // setters for named parameter idiom
  Type & set__info(
    const moveit_task_constructor_msgs::msg::SolutionInfo_<ContainerAllocator> & _arg)
  {
    this->info = _arg;
    return *this;
  }
  Type & set__sub_solution_id(
    const std::vector<uint32_t, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<uint32_t>> & _arg)
  {
    this->sub_solution_id = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator> *;
  using ConstRawPtr =
    const moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__moveit_task_constructor_msgs__msg__SubSolution
    std::shared_ptr<moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__moveit_task_constructor_msgs__msg__SubSolution
    std::shared_ptr<moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const SubSolution_ & other) const
  {
    if (this->info != other.info) {
      return false;
    }
    if (this->sub_solution_id != other.sub_solution_id) {
      return false;
    }
    return true;
  }
  bool operator!=(const SubSolution_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct SubSolution_

// alias to use template instance with default allocator
using SubSolution =
  moveit_task_constructor_msgs::msg::SubSolution_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_SOLUTION__STRUCT_HPP_
