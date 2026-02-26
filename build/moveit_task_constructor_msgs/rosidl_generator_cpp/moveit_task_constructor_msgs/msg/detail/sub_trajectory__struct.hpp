// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from moveit_task_constructor_msgs:msg/SubTrajectory.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_TRAJECTORY__STRUCT_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_TRAJECTORY__STRUCT_HPP_

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
// Member 'execution_info'
#include "moveit_task_constructor_msgs/msg/detail/trajectory_execution_info__struct.hpp"
// Member 'trajectory'
#include "moveit_msgs/msg/detail/robot_trajectory__struct.hpp"
// Member 'scene_diff'
#include "moveit_msgs/msg/detail/planning_scene__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__moveit_task_constructor_msgs__msg__SubTrajectory __attribute__((deprecated))
#else
# define DEPRECATED__moveit_task_constructor_msgs__msg__SubTrajectory __declspec(deprecated)
#endif

namespace moveit_task_constructor_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct SubTrajectory_
{
  using Type = SubTrajectory_<ContainerAllocator>;

  explicit SubTrajectory_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_init),
    execution_info(_init),
    trajectory(_init),
    scene_diff(_init)
  {
    (void)_init;
  }

  explicit SubTrajectory_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : info(_alloc, _init),
    execution_info(_alloc, _init),
    trajectory(_alloc, _init),
    scene_diff(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _info_type =
    moveit_task_constructor_msgs::msg::SolutionInfo_<ContainerAllocator>;
  _info_type info;
  using _execution_info_type =
    moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo_<ContainerAllocator>;
  _execution_info_type execution_info;
  using _trajectory_type =
    moveit_msgs::msg::RobotTrajectory_<ContainerAllocator>;
  _trajectory_type trajectory;
  using _scene_diff_type =
    moveit_msgs::msg::PlanningScene_<ContainerAllocator>;
  _scene_diff_type scene_diff;

  // setters for named parameter idiom
  Type & set__info(
    const moveit_task_constructor_msgs::msg::SolutionInfo_<ContainerAllocator> & _arg)
  {
    this->info = _arg;
    return *this;
  }
  Type & set__execution_info(
    const moveit_task_constructor_msgs::msg::TrajectoryExecutionInfo_<ContainerAllocator> & _arg)
  {
    this->execution_info = _arg;
    return *this;
  }
  Type & set__trajectory(
    const moveit_msgs::msg::RobotTrajectory_<ContainerAllocator> & _arg)
  {
    this->trajectory = _arg;
    return *this;
  }
  Type & set__scene_diff(
    const moveit_msgs::msg::PlanningScene_<ContainerAllocator> & _arg)
  {
    this->scene_diff = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator> *;
  using ConstRawPtr =
    const moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__moveit_task_constructor_msgs__msg__SubTrajectory
    std::shared_ptr<moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__moveit_task_constructor_msgs__msg__SubTrajectory
    std::shared_ptr<moveit_task_constructor_msgs::msg::SubTrajectory_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const SubTrajectory_ & other) const
  {
    if (this->info != other.info) {
      return false;
    }
    if (this->execution_info != other.execution_info) {
      return false;
    }
    if (this->trajectory != other.trajectory) {
      return false;
    }
    if (this->scene_diff != other.scene_diff) {
      return false;
    }
    return true;
  }
  bool operator!=(const SubTrajectory_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct SubTrajectory_

// alias to use template instance with default allocator
using SubTrajectory =
  moveit_task_constructor_msgs::msg::SubTrajectory_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__SUB_TRAJECTORY__STRUCT_HPP_
