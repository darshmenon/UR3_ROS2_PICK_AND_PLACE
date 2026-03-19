cmake_minimum_required(VERSION 3.16)
project(moveit_task_constructor_core)

find_package(ament_cmake REQUIRED)

find_package(Boost REQUIRED)
find_package(fmt REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(moveit_common REQUIRED)
moveit_package()
find_package(moveit_core REQUIRED)

# Cross-distro header compatibility: Humble ships .h, Jazzy ships .hpp.
# If only .hpp exists (Jazzy), generate .h shims so MTC sources compile on both.
find_file(_cf_h "moveit/macros/class_forward.h" HINTS ${moveit_core_INCLUDE_DIRS}
          PATHS /opt/ros/humble/include /opt/ros/jazzy/include
          PATH_SUFFIXES "" NO_DEFAULT_PATH)
if(NOT _cf_h)
  message(STATUS "MTC compat: Jazzy-style headers — generating .h shims")
  set(_compat "${CMAKE_CURRENT_BINARY_DIR}/compat_include")
  foreach(_d macros planning_scene robot_model robot_trajectory trajectory_processing utils)
    file(MAKE_DIRECTORY "${_compat}/moveit/${_d}")
  endforeach()
  file(WRITE "${_compat}/moveit/macros/class_forward.h"
    "#pragma once\n#include <moveit/macros/class_forward.hpp>\n")
  file(WRITE "${_compat}/moveit/planning_scene/planning_scene.h"
    "#pragma once\n#include <moveit/planning_scene/planning_scene.hpp>\n")
  file(WRITE "${_compat}/moveit/robot_model/robot_model.h"
    "#pragma once\n#include <moveit/robot_model/robot_model.hpp>\n")
  file(WRITE "${_compat}/moveit/robot_trajectory/robot_trajectory.h"
    "#pragma once\n#include <moveit/robot_trajectory/robot_trajectory.hpp>\n")
  file(WRITE "${_compat}/moveit/trajectory_processing/time_parameterization.h"
    "#pragma once\n#include <moveit/trajectory_processing/time_parameterization.hpp>\n")
  file(WRITE "${_compat}/moveit/utils/moveit_error_code.h"
    "#pragma once\n#include <moveit/utils/moveit_error_code.hpp>\n")
  include_directories(BEFORE "${_compat}")
else()
  message(STATUS "MTC compat: Humble-style headers (.h) — no shims needed")
endif()

find_package(moveit_ros_planning REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(moveit_task_constructor_msgs REQUIRED)
find_package(py_binding_tools REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rviz_marker_tools REQUIRED)
find_package(tf2_eigen REQUIRED)
find_package(visualization_msgs REQUIRED)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_compile_options(-fvisibility-inlines-hidden)

set(PROJECT_INCLUDE ${CMAKE_CURRENT_SOURCE_DIR}/include/moveit/task_constructor)

add_subdirectory(src)
ament_python_install_package(moveit PACKAGE_DIR python/moveit)
add_subdirectory(python)
add_subdirectory(test)

install(DIRECTORY include/ DESTINATION include
	PATTERN "*_p.h" EXCLUDE)

pluginlib_export_plugin_description_file(${PROJECT_NAME} motion_planning_stages_plugin_description.xml)

ament_export_targets(${PROJECT_NAME}Targets HAS_LIBRARY_TARGET)
ament_export_dependencies(Boost)
ament_export_dependencies(geometry_msgs)
ament_export_dependencies(moveit_core)
ament_export_dependencies(moveit_ros_planning)
ament_export_dependencies(moveit_ros_planning_interface)
ament_export_dependencies(moveit_task_constructor_msgs)
ament_export_dependencies(py_binding_tools)
ament_export_dependencies(rclcpp)
ament_export_dependencies(rviz_marker_tools)
ament_export_dependencies(tf2_eigen)
ament_export_dependencies(visualization_msgs)
ament_package()
