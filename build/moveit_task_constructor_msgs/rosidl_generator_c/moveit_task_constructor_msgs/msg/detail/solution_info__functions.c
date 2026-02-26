// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from moveit_task_constructor_msgs:msg/SolutionInfo.idl
// generated code does not contain a copyright notice
#include "moveit_task_constructor_msgs/msg/detail/solution_info__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `comment`
// Member `planner_id`
#include "rosidl_runtime_c/string_functions.h"
// Member `markers`
#include "visualization_msgs/msg/detail/marker__functions.h"

bool
moveit_task_constructor_msgs__msg__SolutionInfo__init(moveit_task_constructor_msgs__msg__SolutionInfo * msg)
{
  if (!msg) {
    return false;
  }
  // id
  // cost
  // comment
  if (!rosidl_runtime_c__String__init(&msg->comment)) {
    moveit_task_constructor_msgs__msg__SolutionInfo__fini(msg);
    return false;
  }
  // stage_id
  // planner_id
  if (!rosidl_runtime_c__String__init(&msg->planner_id)) {
    moveit_task_constructor_msgs__msg__SolutionInfo__fini(msg);
    return false;
  }
  // markers
  if (!visualization_msgs__msg__Marker__Sequence__init(&msg->markers, 0)) {
    moveit_task_constructor_msgs__msg__SolutionInfo__fini(msg);
    return false;
  }
  return true;
}

void
moveit_task_constructor_msgs__msg__SolutionInfo__fini(moveit_task_constructor_msgs__msg__SolutionInfo * msg)
{
  if (!msg) {
    return;
  }
  // id
  // cost
  // comment
  rosidl_runtime_c__String__fini(&msg->comment);
  // stage_id
  // planner_id
  rosidl_runtime_c__String__fini(&msg->planner_id);
  // markers
  visualization_msgs__msg__Marker__Sequence__fini(&msg->markers);
}

bool
moveit_task_constructor_msgs__msg__SolutionInfo__are_equal(const moveit_task_constructor_msgs__msg__SolutionInfo * lhs, const moveit_task_constructor_msgs__msg__SolutionInfo * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // id
  if (lhs->id != rhs->id) {
    return false;
  }
  // cost
  if (lhs->cost != rhs->cost) {
    return false;
  }
  // comment
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->comment), &(rhs->comment)))
  {
    return false;
  }
  // stage_id
  if (lhs->stage_id != rhs->stage_id) {
    return false;
  }
  // planner_id
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->planner_id), &(rhs->planner_id)))
  {
    return false;
  }
  // markers
  if (!visualization_msgs__msg__Marker__Sequence__are_equal(
      &(lhs->markers), &(rhs->markers)))
  {
    return false;
  }
  return true;
}

bool
moveit_task_constructor_msgs__msg__SolutionInfo__copy(
  const moveit_task_constructor_msgs__msg__SolutionInfo * input,
  moveit_task_constructor_msgs__msg__SolutionInfo * output)
{
  if (!input || !output) {
    return false;
  }
  // id
  output->id = input->id;
  // cost
  output->cost = input->cost;
  // comment
  if (!rosidl_runtime_c__String__copy(
      &(input->comment), &(output->comment)))
  {
    return false;
  }
  // stage_id
  output->stage_id = input->stage_id;
  // planner_id
  if (!rosidl_runtime_c__String__copy(
      &(input->planner_id), &(output->planner_id)))
  {
    return false;
  }
  // markers
  if (!visualization_msgs__msg__Marker__Sequence__copy(
      &(input->markers), &(output->markers)))
  {
    return false;
  }
  return true;
}

moveit_task_constructor_msgs__msg__SolutionInfo *
moveit_task_constructor_msgs__msg__SolutionInfo__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__SolutionInfo * msg = (moveit_task_constructor_msgs__msg__SolutionInfo *)allocator.allocate(sizeof(moveit_task_constructor_msgs__msg__SolutionInfo), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(moveit_task_constructor_msgs__msg__SolutionInfo));
  bool success = moveit_task_constructor_msgs__msg__SolutionInfo__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
moveit_task_constructor_msgs__msg__SolutionInfo__destroy(moveit_task_constructor_msgs__msg__SolutionInfo * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    moveit_task_constructor_msgs__msg__SolutionInfo__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
moveit_task_constructor_msgs__msg__SolutionInfo__Sequence__init(moveit_task_constructor_msgs__msg__SolutionInfo__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__SolutionInfo * data = NULL;

  if (size) {
    data = (moveit_task_constructor_msgs__msg__SolutionInfo *)allocator.zero_allocate(size, sizeof(moveit_task_constructor_msgs__msg__SolutionInfo), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = moveit_task_constructor_msgs__msg__SolutionInfo__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        moveit_task_constructor_msgs__msg__SolutionInfo__fini(&data[i - 1]);
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
moveit_task_constructor_msgs__msg__SolutionInfo__Sequence__fini(moveit_task_constructor_msgs__msg__SolutionInfo__Sequence * array)
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
      moveit_task_constructor_msgs__msg__SolutionInfo__fini(&array->data[i]);
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

moveit_task_constructor_msgs__msg__SolutionInfo__Sequence *
moveit_task_constructor_msgs__msg__SolutionInfo__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__SolutionInfo__Sequence * array = (moveit_task_constructor_msgs__msg__SolutionInfo__Sequence *)allocator.allocate(sizeof(moveit_task_constructor_msgs__msg__SolutionInfo__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = moveit_task_constructor_msgs__msg__SolutionInfo__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
moveit_task_constructor_msgs__msg__SolutionInfo__Sequence__destroy(moveit_task_constructor_msgs__msg__SolutionInfo__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    moveit_task_constructor_msgs__msg__SolutionInfo__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
moveit_task_constructor_msgs__msg__SolutionInfo__Sequence__are_equal(const moveit_task_constructor_msgs__msg__SolutionInfo__Sequence * lhs, const moveit_task_constructor_msgs__msg__SolutionInfo__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!moveit_task_constructor_msgs__msg__SolutionInfo__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
moveit_task_constructor_msgs__msg__SolutionInfo__Sequence__copy(
  const moveit_task_constructor_msgs__msg__SolutionInfo__Sequence * input,
  moveit_task_constructor_msgs__msg__SolutionInfo__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(moveit_task_constructor_msgs__msg__SolutionInfo);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    moveit_task_constructor_msgs__msg__SolutionInfo * data =
      (moveit_task_constructor_msgs__msg__SolutionInfo *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!moveit_task_constructor_msgs__msg__SolutionInfo__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          moveit_task_constructor_msgs__msg__SolutionInfo__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!moveit_task_constructor_msgs__msg__SolutionInfo__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
