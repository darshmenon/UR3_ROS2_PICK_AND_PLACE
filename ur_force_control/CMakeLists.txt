cmake_minimum_required(VERSION 3.5)
project(ur_force_control)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(moveit_core REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(pinocchio REQUIRED)

ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS
  ur_force_control/ft_monitor_node.py
  DESTINATION lib/${PROJECT_NAME}
)

add_executable(external_wrench_estimator src/external_wrench_estimator.cpp)
target_compile_features(external_wrench_estimator PUBLIC cxx_std_17)
ament_target_dependencies(external_wrench_estimator
  rclcpp
  moveit_ros_planning_interface
  moveit_core
  geometry_msgs
  std_msgs
  std_srvs
)
target_link_libraries(external_wrench_estimator
  pinocchio::pinocchio_default
  pinocchio::pinocchio_parsers
)

add_executable(joint_impedance_controller src/joint_impedance_controller.cpp)
target_compile_features(joint_impedance_controller PUBLIC cxx_std_17)
ament_target_dependencies(joint_impedance_controller
  rclcpp
  moveit_ros_planning_interface
  moveit_core
  std_msgs
  std_srvs
)
target_link_libraries(joint_impedance_controller
  pinocchio::pinocchio_default
  pinocchio::pinocchio_parsers
)

install(TARGETS external_wrench_estimator joint_impedance_controller
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
