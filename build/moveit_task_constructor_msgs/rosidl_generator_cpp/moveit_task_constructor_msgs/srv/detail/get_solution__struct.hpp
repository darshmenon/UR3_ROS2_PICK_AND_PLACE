// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from moveit_task_constructor_msgs:srv/GetSolution.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__SRV__DETAIL__GET_SOLUTION__STRUCT_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__SRV__DETAIL__GET_SOLUTION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__moveit_task_constructor_msgs__srv__GetSolution_Request __attribute__((deprecated))
#else
# define DEPRECATED__moveit_task_constructor_msgs__srv__GetSolution_Request __declspec(deprecated)
#endif

namespace moveit_task_constructor_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct GetSolution_Request_
{
  using Type = GetSolution_Request_<ContainerAllocator>;

  explicit GetSolution_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->solution_id = 0ul;
    }
  }

  explicit GetSolution_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->solution_id = 0ul;
    }
  }

  // field types and members
  using _solution_id_type =
    uint32_t;
  _solution_id_type solution_id;

  // setters for named parameter idiom
  Type & set__solution_id(
    const uint32_t & _arg)
  {
    this->solution_id = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    moveit_task_constructor_msgs::srv::GetSolution_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const moveit_task_constructor_msgs::srv::GetSolution_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::srv::GetSolution_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::srv::GetSolution_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::srv::GetSolution_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::srv::GetSolution_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::srv::GetSolution_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::srv::GetSolution_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::srv::GetSolution_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::srv::GetSolution_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__moveit_task_constructor_msgs__srv__GetSolution_Request
    std::shared_ptr<moveit_task_constructor_msgs::srv::GetSolution_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__moveit_task_constructor_msgs__srv__GetSolution_Request
    std::shared_ptr<moveit_task_constructor_msgs::srv::GetSolution_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GetSolution_Request_ & other) const
  {
    if (this->solution_id != other.solution_id) {
      return false;
    }
    return true;
  }
  bool operator!=(const GetSolution_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GetSolution_Request_

// alias to use template instance with default allocator
using GetSolution_Request =
  moveit_task_constructor_msgs::srv::GetSolution_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace moveit_task_constructor_msgs


// Include directives for member types
// Member 'solution'
#include "moveit_task_constructor_msgs/msg/detail/solution__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__moveit_task_constructor_msgs__srv__GetSolution_Response __attribute__((deprecated))
#else
# define DEPRECATED__moveit_task_constructor_msgs__srv__GetSolution_Response __declspec(deprecated)
#endif

namespace moveit_task_constructor_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct GetSolution_Response_
{
  using Type = GetSolution_Response_<ContainerAllocator>;

  explicit GetSolution_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : solution(_init)
  {
    (void)_init;
  }

  explicit GetSolution_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : solution(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _solution_type =
    moveit_task_constructor_msgs::msg::Solution_<ContainerAllocator>;
  _solution_type solution;

  // setters for named parameter idiom
  Type & set__solution(
    const moveit_task_constructor_msgs::msg::Solution_<ContainerAllocator> & _arg)
  {
    this->solution = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    moveit_task_constructor_msgs::srv::GetSolution_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const moveit_task_constructor_msgs::srv::GetSolution_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::srv::GetSolution_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::srv::GetSolution_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::srv::GetSolution_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::srv::GetSolution_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::srv::GetSolution_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::srv::GetSolution_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::srv::GetSolution_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::srv::GetSolution_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__moveit_task_constructor_msgs__srv__GetSolution_Response
    std::shared_ptr<moveit_task_constructor_msgs::srv::GetSolution_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__moveit_task_constructor_msgs__srv__GetSolution_Response
    std::shared_ptr<moveit_task_constructor_msgs::srv::GetSolution_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GetSolution_Response_ & other) const
  {
    if (this->solution != other.solution) {
      return false;
    }
    return true;
  }
  bool operator!=(const GetSolution_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GetSolution_Response_

// alias to use template instance with default allocator
using GetSolution_Response =
  moveit_task_constructor_msgs::srv::GetSolution_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace moveit_task_constructor_msgs

namespace moveit_task_constructor_msgs
{

namespace srv
{

struct GetSolution
{
  using Request = moveit_task_constructor_msgs::srv::GetSolution_Request;
  using Response = moveit_task_constructor_msgs::srv::GetSolution_Response;
};

}  // namespace srv

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__SRV__DETAIL__GET_SOLUTION__STRUCT_HPP_
