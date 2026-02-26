// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from moveit_task_constructor_msgs:action/ExecuteTaskSolution.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__ACTION__DETAIL__EXECUTE_TASK_SOLUTION__BUILDER_HPP_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__ACTION__DETAIL__EXECUTE_TASK_SOLUTION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "moveit_task_constructor_msgs/action/detail/execute_task_solution__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace moveit_task_constructor_msgs
{

namespace action
{

namespace builder
{

class Init_ExecuteTaskSolution_Goal_solution
{
public:
  Init_ExecuteTaskSolution_Goal_solution()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal solution(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal::_solution_type arg)
  {
    msg_.solution = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::action::ExecuteTaskSolution_Goal>()
{
  return moveit_task_constructor_msgs::action::builder::Init_ExecuteTaskSolution_Goal_solution();
}

}  // namespace moveit_task_constructor_msgs


namespace moveit_task_constructor_msgs
{

namespace action
{

namespace builder
{

class Init_ExecuteTaskSolution_Result_error_code
{
public:
  Init_ExecuteTaskSolution_Result_error_code()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result error_code(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result::_error_code_type arg)
  {
    msg_.error_code = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::action::ExecuteTaskSolution_Result>()
{
  return moveit_task_constructor_msgs::action::builder::Init_ExecuteTaskSolution_Result_error_code();
}

}  // namespace moveit_task_constructor_msgs


namespace moveit_task_constructor_msgs
{

namespace action
{

namespace builder
{

class Init_ExecuteTaskSolution_Feedback_sub_no
{
public:
  explicit Init_ExecuteTaskSolution_Feedback_sub_no(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback & msg)
  : msg_(msg)
  {}
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback sub_no(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback::_sub_no_type arg)
  {
    msg_.sub_no = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback msg_;
};

class Init_ExecuteTaskSolution_Feedback_sub_id
{
public:
  Init_ExecuteTaskSolution_Feedback_sub_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ExecuteTaskSolution_Feedback_sub_no sub_id(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback::_sub_id_type arg)
  {
    msg_.sub_id = std::move(arg);
    return Init_ExecuteTaskSolution_Feedback_sub_no(msg_);
  }

private:
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::action::ExecuteTaskSolution_Feedback>()
{
  return moveit_task_constructor_msgs::action::builder::Init_ExecuteTaskSolution_Feedback_sub_id();
}

}  // namespace moveit_task_constructor_msgs


namespace moveit_task_constructor_msgs
{

namespace action
{

namespace builder
{

class Init_ExecuteTaskSolution_SendGoal_Request_goal
{
public:
  explicit Init_ExecuteTaskSolution_SendGoal_Request_goal(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request & msg)
  : msg_(msg)
  {}
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request goal(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request::_goal_type arg)
  {
    msg_.goal = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request msg_;
};

class Init_ExecuteTaskSolution_SendGoal_Request_goal_id
{
public:
  Init_ExecuteTaskSolution_SendGoal_Request_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ExecuteTaskSolution_SendGoal_Request_goal goal_id(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return Init_ExecuteTaskSolution_SendGoal_Request_goal(msg_);
  }

private:
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Request>()
{
  return moveit_task_constructor_msgs::action::builder::Init_ExecuteTaskSolution_SendGoal_Request_goal_id();
}

}  // namespace moveit_task_constructor_msgs


namespace moveit_task_constructor_msgs
{

namespace action
{

namespace builder
{

class Init_ExecuteTaskSolution_SendGoal_Response_stamp
{
public:
  explicit Init_ExecuteTaskSolution_SendGoal_Response_stamp(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response & msg)
  : msg_(msg)
  {}
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response stamp(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response::_stamp_type arg)
  {
    msg_.stamp = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response msg_;
};

class Init_ExecuteTaskSolution_SendGoal_Response_accepted
{
public:
  Init_ExecuteTaskSolution_SendGoal_Response_accepted()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ExecuteTaskSolution_SendGoal_Response_stamp accepted(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response::_accepted_type arg)
  {
    msg_.accepted = std::move(arg);
    return Init_ExecuteTaskSolution_SendGoal_Response_stamp(msg_);
  }

private:
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::action::ExecuteTaskSolution_SendGoal_Response>()
{
  return moveit_task_constructor_msgs::action::builder::Init_ExecuteTaskSolution_SendGoal_Response_accepted();
}

}  // namespace moveit_task_constructor_msgs


namespace moveit_task_constructor_msgs
{

namespace action
{

namespace builder
{

class Init_ExecuteTaskSolution_GetResult_Request_goal_id
{
public:
  Init_ExecuteTaskSolution_GetResult_Request_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request goal_id(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Request>()
{
  return moveit_task_constructor_msgs::action::builder::Init_ExecuteTaskSolution_GetResult_Request_goal_id();
}

}  // namespace moveit_task_constructor_msgs


namespace moveit_task_constructor_msgs
{

namespace action
{

namespace builder
{

class Init_ExecuteTaskSolution_GetResult_Response_result
{
public:
  explicit Init_ExecuteTaskSolution_GetResult_Response_result(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response & msg)
  : msg_(msg)
  {}
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response result(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response::_result_type arg)
  {
    msg_.result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response msg_;
};

class Init_ExecuteTaskSolution_GetResult_Response_status
{
public:
  Init_ExecuteTaskSolution_GetResult_Response_status()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ExecuteTaskSolution_GetResult_Response_result status(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_ExecuteTaskSolution_GetResult_Response_result(msg_);
  }

private:
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::action::ExecuteTaskSolution_GetResult_Response>()
{
  return moveit_task_constructor_msgs::action::builder::Init_ExecuteTaskSolution_GetResult_Response_status();
}

}  // namespace moveit_task_constructor_msgs


namespace moveit_task_constructor_msgs
{

namespace action
{

namespace builder
{

class Init_ExecuteTaskSolution_FeedbackMessage_feedback
{
public:
  explicit Init_ExecuteTaskSolution_FeedbackMessage_feedback(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage & msg)
  : msg_(msg)
  {}
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage feedback(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage::_feedback_type arg)
  {
    msg_.feedback = std::move(arg);
    return std::move(msg_);
  }

private:
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage msg_;
};

class Init_ExecuteTaskSolution_FeedbackMessage_goal_id
{
public:
  Init_ExecuteTaskSolution_FeedbackMessage_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ExecuteTaskSolution_FeedbackMessage_feedback goal_id(::moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return Init_ExecuteTaskSolution_FeedbackMessage_feedback(msg_);
  }

private:
  ::moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::moveit_task_constructor_msgs::action::ExecuteTaskSolution_FeedbackMessage>()
{
  return moveit_task_constructor_msgs::action::builder::Init_ExecuteTaskSolution_FeedbackMessage_goal_id();
}

}  // namespace moveit_task_constructor_msgs

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__ACTION__DETAIL__EXECUTE_TASK_SOLUTION__BUILDER_HPP_
