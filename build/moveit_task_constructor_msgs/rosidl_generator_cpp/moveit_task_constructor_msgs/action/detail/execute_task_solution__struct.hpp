// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from moveit_task_constructor_msgs:action/ExecuteTaskSolution.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__ACTION__DETAIL__EXECUTE_TASK_SOLUTION__STRUCT_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__ACTION__DETAIL__EXECUTE_TASK_SOLUTION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'solution'
#include "moveit_task_constructor_msgs/msg/detail/solution__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_Goal __attribute__((deprecated))
#else
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_Goal __declspec(deprecated)
#endif

namespace moveit_task_constructor_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct ExecuteTaskSolution_Goal_
{
  using Type = ExecuteTaskSolution_Goal_<ContainerAllocator>;

  explicit ExecuteTaskSolution_Goal_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : solution(_init)
  {
    (void)_init;
  }

  explicit ExecuteTaskSolution_Goal_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
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
    moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal_<ContainerAllocator> *;
  using ConstRawPtr =
    const moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_Goal
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_Goal
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ExecuteTaskSolution_Goal_ & other) const
  {
    if (this->solution != other.solution) {
      return false;
    }
    return true;
  }
  bool operator!=(const ExecuteTaskSolution_Goal_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ExecuteTaskSolution_Goal_

// alias to use template instance with default allocator
using ExecuteTaskSolution_Goal =
  moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal_<std::allocator<void>>;

// constant definitions

}  // namespace action

}  // namespace moveit_task_constructor_msgs


// Include directives for member types
// Member 'error_code'
#include "moveit_msgs/msg/detail/move_it_error_codes__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_Result __attribute__((deprecated))
#else
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_Result __declspec(deprecated)
#endif

namespace moveit_task_constructor_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct ExecuteTaskSolution_Result_
{
  using Type = ExecuteTaskSolution_Result_<ContainerAllocator>;

  explicit ExecuteTaskSolution_Result_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : error_code(_init)
  {
    (void)_init;
  }

  explicit ExecuteTaskSolution_Result_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : error_code(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _error_code_type =
    moveit_msgs::msg::MoveItErrorCodes_<ContainerAllocator>;
  _error_code_type error_code;

  // setters for named parameter idiom
  Type & set__error_code(
    const moveit_msgs::msg::MoveItErrorCodes_<ContainerAllocator> & _arg)
  {
    this->error_code = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result_<ContainerAllocator> *;
  using ConstRawPtr =
    const moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_Result
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_Result
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ExecuteTaskSolution_Result_ & other) const
  {
    if (this->error_code != other.error_code) {
      return false;
    }
    return true;
  }
  bool operator!=(const ExecuteTaskSolution_Result_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ExecuteTaskSolution_Result_

// alias to use template instance with default allocator
using ExecuteTaskSolution_Result =
  moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result_<std::allocator<void>>;

// constant definitions

}  // namespace action

}  // namespace moveit_task_constructor_msgs


#ifndef _WIN32
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_Feedback __attribute__((deprecated))
#else
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_Feedback __declspec(deprecated)
#endif

namespace moveit_task_constructor_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct ExecuteTaskSolution_Feedback_
{
  using Type = ExecuteTaskSolution_Feedback_<ContainerAllocator>;

  explicit ExecuteTaskSolution_Feedback_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->sub_id = 0ul;
      this->sub_no = 0ul;
    }
  }

  explicit ExecuteTaskSolution_Feedback_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->sub_id = 0ul;
      this->sub_no = 0ul;
    }
  }

  // field types and members
  using _sub_id_type =
    uint32_t;
  _sub_id_type sub_id;
  using _sub_no_type =
    uint32_t;
  _sub_no_type sub_no;

  // setters for named parameter idiom
  Type & set__sub_id(
    const uint32_t & _arg)
  {
    this->sub_id = _arg;
    return *this;
  }
  Type & set__sub_no(
    const uint32_t & _arg)
  {
    this->sub_no = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback_<ContainerAllocator> *;
  using ConstRawPtr =
    const moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_Feedback
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_Feedback
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ExecuteTaskSolution_Feedback_ & other) const
  {
    if (this->sub_id != other.sub_id) {
      return false;
    }
    if (this->sub_no != other.sub_no) {
      return false;
    }
    return true;
  }
  bool operator!=(const ExecuteTaskSolution_Feedback_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ExecuteTaskSolution_Feedback_

// alias to use template instance with default allocator
using ExecuteTaskSolution_Feedback =
  moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback_<std::allocator<void>>;

// constant definitions

}  // namespace action

}  // namespace moveit_task_constructor_msgs


// Include directives for member types
// Member 'goal_id'
#include "unique_identifier_msgs/msg/detail/uuid__struct.hpp"
// Member 'goal'
#include "moveit_task_constructor_msgs/action/detail/execute_task_solution__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Request __attribute__((deprecated))
#else
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Request __declspec(deprecated)
#endif

namespace moveit_task_constructor_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct ExecuteTaskSolution_SendGoal_Request_
{
  using Type = ExecuteTaskSolution_SendGoal_Request_<ContainerAllocator>;

  explicit ExecuteTaskSolution_SendGoal_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : goal_id(_init),
    goal(_init)
  {
    (void)_init;
  }

  explicit ExecuteTaskSolution_SendGoal_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : goal_id(_alloc, _init),
    goal(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _goal_id_type =
    unique_identifier_msgs::msg::UUID_<ContainerAllocator>;
  _goal_id_type goal_id;
  using _goal_type =
    moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal_<ContainerAllocator>;
  _goal_type goal;

  // setters for named parameter idiom
  Type & set__goal_id(
    const unique_identifier_msgs::msg::UUID_<ContainerAllocator> & _arg)
  {
    this->goal_id = _arg;
    return *this;
  }
  Type & set__goal(
    const moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal_<ContainerAllocator> & _arg)
  {
    this->goal = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Request
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Request
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ExecuteTaskSolution_SendGoal_Request_ & other) const
  {
    if (this->goal_id != other.goal_id) {
      return false;
    }
    if (this->goal != other.goal) {
      return false;
    }
    return true;
  }
  bool operator!=(const ExecuteTaskSolution_SendGoal_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ExecuteTaskSolution_SendGoal_Request_

// alias to use template instance with default allocator
using ExecuteTaskSolution_SendGoal_Request =
  moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request_<std::allocator<void>>;

// constant definitions

}  // namespace action

}  // namespace moveit_task_constructor_msgs


// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Response __attribute__((deprecated))
#else
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Response __declspec(deprecated)
#endif

namespace moveit_task_constructor_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct ExecuteTaskSolution_SendGoal_Response_
{
  using Type = ExecuteTaskSolution_SendGoal_Response_<ContainerAllocator>;

  explicit ExecuteTaskSolution_SendGoal_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : stamp(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->accepted = false;
    }
  }

  explicit ExecuteTaskSolution_SendGoal_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : stamp(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->accepted = false;
    }
  }

  // field types and members
  using _accepted_type =
    bool;
  _accepted_type accepted;
  using _stamp_type =
    builtin_interfaces::msg::Time_<ContainerAllocator>;
  _stamp_type stamp;

  // setters for named parameter idiom
  Type & set__accepted(
    const bool & _arg)
  {
    this->accepted = _arg;
    return *this;
  }
  Type & set__stamp(
    const builtin_interfaces::msg::Time_<ContainerAllocator> & _arg)
  {
    this->stamp = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Response
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Response
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ExecuteTaskSolution_SendGoal_Response_ & other) const
  {
    if (this->accepted != other.accepted) {
      return false;
    }
    if (this->stamp != other.stamp) {
      return false;
    }
    return true;
  }
  bool operator!=(const ExecuteTaskSolution_SendGoal_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ExecuteTaskSolution_SendGoal_Response_

// alias to use template instance with default allocator
using ExecuteTaskSolution_SendGoal_Response =
  moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response_<std::allocator<void>>;

// constant definitions

}  // namespace action

}  // namespace moveit_task_constructor_msgs

namespace moveit_task_constructor_msgs
{

namespace action
{

struct ExecuteTaskSolution_SendGoal
{
  using Request = moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request;
  using Response = moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response;
};

}  // namespace action

}  // namespace moveit_task_constructor_msgs


// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Request __attribute__((deprecated))
#else
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Request __declspec(deprecated)
#endif

namespace moveit_task_constructor_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct ExecuteTaskSolution_GetResult_Request_
{
  using Type = ExecuteTaskSolution_GetResult_Request_<ContainerAllocator>;

  explicit ExecuteTaskSolution_GetResult_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : goal_id(_init)
  {
    (void)_init;
  }

  explicit ExecuteTaskSolution_GetResult_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : goal_id(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _goal_id_type =
    unique_identifier_msgs::msg::UUID_<ContainerAllocator>;
  _goal_id_type goal_id;

  // setters for named parameter idiom
  Type & set__goal_id(
    const unique_identifier_msgs::msg::UUID_<ContainerAllocator> & _arg)
  {
    this->goal_id = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Request
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Request
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ExecuteTaskSolution_GetResult_Request_ & other) const
  {
    if (this->goal_id != other.goal_id) {
      return false;
    }
    return true;
  }
  bool operator!=(const ExecuteTaskSolution_GetResult_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ExecuteTaskSolution_GetResult_Request_

// alias to use template instance with default allocator
using ExecuteTaskSolution_GetResult_Request =
  moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request_<std::allocator<void>>;

// constant definitions

}  // namespace action

}  // namespace moveit_task_constructor_msgs


// Include directives for member types
// Member 'result'
// already included above
// #include "moveit_task_constructor_msgs/action/detail/execute_task_solution__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Response __attribute__((deprecated))
#else
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Response __declspec(deprecated)
#endif

namespace moveit_task_constructor_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct ExecuteTaskSolution_GetResult_Response_
{
  using Type = ExecuteTaskSolution_GetResult_Response_<ContainerAllocator>;

  explicit ExecuteTaskSolution_GetResult_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : result(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->status = 0;
    }
  }

  explicit ExecuteTaskSolution_GetResult_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : result(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->status = 0;
    }
  }

  // field types and members
  using _status_type =
    int8_t;
  _status_type status;
  using _result_type =
    moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result_<ContainerAllocator>;
  _result_type result;

  // setters for named parameter idiom
  Type & set__status(
    const int8_t & _arg)
  {
    this->status = _arg;
    return *this;
  }
  Type & set__result(
    const moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result_<ContainerAllocator> & _arg)
  {
    this->result = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Response
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Response
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ExecuteTaskSolution_GetResult_Response_ & other) const
  {
    if (this->status != other.status) {
      return false;
    }
    if (this->result != other.result) {
      return false;
    }
    return true;
  }
  bool operator!=(const ExecuteTaskSolution_GetResult_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ExecuteTaskSolution_GetResult_Response_

// alias to use template instance with default allocator
using ExecuteTaskSolution_GetResult_Response =
  moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response_<std::allocator<void>>;

// constant definitions

}  // namespace action

}  // namespace moveit_task_constructor_msgs

namespace moveit_task_constructor_msgs
{

namespace action
{

struct ExecuteTaskSolution_GetResult
{
  using Request = moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request;
  using Response = moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response;
};

}  // namespace action

}  // namespace moveit_task_constructor_msgs


// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.hpp"
// Member 'feedback'
// already included above
// #include "moveit_task_constructor_msgs/action/detail/execute_task_solution__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_FeedbackMessage __attribute__((deprecated))
#else
# define DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_FeedbackMessage __declspec(deprecated)
#endif

namespace moveit_task_constructor_msgs
{

namespace action
{

// message struct
template<class ContainerAllocator>
struct ExecuteTaskSolution_FeedbackMessage_
{
  using Type = ExecuteTaskSolution_FeedbackMessage_<ContainerAllocator>;

  explicit ExecuteTaskSolution_FeedbackMessage_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : goal_id(_init),
    feedback(_init)
  {
    (void)_init;
  }

  explicit ExecuteTaskSolution_FeedbackMessage_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : goal_id(_alloc, _init),
    feedback(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _goal_id_type =
    unique_identifier_msgs::msg::UUID_<ContainerAllocator>;
  _goal_id_type goal_id;
  using _feedback_type =
    moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback_<ContainerAllocator>;
  _feedback_type feedback;

  // setters for named parameter idiom
  Type & set__goal_id(
    const unique_identifier_msgs::msg::UUID_<ContainerAllocator> & _arg)
  {
    this->goal_id = _arg;
    return *this;
  }
  Type & set__feedback(
    const moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback_<ContainerAllocator> & _arg)
  {
    this->feedback = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage_<ContainerAllocator> *;
  using ConstRawPtr =
    const moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_FeedbackMessage
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__moveit_task_constructor_msgs__action__ExecuteTaskSolution_FeedbackMessage
    std::shared_ptr<moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ExecuteTaskSolution_FeedbackMessage_ & other) const
  {
    if (this->goal_id != other.goal_id) {
      return false;
    }
    if (this->feedback != other.feedback) {
      return false;
    }
    return true;
  }
  bool operator!=(const ExecuteTaskSolution_FeedbackMessage_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ExecuteTaskSolution_FeedbackMessage_

// alias to use template instance with default allocator
using ExecuteTaskSolution_FeedbackMessage =
  moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage_<std::allocator<void>>;

// constant definitions

}  // namespace action

}  // namespace moveit_task_constructor_msgs

#include "action_msgs/srv/cancel_goal.hpp"
#include "action_msgs/msg/goal_info.hpp"
#include "action_msgs/msg/goal_status_array.hpp"

namespace moveit_task_constructor_msgs
{

namespace action
{

struct ExecuteTaskSolution
{
  /// The goal message defined in the action definition.
  using Goal = moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal;
  /// The result message defined in the action definition.
  using Result = moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result;
  /// The feedback message defined in the action definition.
  using Feedback = moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback;

  struct Impl
  {
    /// The send_goal service using a wrapped version of the goal message as a request.
    using SendGoalService = moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal;
    /// The get_result service using a wrapped version of the result message as a response.
    using GetResultService = moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult;
    /// The feedback message with generic fields which wraps the feedback message.
    using FeedbackMessage = moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage;

    /// The generic service to cancel a goal.
    using CancelGoalService = action_msgs::srv::CancelGoal;
    /// The generic message for the status of a goal.
    using GoalStatusMessage = action_msgs::msg::GoalStatusArray;
  };
};

typedef struct ExecuteTaskSolution ExecuteTaskSolution;

}  // namespace action

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__ACTION__DETAIL__EXECUTE_TASK_SOLUTION__STRUCT_HPP_
