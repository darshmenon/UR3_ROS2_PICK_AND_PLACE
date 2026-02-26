// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from moveit_task_constructor_msgs:msg/StageStatistics.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_STATISTICS__FUNCTIONS_H_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_STATISTICS__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "moveit_task_constructor_msgs/msg/rosidl_generator_c__visibility_control.h"

#include "moveit_task_constructor_msgs/msg/detail/stage_statistics__struct.h"

/// Initialize msg/StageStatistics message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * moveit_task_constructor_msgs__msg__StageStatistics
 * )) before or use
 * moveit_task_constructor_msgs__msg__StageStatistics__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
bool
moveit_task_constructor_msgs__msg__StageStatistics__init(moveit_task_constructor_msgs__msg__StageStatistics * msg);

/// Finalize msg/StageStatistics message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
void
moveit_task_constructor_msgs__msg__StageStatistics__fini(moveit_task_constructor_msgs__msg__StageStatistics * msg);

/// Create msg/StageStatistics message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * moveit_task_constructor_msgs__msg__StageStatistics__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
moveit_task_constructor_msgs__msg__StageStatistics *
moveit_task_constructor_msgs__msg__StageStatistics__create();

/// Destroy msg/StageStatistics message.
/**
 * It calls
 * moveit_task_constructor_msgs__msg__StageStatistics__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
void
moveit_task_constructor_msgs__msg__StageStatistics__destroy(moveit_task_constructor_msgs__msg__StageStatistics * msg);

/// Check for msg/StageStatistics message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
bool
moveit_task_constructor_msgs__msg__StageStatistics__are_equal(const moveit_task_constructor_msgs__msg__StageStatistics * lhs, const moveit_task_constructor_msgs__msg__StageStatistics * rhs);

/// Copy a msg/StageStatistics message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
bool
moveit_task_constructor_msgs__msg__StageStatistics__copy(
  const moveit_task_constructor_msgs__msg__StageStatistics * input,
  moveit_task_constructor_msgs__msg__StageStatistics * output);

/// Initialize array of msg/StageStatistics messages.
/**
 * It allocates the memory for the number of elements and calls
 * moveit_task_constructor_msgs__msg__StageStatistics__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
bool
moveit_task_constructor_msgs__msg__StageStatistics__Sequence__init(moveit_task_constructor_msgs__msg__StageStatistics__Sequence * array, size_t size);

/// Finalize array of msg/StageStatistics messages.
/**
 * It calls
 * moveit_task_constructor_msgs__msg__StageStatistics__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
void
moveit_task_constructor_msgs__msg__StageStatistics__Sequence__fini(moveit_task_constructor_msgs__msg__StageStatistics__Sequence * array);

/// Create array of msg/StageStatistics messages.
/**
 * It allocates the memory for the array and calls
 * moveit_task_constructor_msgs__msg__StageStatistics__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
moveit_task_constructor_msgs__msg__StageStatistics__Sequence *
moveit_task_constructor_msgs__msg__StageStatistics__Sequence__create(size_t size);

/// Destroy array of msg/StageStatistics messages.
/**
 * It calls
 * moveit_task_constructor_msgs__msg__StageStatistics__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
void
moveit_task_constructor_msgs__msg__StageStatistics__Sequence__destroy(moveit_task_constructor_msgs__msg__StageStatistics__Sequence * array);

/// Check for msg/StageStatistics message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
bool
moveit_task_constructor_msgs__msg__StageStatistics__Sequence__are_equal(const moveit_task_constructor_msgs__msg__StageStatistics__Sequence * lhs, const moveit_task_constructor_msgs__msg__StageStatistics__Sequence * rhs);

/// Copy an array of msg/StageStatistics messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
bool
moveit_task_constructor_msgs__msg__StageStatistics__Sequence__copy(
  const moveit_task_constructor_msgs__msg__StageStatistics__Sequence * input,
  moveit_task_constructor_msgs__msg__StageStatistics__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_STATISTICS__FUNCTIONS_H_
