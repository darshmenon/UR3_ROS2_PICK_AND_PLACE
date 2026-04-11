cmake_minimum_required(VERSION 3.8)
project(ur_perception)

# OpenMPI can report include flags with "-I" prefixes that newer PCL/VTK/MPI
# discovery paths may treat as literal directories. Normalize them up front.
find_program(MPICC_EXECUTABLE mpicc)
if(MPICC_EXECUTABLE)
  execute_process(
    COMMAND ${MPICC_EXECUTABLE} --showme:compile
    OUTPUT_VARIABLE MPI_SHOWME_COMPILE
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
  )
  if(MPI_SHOWME_COMPILE)
    separate_arguments(MPI_SHOWME_TOKENS UNIX_COMMAND "${MPI_SHOWME_COMPILE}")
    set(MPI_SANITIZED_INCLUDE_DIRS "")
    foreach(token IN LISTS MPI_SHOWME_TOKENS)
      if(token MATCHES "^-I.+")
        string(REGEX REPLACE "^-I" "" include_dir "${token}")
        list(APPEND MPI_SANITIZED_INCLUDE_DIRS "${include_dir}")
      endif()
    endforeach()
    if(MPI_SANITIZED_INCLUDE_DIRS)
      set(MPI_C_COMPILER_INCLUDE_DIRS "${MPI_SANITIZED_INCLUDE_DIRS}" CACHE STRING "" FORCE)
      set(MPI_CXX_COMPILER_INCLUDE_DIRS "${MPI_SANITIZED_INCLUDE_DIRS}" CACHE STRING "" FORCE)
    endif()
  endif()
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(PCL REQUIRED COMPONENTS common io filters segmentation features search kdtree)
find_package(pcl_conversions REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_eigen REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(Eigen3 REQUIRED)

# -----------------------------------------------------------------------
# Python package (object_detector_node — colour + YOLO)
# -----------------------------------------------------------------------
ament_python_install_package(${PROJECT_NAME})
install(PROGRAMS
  ur_perception/object_detector_node.py
  DESTINATION lib/${PROJECT_NAME}
)

# -----------------------------------------------------------------------
# C++ PCL library — shared PCL utilities
# (sources ported from ur_mtc_pick_place_demo)
# -----------------------------------------------------------------------
add_library(ur_perception_pcl SHARED
  src/normals_curvature_and_rsd_estimation.cpp
  src/cluster_extraction.cpp
  src/plane_segmentation.cpp
  src/object_segmentation.cpp
)
target_include_directories(ur_perception_pcl PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
  ${PCL_INCLUDE_DIRS}
)
target_link_libraries(ur_perception_pcl ${PCL_LIBRARIES})
ament_target_dependencies(ur_perception_pcl
  rclcpp sensor_msgs pcl_conversions tf2_ros tf2_eigen moveit_msgs
)
target_compile_definitions(ur_perception_pcl PRIVATE ${PCL_DEFINITIONS})

install(TARGETS ur_perception_pcl
  EXPORT export_ur_perception
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  RUNTIME DESTINATION bin
)
install(DIRECTORY include/ DESTINATION include)

# -----------------------------------------------------------------------
# Shared install dirs
# -----------------------------------------------------------------------
install(DIRECTORY launch config DESTINATION share/${PROJECT_NAME})

ament_package()
