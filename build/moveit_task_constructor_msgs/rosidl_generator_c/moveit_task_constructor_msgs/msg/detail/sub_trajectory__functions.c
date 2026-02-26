// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from moveit_task_constructor_msgs:msg/SubTrajectory.idl
// generated code does not contain a copyright notice
#include "moveit_task_constructor_msgs/msg/detail/sub_trajectory__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `info`
#include "moveit_task_constructor_msgs/msg/detail/solution_info__functions.h"
// Member `execution_info`
#include "moveit_task_constructor_msgs/msg/detail/trajectory_execution_info__functions.h"
// Member `trajectory`
#include "moveit_msgs/msg/detail/robot_trajectory__functions.h"
// Member `scene_diff`
#include "moveit_msgs/msg/detail/planning_scene__functions.h"

bool
moveit_task_constructor_msgs__msg__SubTrajectory__init(moveit_task_constructor_msgs__msg__SubTrajectory * msg)
{
  if (!msg) {
    return false;
  }
  // info
  if (!moveit_task_constructor_msgs__msg__SolutionInfo__init(&msg->info)) {
    moveit_task_constructor_msgs__msg__SubTrajectory__fini(msg);
    return false;
  }
  // execution_info
  if (!moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__init(&msg->execution_info)) {
    moveit_task_constructor_msgs__msg__SubTrajectory__fini(msg);
    return false;
  }
  // trajectory
  if (!moveit_msgs__msg__RobotTrajectory__init(&msg->trajectory)) {
    moveit_task_constructor_msgs__msg__SubTrajectory__fini(msg);
    return false;
  }
  // scene_diff
  if (!moveit_msgs__msg__PlanningScene__init(&msg->scene_diff)) {
    moveit_task_constructor_msgs__msg__SubTrajectory__fini(msg);
    return false;
  }
  return true;
}

void
moveit_task_constructor_msgs__msg__SubTrajectory__fini(moveit_task_constructor_msgs__msg__SubTrajectory * msg)
{
  if (!msg) {
    return;
  }
  // info
  moveit_task_constructor_msgs__msg__SolutionInfo__fini(&msg->info);
  // execution_info
  moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__fini(&msg->execution_info);
  // trajectory
  moveit_msgs__msg__RobotTrajectory__fini(&msg->trajectory);
  // scene_diff
  moveit_msgs__msg__PlanningScene__fini(&msg->scene_diff);
}

bool
moveit_task_constructor_msgs__msg__SubTrajectory__are_equal(const moveit_task_constructor_msgs__msg__SubTrajectory * lhs, const moveit_task_constructor_msgs__msg__SubTrajectory * rhs)
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
  // execution_info
  if (!moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__are_equal(
      &(lhs->execution_info), &(rhs->execution_info)))
  {
    return false;
  }
  // trajectory
  if (!moveit_msgs__msg__RobotTrajectory__are_equal(
      &(lhs->trajectory), &(rhs->trajectory)))
  {
    return false;
  }
  // scene_diff
  if (!moveit_msgs__msg__PlanningScene__are_equal(
      &(lhs->scene_diff), &(rhs->scene_diff)))
  {
    return false;
  }
  return true;
}

bool
moveit_task_constructor_msgs__msg__SubTrajectory__copy(
  const moveit_task_constructor_msgs__msg__SubTrajectory * input,
  moveit_task_constructor_msgs__msg__SubTrajectory * output)
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
  // execution_info
  if (!moveit_task_constructor_msgs__msg__TrajectoryExecutionInfo__copy(
      &(input->execution_info), &(output->execution_info)))
  {
    return false;
  }
  // trajectory
  if (!moveit_msgs__msg__RobotTrajectory__copy(
      &(input->trajectory), &(output->trajectory)))
  {
    return false;
  }
  // scene_diff
  if (!moveit_msgs__msg__PlanningScene__copy(
      &(input->scene_diff), &(output->scene_diff)))
  {
    return false;
  }
  return true;
}

moveit_task_constructor_msgs__msg__SubTrajectory *
moveit_task_constructor_msgs__msg__SubTrajectory__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__SubTrajectory * msg = (moveit_task_constructor_msgs__msg__SubTrajectory *)allocator.allocate(sizeof(moveit_task_constructor_msgs__msg__SubTrajectory), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(moveit_task_constructor_msgs__msg__SubTrajectory));
  bool success = moveit_task_constructor_msgs__msg__SubTrajectory__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
moveit_task_constructor_msgs__msg__SubTrajectory__destroy(moveit_task_constructor_msgs__msg__SubTrajectory * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    moveit_task_constructor_msgs__msg__SubTrajectory__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
moveit_task_constructor_msgs__msg__SubTrajectory__Sequence__init(moveit_task_constructor_msgs__msg__SubTrajectory__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__SubTrajectory * data = NULL;

  if (size) {
    data = (moveit_task_constructor_msgs__msg__SubTrajectory *)allocator.zero_allocate(size, sizeof(moveit_task_constructor_msgs__msg__SubTrajectory), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = moveit_task_constructor_msgs__msg__SubTrajectory__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        moveit_task_constructor_msgs__msg__SubTrajectory__fini(&data[i - 1]);
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
moveit_task_constructor_msgs__msg__SubTrajectory__Sequence__fini(moveit_task_constructor_msgs__msg__SubTrajectory__Sequence * array)
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
      moveit_task_constructor_msgs__msg__SubTrajectory__fini(&array->data[i]);
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

moveit_task_constructor_msgs__msg__SubTrajectory__Sequence *
moveit_task_constructor_msgs__msg__SubTrajectory__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  moveit_task_constructor_msgs__msg__SubTrajectory__Sequence * array = (moveit_task_constructor_msgs__msg__SubTrajectory__Sequence *)allocator.allocate(sizeof(moveit_task_constructor_msgs__msg__SubTrajectory__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = moveit_task_constructor_msgs__msg__SubTrajectory__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
moveit_task_constructor_msgs__msg__SubTrajectory__Sequence__destroy(moveit_task_constructor_msgs__msg__SubTrajectory__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    moveit_task_constructor_msgs__msg__SubTrajectory__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
moveit_task_constructor_msgs__msg__SubTrajectory__Sequence__are_equal(const moveit_task_constructor_msgs__msg__SubTrajectory__Sequence * lhs, const moveit_task_constructor_msgs__msg__SubTrajectory__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!moveit_task_constructor_msgs__msg__SubTrajectory__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
moveit_task_constructor_msgs__msg__SubTrajectory__Sequence__copy(
  const moveit_task_constructor_msgs__msg__SubTrajectory__Sequence * input,
  moveit_task_constructor_msgs__msg__SubTrajectory__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(moveit_task_constructor_msgs__msg__SubTrajectory);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    moveit_task_constructor_msgs__msg__SubTrajectory * data =
      (moveit_task_constructor_msgs__msg__SubTrajectory *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!moveit_task_constructor_msgs__msg__SubTrajectory__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          moveit_task_constructor_msgs__msg__SubTrajectory__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!moveit_task_constructor_msgs__msg__SubTrajectory__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
