// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from ur_interfaces:srv/GetPlanningScene.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "ur_interfaces/srv/detail/get_planning_scene__rosidl_typesupport_introspection_c.h"
#include "ur_interfaces/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "ur_interfaces/srv/detail/get_planning_scene__functions.h"
#include "ur_interfaces/srv/detail/get_planning_scene__struct.h"


// Include directives for member types
// Member `target_shape`
#include "rosidl_runtime_c/string_functions.h"
// Member `target_dimensions`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__GetPlanningScene_Request_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  ur_interfaces__srv__GetPlanningScene_Request__init(message_memory);
}

void ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__GetPlanningScene_Request_fini_function(void * message_memory)
{
  ur_interfaces__srv__GetPlanningScene_Request__fini(message_memory);
}

size_t ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__size_function__GetPlanningScene_Request__target_dimensions(
  const void * untyped_member)
{
  const rosidl_runtime_c__double__Sequence * member =
    (const rosidl_runtime_c__double__Sequence *)(untyped_member);
  return member->size;
}

const void * ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__get_const_function__GetPlanningScene_Request__target_dimensions(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__double__Sequence * member =
    (const rosidl_runtime_c__double__Sequence *)(untyped_member);
  return &member->data[index];
}

void * ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__get_function__GetPlanningScene_Request__target_dimensions(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__double__Sequence * member =
    (rosidl_runtime_c__double__Sequence *)(untyped_member);
  return &member->data[index];
}

void ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__fetch_function__GetPlanningScene_Request__target_dimensions(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const double * item =
    ((const double *)
    ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__get_const_function__GetPlanningScene_Request__target_dimensions(untyped_member, index));
  double * value =
    (double *)(untyped_value);
  *value = *item;
}

void ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__assign_function__GetPlanningScene_Request__target_dimensions(
  void * untyped_member, size_t index, const void * untyped_value)
{
  double * item =
    ((double *)
    ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__get_function__GetPlanningScene_Request__target_dimensions(untyped_member, index));
  const double * value =
    (const double *)(untyped_value);
  *item = *value;
}

bool ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__resize_function__GetPlanningScene_Request__target_dimensions(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__double__Sequence * member =
    (rosidl_runtime_c__double__Sequence *)(untyped_member);
  rosidl_runtime_c__double__Sequence__fini(member);
  return rosidl_runtime_c__double__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__GetPlanningScene_Request_message_member_array[2] = {
  {
    "target_shape",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ur_interfaces__srv__GetPlanningScene_Request, target_shape),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "target_dimensions",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ur_interfaces__srv__GetPlanningScene_Request, target_dimensions),  // bytes offset in struct
    NULL,  // default value
    ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__size_function__GetPlanningScene_Request__target_dimensions,  // size() function pointer
    ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__get_const_function__GetPlanningScene_Request__target_dimensions,  // get_const(index) function pointer
    ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__get_function__GetPlanningScene_Request__target_dimensions,  // get(index) function pointer
    ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__fetch_function__GetPlanningScene_Request__target_dimensions,  // fetch(index, &value) function pointer
    ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__assign_function__GetPlanningScene_Request__target_dimensions,  // assign(index, value) function pointer
    ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__resize_function__GetPlanningScene_Request__target_dimensions  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__GetPlanningScene_Request_message_members = {
  "ur_interfaces__srv",  // message namespace
  "GetPlanningScene_Request",  // message name
  2,  // number of fields
  sizeof(ur_interfaces__srv__GetPlanningScene_Request),
  ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__GetPlanningScene_Request_message_member_array,  // message members
  ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__GetPlanningScene_Request_init_function,  // function to initialize message memory (memory has to be allocated)
  ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__GetPlanningScene_Request_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__GetPlanningScene_Request_message_type_support_handle = {
  0,
  &ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__GetPlanningScene_Request_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_ur_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, ur_interfaces, srv, GetPlanningScene_Request)() {
  if (!ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__GetPlanningScene_Request_message_type_support_handle.typesupport_identifier) {
    ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__GetPlanningScene_Request_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &ur_interfaces__srv__GetPlanningScene_Request__rosidl_typesupport_introspection_c__GetPlanningScene_Request_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

// already included above
// #include <stddef.h>
// already included above
// #include "ur_interfaces/srv/detail/get_planning_scene__rosidl_typesupport_introspection_c.h"
// already included above
// #include "ur_interfaces/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "rosidl_typesupport_introspection_c/field_types.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
// already included above
// #include "rosidl_typesupport_introspection_c/message_introspection.h"
// already included above
// #include "ur_interfaces/srv/detail/get_planning_scene__functions.h"
// already included above
// #include "ur_interfaces/srv/detail/get_planning_scene__struct.h"


// Include directives for member types
// Member `scene_world`
#include "moveit_msgs/msg/planning_scene_world.h"
// Member `scene_world`
#include "moveit_msgs/msg/detail/planning_scene_world__rosidl_typesupport_introspection_c.h"
// Member `full_cloud`
#include "sensor_msgs/msg/point_cloud2.h"
// Member `full_cloud`
#include "sensor_msgs/msg/detail/point_cloud2__rosidl_typesupport_introspection_c.h"
// Member `rgb_image`
#include "sensor_msgs/msg/image.h"
// Member `rgb_image`
#include "sensor_msgs/msg/detail/image__rosidl_typesupport_introspection_c.h"
// Member `target_object_id`
// Member `support_surface_id`
// already included above
// #include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void ur_interfaces__srv__GetPlanningScene_Response__rosidl_typesupport_introspection_c__GetPlanningScene_Response_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  ur_interfaces__srv__GetPlanningScene_Response__init(message_memory);
}

void ur_interfaces__srv__GetPlanningScene_Response__rosidl_typesupport_introspection_c__GetPlanningScene_Response_fini_function(void * message_memory)
{
  ur_interfaces__srv__GetPlanningScene_Response__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember ur_interfaces__srv__GetPlanningScene_Response__rosidl_typesupport_introspection_c__GetPlanningScene_Response_message_member_array[6] = {
  {
    "scene_world",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ur_interfaces__srv__GetPlanningScene_Response, scene_world),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "full_cloud",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ur_interfaces__srv__GetPlanningScene_Response, full_cloud),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "rgb_image",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ur_interfaces__srv__GetPlanningScene_Response, rgb_image),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "target_object_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ur_interfaces__srv__GetPlanningScene_Response, target_object_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "support_surface_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ur_interfaces__srv__GetPlanningScene_Response, support_surface_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "success",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(ur_interfaces__srv__GetPlanningScene_Response, success),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers ur_interfaces__srv__GetPlanningScene_Response__rosidl_typesupport_introspection_c__GetPlanningScene_Response_message_members = {
  "ur_interfaces__srv",  // message namespace
  "GetPlanningScene_Response",  // message name
  6,  // number of fields
  sizeof(ur_interfaces__srv__GetPlanningScene_Response),
  ur_interfaces__srv__GetPlanningScene_Response__rosidl_typesupport_introspection_c__GetPlanningScene_Response_message_member_array,  // message members
  ur_interfaces__srv__GetPlanningScene_Response__rosidl_typesupport_introspection_c__GetPlanningScene_Response_init_function,  // function to initialize message memory (memory has to be allocated)
  ur_interfaces__srv__GetPlanningScene_Response__rosidl_typesupport_introspection_c__GetPlanningScene_Response_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t ur_interfaces__srv__GetPlanningScene_Response__rosidl_typesupport_introspection_c__GetPlanningScene_Response_message_type_support_handle = {
  0,
  &ur_interfaces__srv__GetPlanningScene_Response__rosidl_typesupport_introspection_c__GetPlanningScene_Response_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_ur_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, ur_interfaces, srv, GetPlanningScene_Response)() {
  ur_interfaces__srv__GetPlanningScene_Response__rosidl_typesupport_introspection_c__GetPlanningScene_Response_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_msgs, msg, PlanningSceneWorld)();
  ur_interfaces__srv__GetPlanningScene_Response__rosidl_typesupport_introspection_c__GetPlanningScene_Response_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, sensor_msgs, msg, PointCloud2)();
  ur_interfaces__srv__GetPlanningScene_Response__rosidl_typesupport_introspection_c__GetPlanningScene_Response_message_member_array[2].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, sensor_msgs, msg, Image)();
  if (!ur_interfaces__srv__GetPlanningScene_Response__rosidl_typesupport_introspection_c__GetPlanningScene_Response_message_type_support_handle.typesupport_identifier) {
    ur_interfaces__srv__GetPlanningScene_Response__rosidl_typesupport_introspection_c__GetPlanningScene_Response_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &ur_interfaces__srv__GetPlanningScene_Response__rosidl_typesupport_introspection_c__GetPlanningScene_Response_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "ur_interfaces/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "ur_interfaces/srv/detail/get_planning_scene__rosidl_typesupport_introspection_c.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/service_introspection.h"

// this is intentionally not const to allow initialization later to prevent an initialization race
static rosidl_typesupport_introspection_c__ServiceMembers ur_interfaces__srv__detail__get_planning_scene__rosidl_typesupport_introspection_c__GetPlanningScene_service_members = {
  "ur_interfaces__srv",  // service namespace
  "GetPlanningScene",  // service name
  // these two fields are initialized below on the first access
  NULL,  // request message
  // ur_interfaces__srv__detail__get_planning_scene__rosidl_typesupport_introspection_c__GetPlanningScene_Request_message_type_support_handle,
  NULL  // response message
  // ur_interfaces__srv__detail__get_planning_scene__rosidl_typesupport_introspection_c__GetPlanningScene_Response_message_type_support_handle
};

static rosidl_service_type_support_t ur_interfaces__srv__detail__get_planning_scene__rosidl_typesupport_introspection_c__GetPlanningScene_service_type_support_handle = {
  0,
  &ur_interfaces__srv__detail__get_planning_scene__rosidl_typesupport_introspection_c__GetPlanningScene_service_members,
  get_service_typesupport_handle_function,
};

// Forward declaration of request/response type support functions
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, ur_interfaces, srv, GetPlanningScene_Request)();

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, ur_interfaces, srv, GetPlanningScene_Response)();

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_ur_interfaces
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_c, ur_interfaces, srv, GetPlanningScene)() {
  if (!ur_interfaces__srv__detail__get_planning_scene__rosidl_typesupport_introspection_c__GetPlanningScene_service_type_support_handle.typesupport_identifier) {
    ur_interfaces__srv__detail__get_planning_scene__rosidl_typesupport_introspection_c__GetPlanningScene_service_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  rosidl_typesupport_introspection_c__ServiceMembers * service_members =
    (rosidl_typesupport_introspection_c__ServiceMembers *)ur_interfaces__srv__detail__get_planning_scene__rosidl_typesupport_introspection_c__GetPlanningScene_service_type_support_handle.data;

  if (!service_members->request_members_) {
    service_members->request_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, ur_interfaces, srv, GetPlanningScene_Request)()->data;
  }
  if (!service_members->response_members_) {
    service_members->response_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, ur_interfaces, srv, GetPlanningScene_Response)()->data;
  }

  return &ur_interfaces__srv__detail__get_planning_scene__rosidl_typesupport_introspection_c__GetPlanningScene_service_type_support_handle;
}
