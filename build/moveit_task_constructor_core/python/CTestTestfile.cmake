# CMake generated Testfile for 
# Source directory: /home/darsh/UR3_ROS2_PICK_AND_PLACE/src/moveit_task_constructor/core/python
# Build directory: /home/darsh/UR3_ROS2_PICK_AND_PLACE/build/moveit_task_constructor_core/python
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(test_mtc "/usr/bin/python3" "-u" "/opt/ros/jazzy/share/ament_cmake_test/cmake/run_test.py" "/home/darsh/UR3_ROS2_PICK_AND_PLACE/build/moveit_task_constructor_core/test_results/moveit_task_constructor_core/test_mtc.xunit.xml" "--package-name" "moveit_task_constructor_core" "--output-file" "/home/darsh/UR3_ROS2_PICK_AND_PLACE/build/moveit_task_constructor_core/ament_cmake_pytest/test_mtc.txt" "--append-env" "PYTHONPATH=/home/darsh/UR3_ROS2_PICK_AND_PLACE/build/moveit_task_constructor_core/python" "--command" "/usr/bin/python3" "-u" "-m" "pytest" "/home/darsh/UR3_ROS2_PICK_AND_PLACE/src/moveit_task_constructor/core/python/test/test_mtc.py" "-o" "cache_dir=/home/darsh/UR3_ROS2_PICK_AND_PLACE/build/moveit_task_constructor_core/python/ament_cmake_pytest/test_mtc/.cache" "--junit-xml=/home/darsh/UR3_ROS2_PICK_AND_PLACE/build/moveit_task_constructor_core/test_results/moveit_task_constructor_core/test_mtc.xunit.xml" "--junit-prefix=moveit_task_constructor_core")
set_tests_properties(test_mtc PROPERTIES  LABELS "pytest" TIMEOUT "60" WORKING_DIRECTORY "/home/darsh/UR3_ROS2_PICK_AND_PLACE/src/moveit_task_constructor/core" _BACKTRACE_TRIPLES "/opt/ros/jazzy/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/jazzy/share/ament_cmake_pytest/cmake/ament_add_pytest_test.cmake;177;ament_add_test;/home/darsh/UR3_ROS2_PICK_AND_PLACE/src/moveit_task_constructor/core/python/CMakeLists.txt;35;ament_add_pytest_test;/home/darsh/UR3_ROS2_PICK_AND_PLACE/src/moveit_task_constructor/core/python/CMakeLists.txt;0;")
subdirs("pybind11")
subdirs("bindings")
