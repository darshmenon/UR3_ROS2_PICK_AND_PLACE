#include <geometry_msgs/msg/pose.hpp>
#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <moveit/robot_trajectory/robot_trajectory.h>
#include <moveit/trajectory_processing/time_optimal_trajectory_generation.h>
#include <thread>
#include <vector>

using moveit::planning_interface::MoveGroupInterface;

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<rclcpp::Node>(
    "custom_zigzag_motion",
    rclcpp::NodeOptions()
      .automatically_declare_parameters_from_overrides(true)
      .parameter_overrides({{"use_sim_time", true}})
  );
  auto logger = rclcpp::get_logger("custom_zigzag_motion");

  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  auto spinner = std::thread([&executor]() { executor.spin(); });

  MoveGroupInterface arm(node, "arm");
  arm.setPlanningPipelineId("ompl");
  arm.setPlannerId("RRTConnectkConfigDefault");
  arm.setPlanningTime(5.0);
  arm.setMaxVelocityScalingFactor(0.3);
  arm.setMaxAccelerationScalingFactor(0.3);
  arm.setEndEffectorLink("robotiq_arg2f_base_link");

  RCLCPP_INFO(logger, "Moving to home pose...");
  arm.setNamedTarget("home");
  MoveGroupInterface::Plan plan;
  
  trajectory_processing::TimeOptimalTrajectoryGeneration totg;
  
  if (arm.plan(plan) == moveit::core::MoveItErrorCode::SUCCESS) {
    auto robot_model = arm.getRobotModel();
    auto robot_traj = std::make_shared<robot_trajectory::RobotTrajectory>(robot_model, "arm");
    robot_traj->setRobotTrajectoryMsg(*arm.getCurrentState(), plan.trajectory_);
    if (!totg.computeTimeStamps(*robot_traj, 0.3, 0.3)) {
      RCLCPP_ERROR(logger, "Time parameterization for home FAILED.");
    } else {
      robot_traj->getRobotTrajectoryMsg(plan.trajectory_);
    }
    arm.execute(plan);
  } else {
    RCLCPP_ERROR(logger, "Failed to plan home position.");
    rclcpp::shutdown();
    spinner.join();
    return 1;
  }
  std::this_thread::sleep_for(std::chrono::seconds(1));

  RCLCPP_INFO(logger, "Performing custom zig-zag pattern...");

  std::vector<geometry_msgs::msg::Pose> waypoints;
  const double START_X = 0.25;
  const double START_Y = 0.0;
  const double Z_LEVEL = 0.30;
  
  // Custom orientatiom: pointing straight down (approximate rotation 180 around X)
  geometry_msgs::msg::Pose start_pose;
  start_pose.position.x = START_X;
  start_pose.position.y = START_Y;
  start_pose.position.z = Z_LEVEL;
  start_pose.orientation.x = 1.0;
  start_pose.orientation.y = 0.0;
  start_pose.orientation.z = 0.0;
  start_pose.orientation.w = 0.0;
  
  waypoints.push_back(start_pose);

  // Define Zig-Zag points
  const int steps = 3;
  const double x_inc = 0.07;
  const double y_amp = 0.12;

  for (int i = 0; i <= steps; ++i) {
    geometry_msgs::msg::Pose wp = start_pose;
    wp.position.x = START_X + (i * x_inc);
    wp.position.y = START_Y + ((i % 2 == 0) ? y_amp : -y_amp);
    waypoints.push_back(wp);
  }

  // Move to the first waypoint (start) using joint-space PTP
  RCLCPP_INFO(logger, "Moving to start position of zig-zag via PTP...");
  arm.setPoseTarget(waypoints[0]);
  MoveGroupInterface::Plan start_plan;
  if (arm.plan(start_plan) == moveit::core::MoveItErrorCode::SUCCESS) {
    auto robot_model = arm.getRobotModel();
    auto robot_traj = std::make_shared<robot_trajectory::RobotTrajectory>(robot_model, "arm");
    robot_traj->setRobotTrajectoryMsg(*arm.getCurrentState(), start_plan.trajectory_);
    if (!totg.computeTimeStamps(*robot_traj, 0.3, 0.3)) {
      RCLCPP_ERROR(logger, "Time parameterization for start wp FAILED.");
    } else {
      robot_traj->getRobotTrajectoryMsg(start_plan.trajectory_);
    }
    arm.execute(start_plan);
  } else {
    RCLCPP_ERROR(logger, "Failed to PTP to start waypoint.");
    rclcpp::shutdown();
    spinner.join();
    return 1;
  }
  std::this_thread::sleep_for(std::chrono::seconds(1));

  RCLCPP_INFO(logger, "Executing zig-zag via LIN...");
  bool success = true;

  // Switch to linear Cartesian planner for Zig-Zag
  arm.setPlanningPipelineId("pilz_industrial_motion_planner");
  arm.setPlannerId("LIN");

  for (size_t i = 1; i < waypoints.size(); ++i) {
    arm.setPoseTarget(waypoints[i]);
    MoveGroupInterface::Plan cartesian_plan;
    
    if (arm.plan(cartesian_plan) == moveit::core::MoveItErrorCode::SUCCESS) {
      arm.execute(cartesian_plan);
    } else {
      RCLCPP_ERROR(logger, "Failed to plan linear path to waypoint %zu.", i);
      success = false;
      break;
    }
  }

  if (success) {
    RCLCPP_INFO(logger, "Motion Complete successfully. Shutting down.");
  } else {
    RCLCPP_ERROR(logger, "Motion failed. Shutting down.");
  }
  
  rclcpp::shutdown();
  spinner.join();
  return 0;
}
