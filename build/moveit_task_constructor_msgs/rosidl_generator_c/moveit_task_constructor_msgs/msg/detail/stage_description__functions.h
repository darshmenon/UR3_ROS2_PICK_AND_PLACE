// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from moveit_task_constructor_msgs:msg/StageDescription.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_DESCRIPTION__FUNCTIONS_H_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_DESCRIPTION__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "moveit_task_constructor_msgs/msg/rosidl_generator_c__visibility_control.h"

#include "moveit_task_constructor_msgs/msg/detail/stage_description__struct.h"

/// Initialize msg/StageDescription message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * moveit_task_constructor_msgs__msg__StageDescription
 * )) before or use
 * moveit_task_constructor_msgs__msg__StageDescription__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
bool
moveit_task_constructor_msgs__msg__StageDescription__init(moveit_task_constructor_msgs__msg__StageDescription * msg);

/// Finalize msg/StageDescription message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
void
moveit_task_constructor_msgs__msg__StageDescription__fini(moveit_task_constructor_msgs__msg__StageDescription * msg);

/// Create msg/StageDescription message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * moveit_task_constructor_msgs__msg__StageDescription__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
moveit_task_constructor_msgs__msg__StageDescription *
moveit_task_constructor_msgs__msg__StageDescription__create();

/// Destroy msg/StageDescription message.
/**
 * It calls
 * moveit_task_constructor_msgs__msg__StageDescription__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
void
moveit_task_constructor_msgs__msg__StageDescription__destroy(moveit_task_constructor_msgs__msg__StageDescription * msg);

/// Check for msg/StageDescription message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
bool
moveit_task_constructor_msgs__msg__StageDescription__are_equal(const moveit_task_constructor_msgs__msg__StageDescription * lhs, const moveit_task_constructor_msgs__msg__StageDescription * rhs);

/// Copy a msg/StageDescription message.
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
moveit_task_constructor_msgs__msg__StageDescription__copy(
  const moveit_task_constructor_msgs__msg__StageDescription * input,
  moveit_task_constructor_msgs__msg__StageDescription * output);

/// Initialize array of msg/StageDescription messages.
/**
 * It allocates the memory for the number of elements and calls
 * moveit_task_constructor_msgs__msg__StageDescription__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
bool
moveit_task_constructor_msgs__msg__StageDescription__Sequence__init(moveit_task_constructor_msgs__msg__StageDescription__Sequence * array, size_t size);

/// Finalize array of msg/StageDescription messages.
/**
 * It calls
 * moveit_task_constructor_msgs__msg__StageDescription__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
void
moveit_task_constructor_msgs__msg__StageDescription__Sequence__fini(moveit_task_constructor_msgs__msg__StageDescription__Sequence * array);

/// Create array of msg/StageDescription messages.
/**
 * It allocates the memory for the array and calls
 * moveit_task_constructor_msgs__msg__StageDescription__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
moveit_task_constructor_msgs__msg__StageDescription__Sequence *
moveit_task_constructor_msgs__msg__StageDescription__Sequence__create(size_t size);

/// Destroy array of msg/StageDescription messages.
/**
 * It calls
 * moveit_task_constructor_msgs__msg__StageDescription__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
void
moveit_task_constructor_msgs__msg__StageDescription__Sequence__destroy(moveit_task_constructor_msgs__msg__StageDescription__Sequence * array);

/// Check for msg/StageDescription message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
bool
moveit_task_constructor_msgs__msg__StageDescription__Sequence__are_equal(const moveit_task_constructor_msgs__msg__StageDescription__Sequence * lhs, const moveit_task_constructor_msgs__msg__StageDescription__Sequence * rhs);

/// Copy an array of msg/StageDescription messages.
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
moveit_task_constructor_msgs__msg__StageDescription__Sequence__copy(
  const moveit_task_constructor_msgs__msg__StageDescription__Sequence * input,
  moveit_task_constructor_msgs__msg__StageDescription__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__STAGE_DESCRIPTION__FUNCTIONS_H_
