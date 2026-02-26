// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from ur_interfaces:srv/GetPlanningScene.idl
// generated code does not contain a copyright notice
#include "ur_interfaces/srv/detail/get_planning_scene__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

// Include directives for member types
// Member `target_shape`
#include "rosidl_runtime_c/string_functions.h"
// Member `target_dimensions`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

bool
ur_interfaces__srv__GetPlanningScene_Request__init(ur_interfaces__srv__GetPlanningScene_Request * msg)
{
  if (!msg) {
    return false;
  }
  // target_shape
  if (!rosidl_runtime_c__String__init(&msg->target_shape)) {
    ur_interfaces__srv__GetPlanningScene_Request__fini(msg);
    return false;
  }
  // target_dimensions
  if (!rosidl_runtime_c__double__Sequence__init(&msg->target_dimensions, 0)) {
    ur_interfaces__srv__GetPlanningScene_Request__fini(msg);
    return false;
  }
  return true;
}

void
ur_interfaces__srv__GetPlanningScene_Request__fini(ur_interfaces__srv__GetPlanningScene_Request * msg)
{
  if (!msg) {
    return;
  }
  // target_shape
  rosidl_runtime_c__String__fini(&msg->target_shape);
  // target_dimensions
  rosidl_runtime_c__double__Sequence__fini(&msg->target_dimensions);
}

bool
ur_interfaces__srv__GetPlanningScene_Request__are_equal(const ur_interfaces__srv__GetPlanningScene_Request * lhs, const ur_interfaces__srv__GetPlanningScene_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // target_shape
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->target_shape), &(rhs->target_shape)))
  {
    return false;
  }
  // target_dimensions
  if (!rosidl_runtime_c__double__Sequence__are_equal(
      &(lhs->target_dimensions), &(rhs->target_dimensions)))
  {
    return false;
  }
  return true;
}

bool
ur_interfaces__srv__GetPlanningScene_Request__copy(
  const ur_interfaces__srv__GetPlanningScene_Request * input,
  ur_interfaces__srv__GetPlanningScene_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // target_shape
  if (!rosidl_runtime_c__String__copy(
      &(input->target_shape), &(output->target_shape)))
  {
    return false;
  }
  // target_dimensions
  if (!rosidl_runtime_c__double__Sequence__copy(
      &(input->target_dimensions), &(output->target_dimensions)))
  {
    return false;
  }
  return true;
}

ur_interfaces__srv__GetPlanningScene_Request *
ur_interfaces__srv__GetPlanningScene_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ur_interfaces__srv__GetPlanningScene_Request * msg = (ur_interfaces__srv__GetPlanningScene_Request *)allocator.allocate(sizeof(ur_interfaces__srv__GetPlanningScene_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(ur_interfaces__srv__GetPlanningScene_Request));
  bool success = ur_interfaces__srv__GetPlanningScene_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
ur_interfaces__srv__GetPlanningScene_Request__destroy(ur_interfaces__srv__GetPlanningScene_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    ur_interfaces__srv__GetPlanningScene_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
ur_interfaces__srv__GetPlanningScene_Request__Sequence__init(ur_interfaces__srv__GetPlanningScene_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ur_interfaces__srv__GetPlanningScene_Request * data = NULL;

  if (size) {
    data = (ur_interfaces__srv__GetPlanningScene_Request *)allocator.zero_allocate(size, sizeof(ur_interfaces__srv__GetPlanningScene_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = ur_interfaces__srv__GetPlanningScene_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        ur_interfaces__srv__GetPlanningScene_Request__fini(&data[i - 1]);
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
ur_interfaces__srv__GetPlanningScene_Request__Sequence__fini(ur_interfaces__srv__GetPlanningScene_Request__Sequence * array)
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
      ur_interfaces__srv__GetPlanningScene_Request__fini(&array->data[i]);
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

ur_interfaces__srv__GetPlanningScene_Request__Sequence *
ur_interfaces__srv__GetPlanningScene_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ur_interfaces__srv__GetPlanningScene_Request__Sequence * array = (ur_interfaces__srv__GetPlanningScene_Request__Sequence *)allocator.allocate(sizeof(ur_interfaces__srv__GetPlanningScene_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = ur_interfaces__srv__GetPlanningScene_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
ur_interfaces__srv__GetPlanningScene_Request__Sequence__destroy(ur_interfaces__srv__GetPlanningScene_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    ur_interfaces__srv__GetPlanningScene_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
ur_interfaces__srv__GetPlanningScene_Request__Sequence__are_equal(const ur_interfaces__srv__GetPlanningScene_Request__Sequence * lhs, const ur_interfaces__srv__GetPlanningScene_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!ur_interfaces__srv__GetPlanningScene_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
ur_interfaces__srv__GetPlanningScene_Request__Sequence__copy(
  const ur_interfaces__srv__GetPlanningScene_Request__Sequence * input,
  ur_interfaces__srv__GetPlanningScene_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(ur_interfaces__srv__GetPlanningScene_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    ur_interfaces__srv__GetPlanningScene_Request * data =
      (ur_interfaces__srv__GetPlanningScene_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!ur_interfaces__srv__GetPlanningScene_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          ur_interfaces__srv__GetPlanningScene_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!ur_interfaces__srv__GetPlanningScene_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `scene_world`
#include "moveit_msgs/msg/detail/planning_scene_world__functions.h"
// Member `full_cloud`
#include "sensor_msgs/msg/detail/point_cloud2__functions.h"
// Member `rgb_image`
#include "sensor_msgs/msg/detail/image__functions.h"
// Member `target_object_id`
// Member `support_surface_id`
// already included above
// #include "rosidl_runtime_c/string_functions.h"

bool
ur_interfaces__srv__GetPlanningScene_Response__init(ur_interfaces__srv__GetPlanningScene_Response * msg)
{
  if (!msg) {
    return false;
  }
  // scene_world
  if (!moveit_msgs__msg__PlanningSceneWorld__init(&msg->scene_world)) {
    ur_interfaces__srv__GetPlanningScene_Response__fini(msg);
    return false;
  }
  // full_cloud
  if (!sensor_msgs__msg__PointCloud2__init(&msg->full_cloud)) {
    ur_interfaces__srv__GetPlanningScene_Response__fini(msg);
    return false;
  }
  // rgb_image
  if (!sensor_msgs__msg__Image__init(&msg->rgb_image)) {
    ur_interfaces__srv__GetPlanningScene_Response__fini(msg);
    return false;
  }
  // target_object_id
  if (!rosidl_runtime_c__String__init(&msg->target_object_id)) {
    ur_interfaces__srv__GetPlanningScene_Response__fini(msg);
    return false;
  }
  // support_surface_id
  if (!rosidl_runtime_c__String__init(&msg->support_surface_id)) {
    ur_interfaces__srv__GetPlanningScene_Response__fini(msg);
    return false;
  }
  // success
  return true;
}

void
ur_interfaces__srv__GetPlanningScene_Response__fini(ur_interfaces__srv__GetPlanningScene_Response * msg)
{
  if (!msg) {
    return;
  }
  // scene_world
  moveit_msgs__msg__PlanningSceneWorld__fini(&msg->scene_world);
  // full_cloud
  sensor_msgs__msg__PointCloud2__fini(&msg->full_cloud);
  // rgb_image
  sensor_msgs__msg__Image__fini(&msg->rgb_image);
  // target_object_id
  rosidl_runtime_c__String__fini(&msg->target_object_id);
  // support_surface_id
  rosidl_runtime_c__String__fini(&msg->support_surface_id);
  // success
}

bool
ur_interfaces__srv__GetPlanningScene_Response__are_equal(const ur_interfaces__srv__GetPlanningScene_Response * lhs, const ur_interfaces__srv__GetPlanningScene_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // scene_world
  if (!moveit_msgs__msg__PlanningSceneWorld__are_equal(
      &(lhs->scene_world), &(rhs->scene_world)))
  {
    return false;
  }
  // full_cloud
  if (!sensor_msgs__msg__PointCloud2__are_equal(
      &(lhs->full_cloud), &(rhs->full_cloud)))
  {
    return false;
  }
  // rgb_image
  if (!sensor_msgs__msg__Image__are_equal(
      &(lhs->rgb_image), &(rhs->rgb_image)))
  {
    return false;
  }
  // target_object_id
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->target_object_id), &(rhs->target_object_id)))
  {
    return false;
  }
  // support_surface_id
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->support_surface_id), &(rhs->support_surface_id)))
  {
    return false;
  }
  // success
  if (lhs->success != rhs->success) {
    return false;
  }
  return true;
}

bool
ur_interfaces__srv__GetPlanningScene_Response__copy(
  const ur_interfaces__srv__GetPlanningScene_Response * input,
  ur_interfaces__srv__GetPlanningScene_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // scene_world
  if (!moveit_msgs__msg__PlanningSceneWorld__copy(
      &(input->scene_world), &(output->scene_world)))
  {
    return false;
  }
  // full_cloud
  if (!sensor_msgs__msg__PointCloud2__copy(
      &(input->full_cloud), &(output->full_cloud)))
  {
    return false;
  }
  // rgb_image
  if (!sensor_msgs__msg__Image__copy(
      &(input->rgb_image), &(output->rgb_image)))
  {
    return false;
  }
  // target_object_id
  if (!rosidl_runtime_c__String__copy(
      &(input->target_object_id), &(output->target_object_id)))
  {
    return false;
  }
  // support_surface_id
  if (!rosidl_runtime_c__String__copy(
      &(input->support_surface_id), &(output->support_surface_id)))
  {
    return false;
  }
  // success
  output->success = input->success;
  return true;
}

ur_interfaces__srv__GetPlanningScene_Response *
ur_interfaces__srv__GetPlanningScene_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ur_interfaces__srv__GetPlanningScene_Response * msg = (ur_interfaces__srv__GetPlanningScene_Response *)allocator.allocate(sizeof(ur_interfaces__srv__GetPlanningScene_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(ur_interfaces__srv__GetPlanningScene_Response));
  bool success = ur_interfaces__srv__GetPlanningScene_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
ur_interfaces__srv__GetPlanningScene_Response__destroy(ur_interfaces__srv__GetPlanningScene_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    ur_interfaces__srv__GetPlanningScene_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
ur_interfaces__srv__GetPlanningScene_Response__Sequence__init(ur_interfaces__srv__GetPlanningScene_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ur_interfaces__srv__GetPlanningScene_Response * data = NULL;

  if (size) {
    data = (ur_interfaces__srv__GetPlanningScene_Response *)allocator.zero_allocate(size, sizeof(ur_interfaces__srv__GetPlanningScene_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = ur_interfaces__srv__GetPlanningScene_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        ur_interfaces__srv__GetPlanningScene_Response__fini(&data[i - 1]);
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
ur_interfaces__srv__GetPlanningScene_Response__Sequence__fini(ur_interfaces__srv__GetPlanningScene_Response__Sequence * array)
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
      ur_interfaces__srv__GetPlanningScene_Response__fini(&array->data[i]);
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

ur_interfaces__srv__GetPlanningScene_Response__Sequence *
ur_interfaces__srv__GetPlanningScene_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  ur_interfaces__srv__GetPlanningScene_Response__Sequence * array = (ur_interfaces__srv__GetPlanningScene_Response__Sequence *)allocator.allocate(sizeof(ur_interfaces__srv__GetPlanningScene_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = ur_interfaces__srv__GetPlanningScene_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
ur_interfaces__srv__GetPlanningScene_Response__Sequence__destroy(ur_interfaces__srv__GetPlanningScene_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    ur_interfaces__srv__GetPlanningScene_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
ur_interfaces__srv__GetPlanningScene_Response__Sequence__are_equal(const ur_interfaces__srv__GetPlanningScene_Response__Sequence * lhs, const ur_interfaces__srv__GetPlanningScene_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!ur_interfaces__srv__GetPlanningScene_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
ur_interfaces__srv__GetPlanningScene_Response__Sequence__copy(
  const ur_interfaces__srv__GetPlanningScene_Response__Sequence * input,
  ur_interfaces__srv__GetPlanningScene_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(ur_interfaces__srv__GetPlanningScene_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    ur_interfaces__srv__GetPlanningScene_Response * data =
      (ur_interfaces__srv__GetPlanningScene_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!ur_interfaces__srv__GetPlanningScene_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          ur_interfaces__srv__GetPlanningScene_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!ur_interfaces__srv__GetPlanningScene_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
