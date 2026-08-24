cmake_minimum_required(VERSION 3.8)
project(ur_data_collector)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Install the Python package
ament_python_install_package(${PROJECT_NAME})

# Install the node executable (this package builds via ament_cmake, so
# setup.py's console_scripts entry_points are never invoked — the node
# must be installed explicitly here, same as ur_perception/ur_openvla do)
install(PROGRAMS
  ur_data_collector/collector_node.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install scripts
install(PROGRAMS
  scripts/train_bc.py
  scripts/export_lerobot_dataset.py
  scripts/auto_collect_demos.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files
install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

# Install config files
install(DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}/config
)

ament_package()
