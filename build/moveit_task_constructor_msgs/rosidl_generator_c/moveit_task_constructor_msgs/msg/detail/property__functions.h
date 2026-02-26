// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from moveit_task_constructor_msgs:msg/Property.idl
// generated code does not contain a copyright notice

#ifndef MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__PROPERTY__FUNCTIONS_H_
#define MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__PROPERTY__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "moveit_task_constructor_msgs/msg/rosidl_generator_c__visibility_control.h"

#include "moveit_task_constructor_msgs/msg/detail/property__struct.h"

/// Initialize msg/Property message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * moveit_task_constructor_msgs__msg__Property
 * )) before or use
 * moveit_task_constructor_msgs__msg__Property__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
bool
moveit_task_constructor_msgs__msg__Property__init(moveit_task_constructor_msgs__msg__Property * msg);

/// Finalize msg/Property message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
void
moveit_task_constructor_msgs__msg__Property__fini(moveit_task_constructor_msgs__msg__Property * msg);

/// Create msg/Property message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * moveit_task_constructor_msgs__msg__Property__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
moveit_task_constructor_msgs__msg__Property *
moveit_task_constructor_msgs__msg__Property__create();

/// Destroy msg/Property message.
/**
 * It calls
 * moveit_task_constructor_msgs__msg__Property__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
void
moveit_task_constructor_msgs__msg__Property__destroy(moveit_task_constructor_msgs__msg__Property * msg);

/// Check for msg/Property message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
bool
moveit_task_constructor_msgs__msg__Property__are_equal(const moveit_task_constructor_msgs__msg__Property * lhs, const moveit_task_constructor_msgs__msg__Property * rhs);

/// Copy a msg/Property message.
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
moveit_task_constructor_msgs__msg__Property__copy(
  const moveit_task_constructor_msgs__msg__Property * input,
  moveit_task_constructor_msgs__msg__Property * output);

/// Initialize array of msg/Property messages.
/**
 * It allocates the memory for the number of elements and calls
 * moveit_task_constructor_msgs__msg__Property__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
bool
moveit_task_constructor_msgs__msg__Property__Sequence__init(moveit_task_constructor_msgs__msg__Property__Sequence * array, size_t size);

/// Finalize array of msg/Property messages.
/**
 * It calls
 * moveit_task_constructor_msgs__msg__Property__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
void
moveit_task_constructor_msgs__msg__Property__Sequence__fini(moveit_task_constructor_msgs__msg__Property__Sequence * array);

/// Create array of msg/Property messages.
/**
 * It allocates the memory for the array and calls
 * moveit_task_constructor_msgs__msg__Property__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
moveit_task_constructor_msgs__msg__Property__Sequence *
moveit_task_constructor_msgs__msg__Property__Sequence__create(size_t size);

/// Destroy array of msg/Property messages.
/**
 * It calls
 * moveit_task_constructor_msgs__msg__Property__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
void
moveit_task_constructor_msgs__msg__Property__Sequence__destroy(moveit_task_constructor_msgs__msg__Property__Sequence * array);

/// Check for msg/Property message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_moveit_task_constructor_msgs
bool
moveit_task_constructor_msgs__msg__Property__Sequence__are_equal(const moveit_task_constructor_msgs__msg__Property__Sequence * lhs, const moveit_task_constructor_msgs__msg__Property__Sequence * rhs);

/// Copy an array of msg/Property messages.
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
moveit_task_constructor_msgs__msg__Property__Sequence__copy(
  const moveit_task_constructor_msgs__msg__Property__Sequence * input,
  moveit_task_constructor_msgs__msg__Property__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // MOVEIT_TASK_CONSTRUCTOR_MSGS__MSG__DETAIL__PROPERTY__FUNCTIONS_H_
