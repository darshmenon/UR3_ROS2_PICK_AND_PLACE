// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from ur_interfaces:srv/GetPlanningScene.idl
// generated code does not contain a copyright notice

#ifndef UR_INTERFACES__SRV__DETAIL__GET_PLANNING_SCENE__STRUCT_H_
#define UR_INTERFACES__SRV__DETAIL__GET_PLANNING_SCENE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'target_shape'
#include "rosidl_runtime_c/string.h"
// Member 'target_dimensions'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in srv/GetPlanningScene in the package ur_interfaces.
typedef struct ur_interfaces__srv__GetPlanningScene_Request
{
  /// e.g., "box", "cylinder"
  rosidl_runtime_c__String target_shape;
  /// Approximate dimensions for identification
  rosidl_runtime_c__double__Sequence target_dimensions;
} ur_interfaces__srv__GetPlanningScene_Request;

// Struct for a sequence of ur_interfaces__srv__GetPlanningScene_Request.
typedef struct ur_interfaces__srv__GetPlanningScene_Request__Sequence
{
  ur_interfaces__srv__GetPlanningScene_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} ur_interfaces__srv__GetPlanningScene_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'scene_world'
#include "moveit_msgs/msg/detail/planning_scene_world__struct.h"
// Member 'full_cloud'
#include "sensor_msgs/msg/detail/point_cloud2__struct.h"
// Member 'rgb_image'
#include "sensor_msgs/msg/detail/image__struct.h"
// Member 'target_object_id'
// Member 'support_surface_id'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in srv/GetPlanningScene in the package ur_interfaces.
typedef struct ur_interfaces__srv__GetPlanningScene_Response
{
  /// Response
  /// Contains CollisionObjects for all detected objects
  moveit_msgs__msg__PlanningSceneWorld scene_world;
  /// Full scene point cloud
  sensor_msgs__msg__PointCloud2 full_cloud;
  /// RGB image of the scene
  sensor_msgs__msg__Image rgb_image;
  /// ID of the target object in the PlanningSceneWorld
  rosidl_runtime_c__String target_object_id;
  /// ID of the support surface in the PlanningSceneWorld
  rosidl_runtime_c__String support_surface_id;
  /// Indicates if the operation was successful
  bool success;
} ur_interfaces__srv__GetPlanningScene_Response;

// Struct for a sequence of ur_interfaces__srv__GetPlanningScene_Response.
typedef struct ur_interfaces__srv__GetPlanningScene_Response__Sequence
{
  ur_interfaces__srv__GetPlanningScene_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} ur_interfaces__srv__GetPlanningScene_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // UR_INTERFACES__SRV__DETAIL__GET_PLANNING_SCENE__STRUCT_H_
