// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from moveit_task_constructor_msgs:msg/Solution.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION__STRUCT_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'start_scene'
#include "moveit_msgs/msg/detail/planning_scene__struct.hpp"
// Member 'sub_solution'
#include "moveit_task_constructor_msgs/msg/detail/sub_solution__struct.hpp"
// Member 'sub_trajectory'
#include "moveit_task_constructor_msgs/msg/detail/sub_trajectory__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__moveit_task_constructor_msgs__msg__Solution __attribute__((deprecated))
#else
# define DEPRECATED__moveit_task_constructor_msgs__msg__Solution __declspec(deprecated)
#endif

namespace moveit_task_constructor_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct Solution_
{
  using Type = Solution_<ContainerAllocator>;

  explicit Solution_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : start_scene(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->task_id = "";
    }
  }

  explicit Solution_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : task_id(_alloc),
    start_scene(_alloc, _init)
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
  using _start_scene_type =
    moveit_msgs::msg::PlanningScene_<ContainerAllocator>;
  _start_scene_type start_scene;
  using _sub_solution_type =
    std::vector<moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator>>>;
  _sub_solution_type sub_solution;
  using _sub_trajectory_type =
    std::vector<moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator>>>;
  _sub_trajectory_type sub_trajectory;

  // setters for named parameter idiom
  Type & set__task_id(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->task_id = _arg;
    return *this;
  }
  Type & set__start_scene(
    const moveit_msgs::msg::PlanningScene_<ContainerAllocator> & _arg)
  {
    this->start_scene = _arg;
    return *this;
  }
  Type & set__sub_solution(
    const std::vector<moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<moveit_task_constructor_msgs::msg::SubSolution_<ContainerAllocator>>> & _arg)
  {
    this->sub_solution = _arg;
    return *this;
  }
  Type & set__sub_trajectory(
    const std::vector<moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator>>> & _arg)
  {
    this->sub_trajectory = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    moveit_task_constructor_msgs::msg::Solution_<ContainerAllocator> *;
  using ConstRawPtr =
    const moveit_task_constructor_msgs::msg::Solution_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::msg::Solution_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::msg::Solution_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::msg::Solution_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::msg::Solution_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::msg::Solution_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::msg::Solution_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::msg::Solution_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::msg::Solution_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__moveit_task_constructor_msgs__msg__Solution
    std::shared_ptr<moveit_task_constructor_msgs::msg::Solution_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__moveit_task_constructor_msgs__msg__Solution
    std::shared_ptr<moveit_task_constructor_msgs::msg::Solution_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const Solution_ & other) const
  {
    if (this->task_id != other.task_id) {
      return false;
    }
    if (this->start_scene != other.start_scene) {
      return false;
    }
    if (this->sub_solution != other.sub_solution) {
      return false;
    }
    if (this->sub_trajectory != other.sub_trajectory) {
      return false;
    }
    return true;
  }
  bool operator!=(const Solution_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct Solution_

// alias to use template instance with default allocator
using Solution =
  moveit_task_constructor_msgs::msg::Solution_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SOLUTION__STRUCT_HPP_
