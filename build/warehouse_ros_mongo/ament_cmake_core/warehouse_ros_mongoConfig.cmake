# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_warehouse_ros_mongo_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED warehouse_ros_mongo_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(warehouse_ros_mongo_FOUND FALSE)
  elseif(NOT warehouse_ros_mongo_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(warehouse_ros_mongo_FOUND FALSE)
  endif()
  return()
endif()
set(_warehouse_ros_mongo_CONFIG_INCLUDED TRUE)

# output package information
if(NOT warehouse_ros_mongo_FIND_QUIETLY)
  message(STATUS "Found warehouse_ros_mongo: 2.0.3 (${warehouse_ros_mongo_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'warehouse_ros_mongo' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${warehouse_ros_mongo_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(warehouse_ros_mongo_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "ConfigExtras.cmake;ament_cmake_export_targets-extras.cmake;ament_cmake_export_dependencies-extras.cmake")
foreach(_extra ${_extras})
  include("${warehouse_ros_mongo_DIR}/${_extra}")
endforeach()
