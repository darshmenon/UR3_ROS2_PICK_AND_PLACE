/**
 * @file test_planning_execution.cpp
 * @brief Testing application for ROS 2 and MoveIt 2 planning and execution
 *
 * This program tests multiple sequential movements of the robotic arm to
 * ensure planning and execution work correctly without hanging.
 *
 * Bug fix: Explicitly applies Time Optimal Trajectory Generation (TOTG)
 * after planning because the OMPL response adapter
 * (AddTimeOptimalParameterization) may not load on all MoveIt2 Humble
 * installs — leaving all trajectory point timestamps at 0.0, which the
 * ros2_control FollowJointTrajectory controller rejects with:
 *   "Time between points 0 and 1 is not strictly increasing"
 */

#include <geometry_msgs/msg/pose_stamped.hpp>
#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <moveit/robot_trajectory/robot_trajectory.h>
#include <moveit/trajectory_processing/time_optimal_trajectory_generation.h>
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
  arm_group_interface.setPlanningTime(5.0);
  arm_group_interface.setMaxVelocityScalingFactor(0.3);
  arm_group_interface.setMaxAccelerationScalingFactor(0.3);
  arm_group_interface.setEndEffectorLink("robotiq_arg2f_base_link");

  RCLCPP_INFO(logger, "Starting Planning and Execution Test");

  // Joint order: shoulder_pan, shoulder_lift, elbow, wrist_1, wrist_2, wrist_3
  // elbow=1.57 keeps the arm in a collision-free L-shape
  std::vector<std::vector<double>> test_joints;

  // 1: Center ready
  test_joints.push_back({ 0.0, -1.57, 1.57, -1.57, 0.0, 0.0});
  // 2: Zig left
  test_joints.push_back({ 0.5, -1.57, 1.57, -1.57, 0.0, 0.0});
  // 3: Zag right
  test_joints.push_back({-0.5, -1.57, 1.57, -1.57, 0.0, 0.0});
  // 4: Zig left again
  test_joints.push_back({ 0.5, -1.57, 1.57, -1.57, 0.0, 0.0});
  // 5: Back to center
  test_joints.push_back({ 0.0, -1.57, 1.57, -1.57, 0.0, 0.0});

  bool all_tests_passed = true;

  // Time-optimal trajectory generator — applied after planning to guarantee
  // strictly-increasing timestamps even if response adapters don't run.
  trajectory_processing::TimeOptimalTrajectoryGeneration totg;

  for (size_t i = 0; i < test_joints.size(); ++i) {
    RCLCPP_INFO(logger, "--- Testing Target %zu (ZigZag) ---", i + 1);

    arm_group_interface.setJointValueTarget(test_joints[i]);

    moveit::planning_interface::MoveGroupInterface::Plan plan;
    bool plan_success = static_cast<bool>(arm_group_interface.plan(plan));

    if (plan_success) {
      // --- Time-parameterization fix ---
      // Rebuild the trajectory as a RobotTrajectory and re-stamp it with TOTG.
      // This resolves the "timestamps not strictly increasing" rejection from
      // the FollowJointTrajectory controller when the response adapter doesn't run.
      auto robot_model = arm_group_interface.getRobotModel();
      auto robot_traj = std::make_shared<robot_trajectory::RobotTrajectory>(robot_model, "arm");
      robot_traj->setRobotTrajectoryMsg(
        *arm_group_interface.getCurrentState(),
        plan.trajectory_
      );

      // Replace missing getters with the known 0.3 scale
      const double vel_scale = 0.3;
      const double acc_scale = 0.3;
      if (!totg.computeTimeStamps(*robot_traj, vel_scale, acc_scale)) {
        RCLCPP_ERROR(logger, "Time parameterization for Target %zu FAILED.", i + 1);
        all_tests_passed = false;
        break;
      }
      robot_traj->getRobotTrajectoryMsg(plan.trajectory_);
      // --- End fix ---

      RCLCPP_INFO(logger, "Planning for Target %zu SUCCESS. Executing...", i + 1);
      auto exec_result = arm_group_interface.execute(plan);

      if (exec_result == moveit::core::MoveItErrorCode::SUCCESS) {
        RCLCPP_INFO(logger, "Execution for Target %zu SUCCESS.", i + 1);
      } else {
        RCLCPP_ERROR(logger, "Execution for Target %zu FAILED.", i + 1);
        all_tests_passed = false;
        break;
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
