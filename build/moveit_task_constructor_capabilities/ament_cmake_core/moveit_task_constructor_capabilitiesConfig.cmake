# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_moveit_task_constructor_capabilities_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED moveit_task_constructor_capabilities_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(moveit_task_constructor_capabilities_FOUND FALSE)
  elseif(NOT moveit_task_constructor_capabilities_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(moveit_task_constructor_capabilities_FOUND FALSE)
  endif()
  return()
endif()
set(_moveit_task_constructor_capabilities_CONFIG_INCLUDED TRUE)

# output package information
if(NOT moveit_task_constructor_capabilities_FIND_QUIETLY)
  message(STATUS "Found moveit_task_constructor_capabilities: 0.1.3 (${moveit_task_constructor_capabilities_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'moveit_task_constructor_capabilities' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT moveit_task_constructor_capabilities_DEPRECATED_QUIET)
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(moveit_task_constructor_capabilities_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "ament_cmake_export_dependencies-extras.cmake")
foreach(_extra ${_extras})
  include("${moveit_task_constructor_capabilities_DIR}/${_extra}")
endforeach()
