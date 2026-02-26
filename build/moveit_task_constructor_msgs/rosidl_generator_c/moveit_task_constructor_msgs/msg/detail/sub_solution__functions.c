// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from moveit_task_constructor_msgs:msg/SubSolution.idl
// generated code does not contain a copyright notice
#include "moveit_task_constructor_msgs/msg/detail/sub_solution__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `info`
#include "moveit_task_constructor_msgs/msg/detail/solution_info__functions.h"
// Member `sub_solution_id`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

bool
moveit_task_constructor_msgs__msg__SubSolution__init(moveit_task_constructor_msgs__msg__SubSolution * msg)
{
  if (!msg) {
    return false;
  }
  // info
  if (!moveit_task_constructor_msgs__msg__SolutionInfo__init(&msg->info)) {
    moveit_task_constructor_msgs__msg__SubSolution__fini(msg);
    return false;
  }
  // sub_solution_id
  if (!rosidl_runtime_c__uint32__Sequence__init(&msg->sub_solution_id, 0)) {
    moveit_task_constructor_msgs__msg__SubSolution__fini(msg);
    return false;
  }
  return true;
}

void
moveit_task_constructor_msgs__msg__SubSolution__fini(moveit_task_constructor_msgs__msg__SubSolution * msg)
{
  if (!msg) {
    return;
  }
  // info
  moveit_task_constructor_msgs__msg__SolutionInfo__fini(&msg->info);
  // sub_solution_id
  rosidl_runtime_c__uint32__Sequence__fini(&msg->sub_solution_id);
}

bool
moveit_task_constructor_msgs__msg__SubSolution__are_equal(const moveit_task_constructor_msgs__msg__SubSolution * lhs, const moveit_task_constructor_msgs__msg__SubSolution * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // info
  if (!moveit_task_constructor_msgs__msg__SolutionInfo__are_equal(
      &(lhs->info), &(rhs->info)))
  {
    return false;
  }
  // sub_solution_id
  if (!rosidl_runtime_c__uint32__Sequence__are_equal(
      &(lhs->sub_solution_id), &(rhs->sub_solution_id)))
  {
    return false;
  }
  return true;
}

bool
moveit_task_constructor_msgs__msg__SubSolution__copy(
  const moveit_task_constructor_msgs__msg__SubSolution * input,
  moveit_task_constructor_msgs__msg__SubSolution * output)
{
  if (!input || !output) {
    return false;
  }
  // info
  if (!moveit_task_constructor_msgs__msg__SolutionInfo__copy(
      &(input->info), &(output->info)))
  {
    return false;
  }
  // sub_solution_id
  if (!rosidl_runtime_c__uint32__Sequence__copy(
      &(input->sub_solution_id), &(output->sub_solution_id)))
  {
    return false;
  }
  return true;
}

moveit_task_constructor_msgs__msg__SubSolution *
moveit_task_constructor_msgs__msg__SubSolution__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__SubSolution * msg = (moveit_task_constructor_msgs__msg__SubSolution *)allocator.allocate(sizeof(moveit_task_constructor_msgs__msg__SubSolution), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(moveit_task_constructor_msgs__msg__SubSolution));
  bool success = moveit_task_constructor_msgs__msg__SubSolution__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
moveit_task_constructor_msgs__msg__SubSolution__destroy(moveit_task_constructor_msgs__msg__SubSolution * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    moveit_task_constructor_msgs__msg__SubSolution__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
moveit_task_constructor_msgs__msg__SubSolution__Sequence__init(moveit_task_constructor_msgs__msg__SubSolution__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__SubSolution * data = NULL;

  if (size) {
    data = (moveit_task_constructor_msgs__msg__SubSolution *)allocator.zero_allocate(size, sizeof(moveit_task_constructor_msgs__msg__SubSolution), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = moveit_task_constructor_msgs__msg__SubSolution__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        moveit_task_constructor_msgs__msg__SubSolution__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
moveit_task_constructor_msgs__msg__SubSolution__Sequence__fini(moveit_task_constructor_msgs__msg__SubSolution__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      moveit_task_constructor_msgs__msg__SubSolution__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

moveit_task_constructor_msgs__msg__SubSolution__Sequence *
moveit_task_constructor_msgs__msg__SubSolution__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__SubSolution__Sequence * array = (moveit_task_constructor_msgs__msg__SubSolution__Sequence *)allocator.allocate(sizeof(moveit_task_constructor_msgs__msg__SubSolution__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = moveit_task_constructor_msgs__msg__SubSolution__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
moveit_task_constructor_msgs__msg__SubSolution__Sequence__destroy(moveit_task_constructor_msgs__msg__SubSolution__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    moveit_task_constructor_msgs__msg__SubSolution__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
moveit_task_constructor_msgs__msg__SubSolution__Sequence__are_equal(const moveit_task_constructor_msgs__msg__SubSolution__Sequence * lhs, const moveit_task_constructor_msgs__msg__SubSolution__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!moveit_task_constructor_msgs__msg__SubSolution__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
moveit_task_constructor_msgs__msg__SubSolution__Sequence__copy(
  const moveit_task_constructor_msgs__msg__SubSolution__Sequence * input,
  moveit_task_constructor_msgs__msg__SubSolution__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(moveit_task_constructor_msgs__msg__SubSolution);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    moveit_task_constructor_msgs__msg__SubSolution * data =
      (moveit_task_constructor_msgs__msg__SubSolution *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!moveit_task_constructor_msgs__msg__SubSolution__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          moveit_task_constructor_msgs__msg__SubSolution__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!moveit_task_constructor_msgs__msg__SubSolution__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
