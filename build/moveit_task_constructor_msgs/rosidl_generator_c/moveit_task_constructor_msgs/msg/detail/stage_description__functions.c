// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from moveit_task_constructor_msgs:msg/StageDescription.idl
// generated code does not contain a copyright notice
#include "moveit_task_constructor_msgs/msg/detail/stage_description__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `name`
#include "rosidl_runtime_c/string_functions.h"
// Member `properties`
#include "moveit_task_constructor_msgs/msg/detail/property__functions.h"

bool
moveit_task_constructor_msgs__msg__StageDescription__init(moveit_task_constructor_msgs__msg__StageDescription * msg)
{
  if (!msg) {
    return false;
  }
  // id
  // parent_id
  // name
  if (!rosidl_runtime_c__String__init(&msg->name)) {
    moveit_task_constructor_msgs__msg__StageDescription__fini(msg);
    return false;
  }
  // flags
  // properties
  if (!moveit_task_constructor_msgs__msg__Property__Sequence__init(&msg->properties, 0)) {
    moveit_task_constructor_msgs__msg__StageDescription__fini(msg);
    return false;
  }
  return true;
}

void
moveit_task_constructor_msgs__msg__StageDescription__fini(moveit_task_constructor_msgs__msg__StageDescription * msg)
{
  if (!msg) {
    return;
  }
  // id
  // parent_id
  // name
  rosidl_runtime_c__String__fini(&msg->name);
  // flags
  // properties
  moveit_task_constructor_msgs__msg__Property__Sequence__fini(&msg->properties);
}

bool
moveit_task_constructor_msgs__msg__StageDescription__are_equal(const moveit_task_constructor_msgs__msg__StageDescription * lhs, const moveit_task_constructor_msgs__msg__StageDescription * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // id
  if (lhs->id != rhs->id) {
    return false;
  }
  // parent_id
  if (lhs->parent_id != rhs->parent_id) {
    return false;
  }
  // name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->name), &(rhs->name)))
  {
    return false;
  }
  // flags
  if (lhs->flags != rhs->flags) {
    return false;
  }
  // properties
  if (!moveit_task_constructor_msgs__msg__Property__Sequence__are_equal(
      &(lhs->properties), &(rhs->properties)))
  {
    return false;
  }
  return true;
}

bool
moveit_task_constructor_msgs__msg__StageDescription__copy(
  const moveit_task_constructor_msgs__msg__StageDescription * input,
  moveit_task_constructor_msgs__msg__StageDescription * output)
{
  if (!input || !output) {
    return false;
  }
  // id
  output->id = input->id;
  // parent_id
  output->parent_id = input->parent_id;
  // name
  if (!rosidl_runtime_c__String__copy(
      &(input->name), &(output->name)))
  {
    return false;
  }
  // flags
  output->flags = input->flags;
  // properties
  if (!moveit_task_constructor_msgs__msg__Property__Sequence__copy(
      &(input->properties), &(output->properties)))
  {
    return false;
  }
  return true;
}

moveit_task_constructor_msgs__msg__StageDescription *
moveit_task_constructor_msgs__msg__StageDescription__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__StageDescription * msg = (moveit_task_constructor_msgs__msg__StageDescription *)allocator.allocate(sizeof(moveit_task_constructor_msgs__msg__StageDescription), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(moveit_task_constructor_msgs__msg__StageDescription));
  bool success = moveit_task_constructor_msgs__msg__StageDescription__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
moveit_task_constructor_msgs__msg__StageDescription__destroy(moveit_task_constructor_msgs__msg__StageDescription * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    moveit_task_constructor_msgs__msg__StageDescription__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
moveit_task_constructor_msgs__msg__StageDescription__Sequence__init(moveit_task_constructor_msgs__msg__StageDescription__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__StageDescription * data = NULL;

  if (size) {
    data = (moveit_task_constructor_msgs__msg__StageDescription *)allocator.zero_allocate(size, sizeof(moveit_task_constructor_msgs__msg__StageDescription), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = moveit_task_constructor_msgs__msg__StageDescription__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        moveit_task_constructor_msgs__msg__StageDescription__fini(&data[i - 1]);
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
moveit_task_constructor_msgs__msg__StageDescription__Sequence__fini(moveit_task_constructor_msgs__msg__StageDescription__Sequence * array)
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
      moveit_task_constructor_msgs__msg__StageDescription__fini(&array->data[i]);
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

moveit_task_constructor_msgs__msg__StageDescription__Sequence *
moveit_task_constructor_msgs__msg__StageDescription__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__StageDescription__Sequence * array = (moveit_task_constructor_msgs__msg__StageDescription__Sequence *)allocator.allocate(sizeof(moveit_task_constructor_msgs__msg__StageDescription__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = moveit_task_constructor_msgs__msg__StageDescription__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
moveit_task_constructor_msgs__msg__StageDescription__Sequence__destroy(moveit_task_constructor_msgs__msg__StageDescription__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    moveit_task_constructor_msgs__msg__StageDescription__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
moveit_task_constructor_msgs__msg__StageDescription__Sequence__are_equal(const moveit_task_constructor_msgs__msg__StageDescription__Sequence * lhs, const moveit_task_constructor_msgs__msg__StageDescription__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!moveit_task_constructor_msgs__msg__StageDescription__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
moveit_task_constructor_msgs__msg__StageDescription__Sequence__copy(
  const moveit_task_constructor_msgs__msg__StageDescription__Sequence * input,
  moveit_task_constructor_msgs__msg__StageDescription__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(moveit_task_constructor_msgs__msg__StageDescription);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    moveit_task_constructor_msgs__msg__StageDescription * data =
      (moveit_task_constructor_msgs__msg__StageDescription *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!moveit_task_constructor_msgs__msg__StageDescription__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          moveit_task_constructor_msgs__msg__StageDescription__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!moveit_task_constructor_msgs__msg__StageDescription__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
