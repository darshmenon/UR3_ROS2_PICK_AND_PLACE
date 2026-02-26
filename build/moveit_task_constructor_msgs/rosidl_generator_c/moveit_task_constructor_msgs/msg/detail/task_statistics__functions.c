// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from moveit_task_constructor_msgs:msg/TaskStatistics.idl
// generated code does not contain a copyright notice
#include "moveit_task_constructor_msgs/msg/detail/task_statistics__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `task_id`
#include "rosidl_runtime_c/string_functions.h"
// Member `stages`
#include "moveit_task_constructor_msgs/msg/detail/stage_statistics__functions.h"

bool
moveit_task_constructor_msgs__msg__TaskStatistics__init(moveit_task_constructor_msgs__msg__TaskStatistics * msg)
{
  if (!msg) {
    return false;
  }
  // task_id
  if (!rosidl_runtime_c__String__init(&msg->task_id)) {
    moveit_task_constructor_msgs__msg__TaskStatistics__fini(msg);
    return false;
  }
  // stages
  if (!moveit_task_constructor_msgs__msg__StageStatistics__Sequence__init(&msg->stages, 0)) {
    moveit_task_constructor_msgs__msg__TaskStatistics__fini(msg);
    return false;
  }
  return true;
}

void
moveit_task_constructor_msgs__msg__TaskStatistics__fini(moveit_task_constructor_msgs__msg__TaskStatistics * msg)
{
  if (!msg) {
    return;
  }
  // task_id
  rosidl_runtime_c__String__fini(&msg->task_id);
  // stages
  moveit_task_constructor_msgs__msg__StageStatistics__Sequence__fini(&msg->stages);
}

bool
moveit_task_constructor_msgs__msg__TaskStatistics__are_equal(const moveit_task_constructor_msgs__msg__TaskStatistics * lhs, const moveit_task_constructor_msgs__msg__TaskStatistics * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // task_id
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->task_id), &(rhs->task_id)))
  {
    return false;
  }
  // stages
  if (!moveit_task_constructor_msgs__msg__StageStatistics__Sequence__are_equal(
      &(lhs->stages), &(rhs->stages)))
  {
    return false;
  }
  return true;
}

bool
moveit_task_constructor_msgs__msg__TaskStatistics__copy(
  const moveit_task_constructor_msgs__msg__TaskStatistics * input,
  moveit_task_constructor_msgs__msg__TaskStatistics * output)
{
  if (!input || !output) {
    return false;
  }
  // task_id
  if (!rosidl_runtime_c__String__copy(
      &(input->task_id), &(output->task_id)))
  {
    return false;
  }
  // stages
  if (!moveit_task_constructor_msgs__msg__StageStatistics__Sequence__copy(
      &(input->stages), &(output->stages)))
  {
    return false;
  }
  return true;
}

moveit_task_constructor_msgs__msg__TaskStatistics *
moveit_task_constructor_msgs__msg__TaskStatistics__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__TaskStatistics * msg = (moveit_task_constructor_msgs__msg__TaskStatistics *)allocator.allocate(sizeof(moveit_task_constructor_msgs__msg__TaskStatistics), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(moveit_task_constructor_msgs__msg__TaskStatistics));
  bool success = moveit_task_constructor_msgs__msg__TaskStatistics__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
moveit_task_constructor_msgs__msg__TaskStatistics__destroy(moveit_task_constructor_msgs__msg__TaskStatistics * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    moveit_task_constructor_msgs__msg__TaskStatistics__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
moveit_task_constructor_msgs__msg__TaskStatistics__Sequence__init(moveit_task_constructor_msgs__msg__TaskStatistics__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__TaskStatistics * data = NULL;

  if (size) {
    data = (moveit_task_constructor_msgs__msg__TaskStatistics *)allocator.zero_allocate(size, sizeof(moveit_task_constructor_msgs__msg__TaskStatistics), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = moveit_task_constructor_msgs__msg__TaskStatistics__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        moveit_task_constructor_msgs__msg__TaskStatistics__fini(&data[i - 1]);
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
moveit_task_constructor_msgs__msg__TaskStatistics__Sequence__fini(moveit_task_constructor_msgs__msg__TaskStatistics__Sequence * array)
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
      moveit_task_constructor_msgs__msg__TaskStatistics__fini(&array->data[i]);
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

moveit_task_constructor_msgs__msg__TaskStatistics__Sequence *
moveit_task_constructor_msgs__msg__TaskStatistics__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__TaskStatistics__Sequence * array = (moveit_task_constructor_msgs__msg__TaskStatistics__Sequence *)allocator.allocate(sizeof(moveit_task_constructor_msgs__msg__TaskStatistics__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = moveit_task_constructor_msgs__msg__TaskStatistics__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
moveit_task_constructor_msgs__msg__TaskStatistics__Sequence__destroy(moveit_task_constructor_msgs__msg__TaskStatistics__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    moveit_task_constructor_msgs__msg__TaskStatistics__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
moveit_task_constructor_msgs__msg__TaskStatistics__Sequence__are_equal(const moveit_task_constructor_msgs__msg__TaskStatistics__Sequence * lhs, const moveit_task_constructor_msgs__msg__TaskStatistics__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!moveit_task_constructor_msgs__msg__TaskStatistics__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
moveit_task_constructor_msgs__msg__TaskStatistics__Sequence__copy(
  const moveit_task_constructor_msgs__msg__TaskStatistics__Sequence * input,
  moveit_task_constructor_msgs__msg__TaskStatistics__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(moveit_task_constructor_msgs__msg__TaskStatistics);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    moveit_task_constructor_msgs__msg__TaskStatistics * data =
      (moveit_task_constructor_msgs__msg__TaskStatistics *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!moveit_task_constructor_msgs__msg__TaskStatistics__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          moveit_task_constructor_msgs__msg__TaskStatistics__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!moveit_task_constructor_msgs__msg__TaskStatistics__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
