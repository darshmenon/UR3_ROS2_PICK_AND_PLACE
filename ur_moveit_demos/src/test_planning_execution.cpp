/**
 * @file test_planning_execution.cpp
 * @brief Testing application for ROS 2 and MoveIt 2 planning and execution
 *
 * This program tests multiple sequential movements of the robotic arm to 
 * ensure planning and execution work correctly without hanging.
 */

#include <geometry_msgs/msg/pose_stamped.hpp>
#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <thread>
#include <vector>

int main(int argc, char * argv[])
{
  // Start up ROS 2
  rclcpp::init(argc, argv);

  // Creates a node
  auto const node = std::make_shared<rclcpp::Node>(
    "test_planning_execution",
    rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true)
  );

  auto const logger = rclcpp::get_logger("test_planning_execution");

  // Spin a single-threaded executor in a background thread for MoveIt action servers.
  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  auto spinner = std::thread([&executor]() { executor.spin(); });

  using moveit::planning_interface::MoveGroupInterface;
  auto arm_group_interface = MoveGroupInterface(node, "arm");

  arm_group_interface.setPlanningPipelineId("ompl");
  arm_group_interface.setPlannerId("RRTConnectkConfigDefault");
  arm_group_interface.setPlanningTime(2.0);
  arm_group_interface.setMaxVelocityScalingFactor(1.0);
  arm_group_interface.setMaxAccelerationScalingFactor(1.0);
  arm_group_interface.setEndEffectorLink("robotiq_arg2f_base_link");

  RCLCPP_INFO(logger, "Starting Planning and Execution Test");

  // Define a series of test poses
  std::vector<geometry_msgs::msg::Pose> test_poses;
  
  // Pose 1
  geometry_msgs::msg::Pose pose1;
  pose1.position.x = 0.128;
  pose1.position.y = -0.266;
  pose1.position.z = 0.200;
  pose1.orientation.x = 0.635;
  pose1.orientation.y = -0.268;
  pose1.orientation.z = 0.694;
  pose1.orientation.w = 0.206;
  test_poses.push_back(pose1);

  // Pose 2
  geometry_msgs::msg::Pose pose2;
  pose2.position.x = 0.061;
  pose2.position.y = -0.176;
  pose2.position.z = 0.300;
  pose2.orientation.x = 0.0;
  pose2.orientation.y = 0.0;
  pose2.orientation.z = 0.0;
  pose2.orientation.w = 1.0;
  test_poses.push_back(pose2);

  bool all_tests_passed = true;

  for (size_t i = 0; i < test_poses.size(); ++i) {
    RCLCPP_INFO(logger, "--- Testing Target %zu ---", i + 1);
    
    geometry_msgs::msg::PoseStamped target_msg;
    target_msg.header.frame_id = "base_link";
    target_msg.header.stamp = node->now();
    target_msg.pose = test_poses[i];

    arm_group_interface.setPoseTarget(target_msg);

    moveit::planning_interface::MoveGroupInterface::Plan plan;
    bool plan_success = static_cast<bool>(arm_group_interface.plan(plan));

    if (plan_success) {
      RCLCPP_INFO(logger, "Planning for Target %zu SUCCESS. Executing...", i + 1);
      auto exec_result = arm_group_interface.execute(plan);
      
      if (exec_result == moveit::core::MoveItErrorCode::SUCCESS) {
        RCLCPP_INFO(logger, "Execution for Target %zu SUCCESS.", i + 1);
      } else {
        RCLCPP_ERROR(logger, "Execution for Target %zu FAILED.", i + 1);
        all_tests_passed = false;
        break; // Stop on first failure
      }
    } else {
      RCLCPP_ERROR(logger, "Planning for Target %zu FAILED.", i + 1);
      all_tests_passed = false;
      break;
    }
    
    // Small delay between movements
    std::this_thread::sleep_for(std::chrono::seconds(1));
  }

  if (all_tests_passed) {
    RCLCPP_INFO(logger, "ALL TESTS PASSED SUCCESSFULLY!");
  } else {
    RCLCPP_ERROR(logger, "SOME TESTS FAILED.");
  }

  // Clean up and shut down the ROS 2 node
  rclcpp::shutdown();

  // Wait for the spinner thread to finish
  spinner.join();

  return 0;
}
