/**
 * @file complex_motion_demo.cpp
 * @brief Complex motion demo using Cartesian paths: zig-zag, vertical sweep,
 *        and horizontal arc patterns executed with OMPL planning.
 */

#include <geometry_msgs/msg/pose.hpp>
#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <thread>
#include <vector>
#include <cmath>

using moveit::planning_interface::MoveGroupInterface;

static const double PI = M_PI;

// Helper: build a pose with tool pointing straight down (gripper facing floor)
geometry_msgs::msg::Pose make_pose(double x, double y, double z)
{
  geometry_msgs::msg::Pose p;
  p.position.x = x;
  p.position.y = y;
  p.position.z = z;
  // Orientation: tool pointing down (quaternion for 180-deg rotation around X)
  p.orientation.x = 1.0;
  p.orientation.y = 0.0;
  p.orientation.z = 0.0;
  p.orientation.w = 0.0;
  return p;
}

// Execute a Cartesian path through waypoints. Returns true on success.
bool run_cartesian(
  MoveGroupInterface & arm,
  const rclcpp::Logger & logger,
  const std::vector<geometry_msgs::msg::Pose> & waypoints,
  const std::string & label,
  double eef_step = 0.01,
  double jump_threshold = 0.0)
{
  moveit_msgs::msg::RobotTrajectory trajectory;
  double fraction = arm.computeCartesianPath(waypoints, eef_step, jump_threshold, trajectory);

  RCLCPP_INFO(logger, "[%s] Cartesian coverage: %.1f%%", label.c_str(), fraction * 100.0);

  if (fraction < 0.9) {
    RCLCPP_ERROR(logger, "[%s] Insufficient Cartesian coverage — skipping", label.c_str());
    return false;
  }

  MoveGroupInterface::Plan plan;
  plan.trajectory_ = trajectory;
  auto result = arm.execute(plan);

  if (result == moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_INFO(logger, "[%s] Execution SUCCESS", label.c_str());
    return true;
  } else {
    RCLCPP_ERROR(logger, "[%s] Execution FAILED (code %d)", label.c_str(),
      static_cast<int>(result.val));
    return false;
  }
}

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<rclcpp::Node>(
    "complex_motion_demo",
    rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true)
  );
  auto logger = rclcpp::get_logger("complex_motion_demo");

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

  RCLCPP_INFO(logger, "=== Complex Motion Demo ===");

  // ----------------------------------------------------------------
  // Step 0: Move to a known safe start pose using joint-space planning
  // ----------------------------------------------------------------
  RCLCPP_INFO(logger, "Moving to start pose...");
  arm.setNamedTarget("home");
  MoveGroupInterface::Plan start_plan;
  if (arm.plan(start_plan) == moveit::core::MoveItErrorCode::SUCCESS) {
    arm.execute(start_plan);
  }
  std::this_thread::sleep_for(std::chrono::seconds(1));

  // Working area: centered in front of the robot
  const double BASE_X = 0.25;
  const double BASE_Y = 0.0;
  const double BASE_Z = 0.30;

  // ----------------------------------------------------------------
  // Pattern 1: Zig-Zag in XY plane
  // Arm sweeps left-right while stepping forward, creating a Z pattern
  // ----------------------------------------------------------------
  RCLCPP_INFO(logger, "--- Pattern 1: Zig-Zag ---");
  {
    std::vector<geometry_msgs::msg::Pose> waypoints;

    // Start at base position
    waypoints.push_back(make_pose(BASE_X, BASE_Y, BASE_Z));

    const int steps = 5;
    const double x_step = 0.05;
    const double y_amp = 0.08;  // amplitude of zig-zag

    for (int i = 0; i <= steps; ++i) {
      double x = BASE_X + i * x_step;
      double y = (i % 2 == 0) ? BASE_Y + y_amp : BASE_Y - y_amp;
      waypoints.push_back(make_pose(x, y, BASE_Z));
    }

    run_cartesian(arm, logger, waypoints, "ZigZag");
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
  }

  // ----------------------------------------------------------------
  // Pattern 2: Vertical Up-Down sweep (like painting a wall)
  // ----------------------------------------------------------------
  RCLCPP_INFO(logger, "--- Pattern 2: Vertical Sweep ---");
  {
    std::vector<geometry_msgs::msg::Pose> waypoints;

    const double X = BASE_X + 0.05;
    const double Z_LOW = 0.20;
    const double Z_HIGH = 0.40;
    const double y_step = 0.04;
    const int cols = 4;

    for (int col = 0; col < cols; ++col) {
      double y = BASE_Y + (col - cols / 2) * y_step;
      // Alternate up/down each column
      if (col % 2 == 0) {
        waypoints.push_back(make_pose(X, y, Z_LOW));
        waypoints.push_back(make_pose(X, y, Z_HIGH));
      } else {
        waypoints.push_back(make_pose(X, y, Z_HIGH));
        waypoints.push_back(make_pose(X, y, Z_LOW));
      }
    }

    run_cartesian(arm, logger, waypoints, "VerticalSweep");
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
  }

  // ----------------------------------------------------------------
  // Pattern 3: Circular arc in the horizontal plane
  // ----------------------------------------------------------------
  RCLCPP_INFO(logger, "--- Pattern 3: Horizontal Arc ---");
  {
    std::vector<geometry_msgs::msg::Pose> waypoints;

    const double radius = 0.10;
    const int arc_points = 12;
    const double start_angle = -PI / 3;
    const double end_angle   =  PI / 3;

    for (int i = 0; i <= arc_points; ++i) {
      double angle = start_angle + (end_angle - start_angle) * i / arc_points;
      double x = BASE_X + radius * std::cos(angle);
      double y = BASE_Y + radius * std::sin(angle);
      waypoints.push_back(make_pose(x, y, BASE_Z));
    }

    run_cartesian(arm, logger, waypoints, "HorizontalArc");
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
  }

  // ----------------------------------------------------------------
  // Step 4: Return home
  // ----------------------------------------------------------------
  RCLCPP_INFO(logger, "Returning to home...");
  arm.setNamedTarget("home");
  MoveGroupInterface::Plan home_plan;
  if (arm.plan(home_plan) == moveit::core::MoveItErrorCode::SUCCESS) {
    arm.execute(home_plan);
  }

  RCLCPP_INFO(logger, "=== Complex Motion Demo Complete ===");

  rclcpp::shutdown();
  spinner.join();
  return 0;
}
