// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from moveit_task_constructor_msgs:srv/GetSolution.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "moveit_task_constructor_msgs/srv/detail/get_solution__rosidl_typesupport_introspection_c.h"
#include "moveit_task_constructor_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "moveit_task_constructor_msgs/srv/detail/get_solution__functions.h"
#include "moveit_task_constructor_msgs/srv/detail/get_solution__struct.h"


#ifdef __cplusplus
extern "C"
{
#endif

void moveit_task_constructor_msgs__srv__GetSolution_Request__rosidl_typesupport_introspection_c__GetSolution_Request_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  moveit_task_constructor_msgs__srv__GetSolution_Request__init(message_memory);
}

void moveit_task_constructor_msgs__srv__GetSolution_Request__rosidl_typesupport_introspection_c__GetSolution_Request_fini_function(void * message_memory)
{
  moveit_task_constructor_msgs__srv__GetSolution_Request__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember moveit_task_constructor_msgs__srv__GetSolution_Request__rosidl_typesupport_introspection_c__GetSolution_Request_message_member_array[1] = {
  {
    "solution_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__srv__GetSolution_Request, solution_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers moveit_task_constructor_msgs__srv__GetSolution_Request__rosidl_typesupport_introspection_c__GetSolution_Request_message_members = {
  "moveit_task_constructor_msgs__srv",  // message namespace
  "GetSolution_Request",  // message name
  1,  // number of fields
  sizeof(moveit_task_constructor_msgs__srv__GetSolution_Request),
  moveit_task_constructor_msgs__srv__GetSolution_Request__rosidl_typesupport_introspection_c__GetSolution_Request_message_member_array,  // message members
  moveit_task_constructor_msgs__srv__GetSolution_Request__rosidl_typesupport_introspection_c__GetSolution_Request_init_function,  // function to initialize message memory (memory has to be allocated)
  moveit_task_constructor_msgs__srv__GetSolution_Request__rosidl_typesupport_introspection_c__GetSolution_Request_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t moveit_task_constructor_msgs__srv__GetSolution_Request__rosidl_typesupport_introspection_c__GetSolution_Request_message_type_support_handle = {
  0,
  &moveit_task_constructor_msgs__srv__GetSolution_Request__rosidl_typesupport_introspection_c__GetSolution_Request_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_moveit_task_constructor_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, srv, GetSolution_Request)() {
  if (!moveit_task_constructor_msgs__srv__GetSolution_Request__rosidl_typesupport_introspection_c__GetSolution_Request_message_type_support_handle.typesupport_identifier) {
    moveit_task_constructor_msgs__srv__GetSolution_Request__rosidl_typesupport_introspection_c__GetSolution_Request_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &moveit_task_constructor_msgs__srv__GetSolution_Request__rosidl_typesupport_introspection_c__GetSolution_Request_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

// already included above
// #include <stddef.h>
// already included above
// #include "moveit_task_constructor_msgs/srv/detail/get_solution__rosidl_typesupport_introspection_c.h"
// already included above
// #include "moveit_task_constructor_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "rosidl_typesupport_introspection_c/field_types.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
// already included above
// #include "rosidl_typesupport_introspection_c/message_introspection.h"
// already included above
// #include "moveit_task_constructor_msgs/srv/detail/get_solution__functions.h"
// already included above
// #include "moveit_task_constructor_msgs/srv/detail/get_solution__struct.h"


// Include directives for member types
// Member `solution`
#include "moveit_task_constructor_msgs/msg/solution.h"
// Member `solution`
#include "moveit_task_constructor_msgs/msg/detail/solution__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void moveit_task_constructor_msgs__srv__GetSolution_Response__rosidl_typesupport_introspection_c__GetSolution_Response_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  moveit_task_constructor_msgs__srv__GetSolution_Response__init(message_memory);
}

void moveit_task_constructor_msgs__srv__GetSolution_Response__rosidl_typesupport_introspection_c__GetSolution_Response_fini_function(void * message_memory)
{
  moveit_task_constructor_msgs__srv__GetSolution_Response__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember moveit_task_constructor_msgs__srv__GetSolution_Response__rosidl_typesupport_introspection_c__GetSolution_Response_message_member_array[1] = {
  {
    "solution",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(moveit_task_constructor_msgs__srv__GetSolution_Response, solution),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers moveit_task_constructor_msgs__srv__GetSolution_Response__rosidl_typesupport_introspection_c__GetSolution_Response_message_members = {
  "moveit_task_constructor_msgs__srv",  // message namespace
  "GetSolution_Response",  // message name
  1,  // number of fields
  sizeof(moveit_task_constructor_msgs__srv__GetSolution_Response),
  moveit_task_constructor_msgs__srv__GetSolution_Response__rosidl_typesupport_introspection_c__GetSolution_Response_message_member_array,  // message members
  moveit_task_constructor_msgs__srv__GetSolution_Response__rosidl_typesupport_introspection_c__GetSolution_Response_init_function,  // function to initialize message memory (memory has to be allocated)
  moveit_task_constructor_msgs__srv__GetSolution_Response__rosidl_typesupport_introspection_c__GetSolution_Response_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t moveit_task_constructor_msgs__srv__GetSolution_Response__rosidl_typesupport_introspection_c__GetSolution_Response_message_type_support_handle = {
  0,
  &moveit_task_constructor_msgs__srv__GetSolution_Response__rosidl_typesupport_introspection_c__GetSolution_Response_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_moveit_task_constructor_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, srv, GetSolution_Response)() {
  moveit_task_constructor_msgs__srv__GetSolution_Response__rosidl_typesupport_introspection_c__GetSolution_Response_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, msg, Solution)();
  if (!moveit_task_constructor_msgs__srv__GetSolution_Response__rosidl_typesupport_introspection_c__GetSolution_Response_message_type_support_handle.typesupport_identifier) {
    moveit_task_constructor_msgs__srv__GetSolution_Response__rosidl_typesupport_introspection_c__GetSolution_Response_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &moveit_task_constructor_msgs__srv__GetSolution_Response__rosidl_typesupport_introspection_c__GetSolution_Response_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "moveit_task_constructor_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "moveit_task_constructor_msgs/srv/detail/get_solution__rosidl_typesupport_introspection_c.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/service_introspection.h"

// this is intentionally not const to allow initialization later to prevent an initialization race
static rosidl_typesupport_introspection_c__ServiceMembers moveit_task_constructor_msgs__srv__detail__get_solution__rosidl_typesupport_introspection_c__GetSolution_service_members = {
  "moveit_task_constructor_msgs__srv",  // service namespace
  "GetSolution",  // service name
  // these two fields are initialized below on the first access
  NULL,  // request message
  // moveit_task_constructor_msgs__srv__detail__get_solution__rosidl_typesupport_introspection_c__GetSolution_Request_message_type_support_handle,
  NULL  // response message
  // moveit_task_constructor_msgs__srv__detail__get_solution__rosidl_typesupport_introspection_c__GetSolution_Response_message_type_support_handle
};

static rosidl_service_type_support_t moveit_task_constructor_msgs__srv__detail__get_solution__rosidl_typesupport_introspection_c__GetSolution_service_type_support_handle = {
  0,
  &moveit_task_constructor_msgs__srv__detail__get_solution__rosidl_typesupport_introspection_c__GetSolution_service_members,
  get_service_typesupport_handle_function,
};

// Forward declaration of request/response type support functions
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, srv, GetSolution_Request)();

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, srv, GetSolution_Response)();

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_moveit_task_constructor_msgs
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, srv, GetSolution)() {
  if (!moveit_task_constructor_msgs__srv__detail__get_solution__rosidl_typesupport_introspection_c__GetSolution_service_type_support_handle.typesupport_identifier) {
    moveit_task_constructor_msgs__srv__detail__get_solution__rosidl_typesupport_introspection_c__GetSolution_service_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  rosidl_typesupport_introspection_c__ServiceMembers * service_members =
    (rosidl_typesupport_introspection_c__ServiceMembers *)moveit_task_constructor_msgs__srv__detail__get_solution__rosidl_typesupport_introspection_c__GetSolution_service_type_support_handle.data;

  if (!service_members->request_members_) {
    service_members->request_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, srv, GetSolution_Request)()->data;
  }
  if (!service_members->response_members_) {
    service_members->response_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, moveit_task_constructor_msgs, srv, GetSolution_Response)()->data;
  }

  return &moveit_task_constructor_msgs__srv__detail__get_solution__rosidl_typesupport_introspection_c__GetSolution_service_type_support_handle;
}
