// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from moveit_task_constructor_msgs:msg/StageStatistics.idl
// generated code does not contain a copyright notice
#include "moveit_task_constructor_msgs/msg/detail/stage_statistics__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `solved`
// Member `failed`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

bool
moveit_task_constructor_msgs__msg__StageStatistics__init(moveit_task_constructor_msgs__msg__StageStatistics * msg)
{
  if (!msg) {
    return false;
  }
  // id
  // solved
  if (!rosidl_runtime_c__uint32__Sequence__init(&msg->solved, 0)) {
    moveit_task_constructor_msgs__msg__StageStatistics__fini(msg);
    return false;
  }
  // failed
  if (!rosidl_runtime_c__uint32__Sequence__init(&msg->failed, 0)) {
    moveit_task_constructor_msgs__msg__StageStatistics__fini(msg);
    return false;
  }
  // num_failed
  // total_compute_time
  return true;
}

void
moveit_task_constructor_msgs__msg__StageStatistics__fini(moveit_task_constructor_msgs__msg__StageStatistics * msg)
{
  if (!msg) {
    return;
  }
  // id
  // solved
  rosidl_runtime_c__uint32__Sequence__fini(&msg->solved);
  // failed
  rosidl_runtime_c__uint32__Sequence__fini(&msg->failed);
  // num_failed
  // total_compute_time
}

bool
moveit_task_constructor_msgs__msg__StageStatistics__are_equal(const moveit_task_constructor_msgs__msg__StageStatistics * lhs, const moveit_task_constructor_msgs__msg__StageStatistics * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // id
  if (lhs->id != rhs->id) {
    return false;
  }
  // solved
  if (!rosidl_runtime_c__uint32__Sequence__are_equal(
      &(lhs->solved), &(rhs->solved)))
  {
    return false;
  }
  // failed
  if (!rosidl_runtime_c__uint32__Sequence__are_equal(
      &(lhs->failed), &(rhs->failed)))
  {
    return false;
  }
  // num_failed
  if (lhs->num_failed != rhs->num_failed) {
    return false;
  }
  // total_compute_time
  if (lhs->total_compute_time != rhs->total_compute_time) {
    return false;
  }
  return true;
}

bool
moveit_task_constructor_msgs__msg__StageStatistics__copy(
  const moveit_task_constructor_msgs__msg__StageStatistics * input,
  moveit_task_constructor_msgs__msg__StageStatistics * output)
{
  if (!input || !output) {
    return false;
  }
  // id
  output->id = input->id;
  // solved
  if (!rosidl_runtime_c__uint32__Sequence__copy(
      &(input->solved), &(output->solved)))
  {
    return false;
  }
  // failed
  if (!rosidl_runtime_c__uint32__Sequence__copy(
      &(input->failed), &(output->failed)))
  {
    return false;
  }
  // num_failed
  output->num_failed = input->num_failed;
  // total_compute_time
  output->total_compute_time = input->total_compute_time;
  return true;
}

moveit_task_constructor_msgs__msg__StageStatistics *
moveit_task_constructor_msgs__msg__StageStatistics__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__StageStatistics * msg = (moveit_task_constructor_msgs__msg__StageStatistics *)allocator.allocate(sizeof(moveit_task_constructor_msgs__msg__StageStatistics), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(moveit_task_constructor_msgs__msg__StageStatistics));
  bool success = moveit_task_constructor_msgs__msg__StageStatistics__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
moveit_task_constructor_msgs__msg__StageStatistics__destroy(moveit_task_constructor_msgs__msg__StageStatistics * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    moveit_task_constructor_msgs__msg__StageStatistics__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
moveit_task_constructor_msgs__msg__StageStatistics__Sequence__init(moveit_task_constructor_msgs__msg__StageStatistics__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__StageStatistics * data = NULL;

  if (size) {
    data = (moveit_task_constructor_msgs__msg__StageStatistics *)allocator.zero_allocate(size, sizeof(moveit_task_constructor_msgs__msg__StageStatistics), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = moveit_task_constructor_msgs__msg__StageStatistics__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        moveit_task_constructor_msgs__msg__StageStatistics__fini(&data[i - 1]);
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
moveit_task_constructor_msgs__msg__StageStatistics__Sequence__fini(moveit_task_constructor_msgs__msg__StageStatistics__Sequence * array)
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
      moveit_task_constructor_msgs__msg__StageStatistics__fini(&array->data[i]);
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

moveit_task_constructor_msgs__msg__StageStatistics__Sequence *
moveit_task_constructor_msgs__msg__StageStatistics__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__StageStatistics__Sequence * array = (moveit_task_constructor_msgs__msg__StageStatistics__Sequence *)allocator.allocate(sizeof(moveit_task_constructor_msgs__msg__StageStatistics__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = moveit_task_constructor_msgs__msg__StageStatistics__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
moveit_task_constructor_msgs__msg__StageStatistics__Sequence__destroy(moveit_task_constructor_msgs__msg__StageStatistics__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    moveit_task_constructor_msgs__msg__StageStatistics__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
moveit_task_constructor_msgs__msg__StageStatistics__Sequence__are_equal(const moveit_task_constructor_msgs__msg__StageStatistics__Sequence * lhs, const moveit_task_constructor_msgs__msg__StageStatistics__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!moveit_task_constructor_msgs__msg__StageStatistics__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
moveit_task_constructor_msgs__msg__StageStatistics__Sequence__copy(
  const moveit_task_constructor_msgs__msg__StageStatistics__Sequence * input,
  moveit_task_constructor_msgs__msg__StageStatistics__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(moveit_task_constructor_msgs__msg__StageStatistics);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    moveit_task_constructor_msgs__msg__StageStatistics * data =
      (moveit_task_constructor_msgs__msg__StageStatistics *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!moveit_task_constructor_msgs__msg__StageStatistics__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          moveit_task_constructor_msgs__msg__StageStatistics__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!moveit_task_constructor_msgs__msg__StageStatistics__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
