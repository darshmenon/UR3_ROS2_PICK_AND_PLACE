cmake_minimum_required(VERSION 3.10)
project(ur_web_dashboard)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch web DESTINATION share/${PROJECT_NAME})

ament_package()
