// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from moveit_task_constructor_msgs:action/ExecuteTaskSolution.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__ACTION__DETAIL__EXECUTE_TASK_SOLUTION__STRUCT_H_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__ACTION__DETAIL__EXECUTE_TASK_SOLUTION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'solution'
#include "moveit_task_constructor_msgs/msg/detail/solution__struct.h"

/// Struct defined in action/ExecuteTaskSolution in the package moveit_task_constructor_msgs.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_Goal
{
  moveit_task_constructor_msgs__msg__Solution solution;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_Goal;

// Struct for a sequence of moveit_task_constructor_msgs__action__ExecuteTaskSolution_Goal.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_Goal__Sequence
{
  moveit_task_constructor_msgs__action__ExecuteTaskSolution_Goal * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_Goal__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'error_code'
#include "moveit_msgs/msg/detail/move_it_error_codes__struct.h"

/// Struct defined in action/ExecuteTaskSolution in the package moveit_task_constructor_msgs.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_Result
{
  /// result of execution
  moveit_msgs__msg__MoveItErrorCodes error_code;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_Result;

// Struct for a sequence of moveit_task_constructor_msgs__action__ExecuteTaskSolution_Result.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_Result__Sequence
{
  moveit_task_constructor_msgs__action__ExecuteTaskSolution_Result * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_Result__Sequence;


// Constants defined in the message

/// Struct defined in action/ExecuteTaskSolution in the package moveit_task_constructor_msgs.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_Feedback
{
  /// finished subtrajectory id / number
  uint32_t sub_id;
  uint32_t sub_no;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_Feedback;

// Struct for a sequence of moveit_task_constructor_msgs__action__ExecuteTaskSolution_Feedback.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_Feedback__Sequence
{
  moveit_task_constructor_msgs__action__ExecuteTaskSolution_Feedback * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_Feedback__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
#include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'goal'
#include "moveit_task_constructor_msgs/action/detail/execute_task_solution__struct.h"

/// Struct defined in action/ExecuteTaskSolution in the package moveit_task_constructor_msgs.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
  moveit_task_constructor_msgs__action__ExecuteTaskSolution_Goal goal;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Request;

// Struct for a sequence of moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Request.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Request__Sequence
{
  moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in action/ExecuteTaskSolution in the package moveit_task_constructor_msgs.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Response
{
  bool accepted;
  builtin_interfaces__msg__Time stamp;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Response;

// Struct for a sequence of moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Response.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Response__Sequence
{
  moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_SendGoal_Response__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"

/// Struct defined in action/ExecuteTaskSolution in the package moveit_task_constructor_msgs.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Request;

// Struct for a sequence of moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Request.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Request__Sequence
{
  moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'result'
// already included above
// #include "moveit_task_constructor_msgs/action/detail/execute_task_solution__struct.h"

/// Struct defined in action/ExecuteTaskSolution in the package moveit_task_constructor_msgs.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Response
{
  int8_t status;
  moveit_task_constructor_msgs__action__ExecuteTaskSolution_Result result;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Response;

// Struct for a sequence of moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Response.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Response__Sequence
{
  moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_GetResult_Response__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'feedback'
// already included above
// #include "moveit_task_constructor_msgs/action/detail/execute_task_solution__struct.h"

/// Struct defined in action/ExecuteTaskSolution in the package moveit_task_constructor_msgs.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_FeedbackMessage
{
  unique_identifier_msgs__msg__UUID goal_id;
  moveit_task_constructor_msgs__action__ExecuteTaskSolution_Feedback feedback;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_FeedbackMessage;

// Struct for a sequence of moveit_task_constructor_msgs__action__ExecuteTaskSolution_FeedbackMessage.
typedef struct moveit_task_constructor_msgs__action__ExecuteTaskSolution_FeedbackMessage__Sequence
{
  moveit_task_constructor_msgs__action__ExecuteTaskSolution_FeedbackMessage * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} moveit_task_constructor_msgs__action__ExecuteTaskSolution_FeedbackMessage__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__ACTION__DETAIL__EXECUTE_TASK_SOLUTION__STRUCT_H_
