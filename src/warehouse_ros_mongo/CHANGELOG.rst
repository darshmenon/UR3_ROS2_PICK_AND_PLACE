^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package warehouse_ros
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

2.0.3 (2021-09-27)
------------------
* Clean OpenSSL dependencies (`#67 <https://github.com/ros-planning/warehouse_ros_mongo/issues/67>`_)
* Add Copyright and LICENSE files (`#65 <https://github.com/ros-planning/warehouse_ros_mongo/issues/65>`_)
* Contributors: Vatan Aksoy Tezer

2.0.2 (2021-06-17)
------------------
* [ROS2] Add prerelease tests (`#59 <https://github.com/ros-planning/warehouse_ros_mongo/issues/59>`_)
* Use libssl-dev build_depend for OpenSSL (`#63 <https://github.com/ros-planning/warehouse_ros_mongo/issues/63>`_)
* Add CI for Galactic, Rolling (`#57 <https://github.com/ros-planning/warehouse_ros_mongo/issues/57>`_)(`#56 <https://github.com/ros-planning/warehouse_ros_mongo/issues/56>`_)
* Contributors: Henning Kayser, Vatan Aksoy Tezer

2.0.1 (2021-04-09)
------------------
* Fix installation path for FindMONGODB.cmake (`#42 <https://github.com/ros-planning/warehouse_ros_mongo/issues/42>`_)
* Fix cmake export of MONGODB dependency (`#41 <https://github.com/ros-planning/warehouse_ros_mongo/issues/41>`_)
* Contributors: Jafar Abdi, Robert Haschke, Tyler Weaver

2.0.0 (2020-11-20)
-----------
* [ros2-migration] Port to ROS 2 (`#38 <https://github.com/ros-planning/warehouse_ros_mongo/issues/38>`_)
  * Migrate package.xml and cmake files to ROS 2
  * Apply ROS 2 migration steps to source files
  * Compile on ROS 2 Foxy, enable CI
  * Check clang-format, ament_lint
* Contributors: Yu Yan

0.10.0 (2020-10-09)
-------------------
* clang-format-10
* Python3 compatibility layer for roslaunch in CMake (`#35 <https://github.com/ros-planning/warehouse_ros_mongo/issues/35>`_)
* Contributors: Robert Haschke, Tyler Weaver

0.9.2 (2020-07-21)
------------------
* Proper cmake test for mongo/version.h
* Bump cmake version to 3.0.2
* ROS test: Start mongodb
* mongo_wrapper_ros.py: Handle permission errors creating database path
* python3 syntax compatibility
* Contributors: Robert Haschke

0.9.1 (2019-09-28)
------------------
* Initialize mongo client only once (`#28 <https://github.com/ros-planning/warehouse_ros_mongo/issues/28>`_)
* Restore mongod python wrapper
* Contributors: Masaki Murooka, Robert Haschke

0.9.0 (2019-08-14)
------------------
* Use std pointers
* Fix catkin issues
* Refactored Warehouse ROS for pluginlib
* Contributors: Christian Rauch, Connor Brew, Dave Coleman, Robert Haschke, v4hn

0.8.8 (2014-10-01)
------------------
* Merge pull request `#13 <https://github.com/ros-planning/warehouse_ros/issues/13>`_ from corot/master
  Issue `#11 <https://github.com/ros-planning/warehouse_ros/issues/11>`_: Add a Python library
* Merge pull request `#15 <https://github.com/ros-planning/warehouse_ros/issues/15>`_ from v4hn/shared-static-mongodb
  only export MongoDB dependency for shared mongodb-library
* only export MongoDB dependency for shared mongodb-library
  libmongoclient.a uses quite a number of other libs and the exact
  requirements can't be read from a cmake/pc file.
  Therefore it makes more sense to keep the dependency hidden from ROS
  when we use the static lib. libwarehouse_ros then provides all required functions.
  ... This is a bit like creating a libmongoclient.so, but the whole problem
  exists because debian/ubuntu don't provide this one, right?
  The shared library can - and has to - be exported as a dependency to ROS.
* Missing part of https://github.com/corot/world_canvas/issues/10:
  requires both mongodb and mongodb-dev
* Merge branch 'master' of https://github.com/corot/warehouse_ros.git
* Add kwargs also to insert so we can solves issues as
  https://github.com/corot/world_canvas/issues/13
* Add kwargs to ensure_index so we can solves issues as
  https://github.com/corot/world_canvas/issues/13
* Add python-pymongo dependency
* Issue https://github.com/corot/world_canvas/issues/11: rospy queue_size
  warnings
* Issue `#11 <https://github.com/ros-planning/warehouse_ros/issues/11>`_: Add a Python library
* Contributors: Ioan A Sucan, corot, v4hn

0.8.5 (2014-02-23)
------------------
* Fixed malloc.h inclusion on Mac OS X
* Rename README.rst to README.md
* added travis support
* Contributors: Acorn, Dave Hershberger, Ioan A Sucan, Marco Esposito

0.8.4 (2013-07-03)
------------------
* update how we find MongoDB

0.8.2 (2013-07-03)
------------------
* fix typo and use correct install location
* add config.h.in for deciding how to include mongo headers

0.8.1 (2013-07-03)
------------------
* fix linking issues (missing SSL symbols) in deps, undef defined macros
