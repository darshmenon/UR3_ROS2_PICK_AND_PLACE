cmake_minimum_required(VERSION 3.8)
project(ur_flow_policy)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS
  ur_flow_policy/inference_node.py
  DESTINATION lib/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/train_flow_policy.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

ament_package()
