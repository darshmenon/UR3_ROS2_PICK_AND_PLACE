/**
 * @file test_dual_arm_home.cpp
 * @brief Plan and execute a move to the SRDF "home" named state, on each
 * dual-arm group in turn (left_arm, then right_arm) -- the equivalent of
 * test_planning_execution.cpp for dual_ur.srdf.xacro's per-arm groups.
 *
 * Same TOTG re-stamping fix as test_planning_execution.cpp: the OMPL response
 * adapter that stamps trajectory timestamps doesn't always load, which the
 * FollowJointTrajectory controller rejects outright without it.
 */

#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <moveit/robot_trajectory/robot_trajectory.h>
#include <moveit/trajectory_processing/time_optimal_trajectory_generation.h>
#include <thread>

namespace {

bool plan_and_execute_home(
  const rclcpp::Logger & logger,
  const rclcpp::Node::SharedPtr & node,
  const std::string & group_name)
{
  using moveit::planning_interface::MoveGroupInterface;
  auto group = MoveGroupInterface(node, group_name);

  group.setPlanningPipelineId("ompl");
  group.setPlannerId("RRTConnectkConfigDefault");
  group.setPlanningTime(5.0);
  group.setMaxVelocityScalingFactor(0.3);
  group.setMaxAccelerationScalingFactor(0.3);
  group.setNamedTarget("home");

  RCLCPP_INFO(logger, "[%s] Planning to 'home'...", group_name.c_str());

  MoveGroupInterface::Plan plan;
  if (!static_cast<bool>(group.plan(plan))) {
    RCLCPP_ERROR(logger, "[%s] Planning FAILED.", group_name.c_str());
    return false;
  }

  // Re-stamp with TOTG in case the OMPL response adapter didn't run --
  // see test_planning_execution.cpp for why this is needed.
  trajectory_processing::TimeOptimalTrajectoryGeneration totg;
  auto robot_traj = std::make_shared<robot_trajectory::RobotTrajectory>(
    group.getRobotModel(), group_name);
  robot_traj->setRobotTrajectoryMsg(*group.getCurrentState(), plan.trajectory_);
  if (!totg.computeTimeStamps(*robot_traj, 0.3, 0.3)) {
    RCLCPP_ERROR(logger, "[%s] Time parameterization FAILED.", group_name.c_str());
    return false;
  }
  robot_traj->getRobotTrajectoryMsg(plan.trajectory_);

  RCLCPP_INFO(logger, "[%s] Planning SUCCESS. Executing...", group_name.c_str());
  auto result = group.execute(plan);
  if (result != moveit::core::MoveItErrorCode::SUCCESS) {
    RCLCPP_ERROR(logger, "[%s] Execution FAILED.", group_name.c_str());
    return false;
  }

  RCLCPP_INFO(logger, "[%s] Execution SUCCESS.", group_name.c_str());
  return true;
}

}  // namespace

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);

  auto const node = std::make_shared<rclcpp::Node>(
    "test_dual_arm_home",
    rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true));
  auto const logger = rclcpp::get_logger("test_dual_arm_home");

  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  auto spinner = std::thread([&executor]() { executor.spin(); });

  bool left_ok = plan_and_execute_home(logger, node, "left_arm");
  bool right_ok = plan_and_execute_home(logger, node, "right_arm");

  if (left_ok && right_ok) {
    RCLCPP_INFO(logger, "BOTH ARMS REACHED HOME SUCCESSFULLY.");
  } else {
    RCLCPP_ERROR(logger, "AT LEAST ONE ARM FAILED (left=%s, right=%s).",
      left_ok ? "ok" : "FAILED", right_ok ? "ok" : "FAILED");
  }

  rclcpp::shutdown();
  spinner.join();
  return (left_ok && right_ok) ? 0 : 1;
}
