/**
 * @file mtc_node.cpp
 * @brief Implementation of a MoveIt Task Constructor (MTC) node for a pick and place task.
 *
 * This program implements a pick and place task using MoveIt Task Constructor (MTC).
 * It creates a planning scene, generates a series of motion stages, and executes them
 * to pick up an object from one location and place it in another.
 *
 * The node performs the following main steps:
 * 1. Set up the planning scene with collision objects
 * 2. Create an MTC task with stages for picking and placing
 * 3. Plan the task
 * 4. Optionally execute the planned task
 *
 * Input Parameters:
 * - Robot configuration (arm_group_name, gripper_group_name, etc.)
 * - Object parameters (name, dimensions, pose)
 * - Motion planning parameters (approach distances, timeouts, etc.)
 * - Execution flag (whether to execute the planned task)
 *
 * Output:
 * - Planned trajectory for the pick and place task
 * - Execution of the planned trajectory (if execution flag is set)
 * - Visualization markers for RViz
 *
 * Services Used:
 * - GetPlanningScene: Retrieves the current planning scene
 *
 * Topics Published:
 * - Various topics for trajectory execution and visualization (specific topics depend on MoveIt configuration)
 *
 * @author Addison Sears-Collins
 * @date December 20, 2024
 */

// Include necessary ROS 2 and MoveIt headers
#include <rclcpp/rclcpp.hpp>
#include <moveit_msgs/msg/collision_object.hpp>
#include <moveit/planning_scene/planning_scene.h>
#include <moveit/planning_scene_interface/planning_scene_interface.h>
#include <moveit/task_constructor/task.h>
#include <moveit/task_constructor/solvers.h>
#include <moveit/task_constructor/stages.h>
#include <moveit/task_constructor/storage.h>
#include <rclcpp_action/rclcpp_action.hpp>
#include <moveit_task_constructor_msgs/action/execute_task_solution.hpp>
#include <moveit_task_constructor_msgs/msg/solution.hpp>
#include <moveit_msgs/srv/get_planning_scene.hpp>
#include <moveit_msgs/srv/apply_planning_scene.hpp>
#include <std_srvs/srv/trigger.hpp>
#include <moveit_msgs/msg/planning_scene.hpp>
#include <moveit_msgs/msg/link_padding.hpp>

// Other utilities
#include <type_traits>
#include <numeric>
#include <cmath>
#include <chrono>
#include <algorithm>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

// Handling the GetPlanningScene service
#include "ur_mtc_pick_place_demo/get_planning_scene_client.h"
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <sensor_msgs/msg/image.hpp>

// Conditional includes for tf2 geometry messages and Eigen
#include <Eigen/Geometry>
#include <geometry_msgs/msg/pose.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2/LinearMath/Matrix3x3.h>
#if __has_include(<tf2_geometry_msgs/tf2_geometry_msgs.hpp>)
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#else
#include <tf2_geometry_msgs/tf2_geometry_msgs.h>
#endif
#if __has_include(<tf2_eigen/tf2_eigen.hpp>)
#include <tf2_eigen/tf2_eigen.hpp>
#else
#include <tf2_eigen/tf2_eigen.h>
#endif

namespace {
/**
 * @brief Transform a vector of numbers into a 3D position and orientation.
 * @param values Vector containing position and orientation values.
 * @return Eigen::Isometry3d representing the transformation.
 */
Eigen::Isometry3d vectorToEigen(const std::vector<double>& values) {
  return Eigen::Translation3d(values[0], values[1], values[2]) *
         Eigen::AngleAxisd(values[3], Eigen::Vector3d::UnitX()) *
         Eigen::AngleAxisd(values[4], Eigen::Vector3d::UnitY()) *
         Eigen::AngleAxisd(values[5], Eigen::Vector3d::UnitZ());
}

/**
 * @brief Convert a vector of numbers to a geometry_msgs::msg::Pose.
 * @param values Vector containing position and orientation values.
 * @return geometry_msgs::msg::Pose representing the pose.
 */
geometry_msgs::msg::Pose vectorToPose(const std::vector<double>& values) {
  return tf2::toMsg(vectorToEigen(values));
};

/**
 * @brief Find the stage whose name starts with `name_prefix` among the
 * (possibly nested, via WrappedSolution/SolutionSequence) solutions that
 * produced `solution` — used to report which Fallbacks grasp candidate
 * actually succeeded, since the winning branch isn't otherwise surfaced.
 */
/**
 * @brief Log every failing leaf stage's failure reasons, not just the first
 * one. Task::explainFailure() (see container.cpp's ContainerBase::
 * explainFailure) returns as soon as it finds ONE failing child — with a
 * Fallbacks container of 21 grasp candidates that all produced 0 solutions,
 * that means 20 of the 21 failure reasons are silently discarded. Distinct
 * failure comments are deduped with a count so 24 near-identical "in
 * collision" messages per candidate collapse to one line.
 */
void logAllFailures(const rclcpp::Logger& logger, const moveit::task_constructor::ContainerBase& root) {
  root.traverseRecursively([&logger](const moveit::task_constructor::Stage& stage, unsigned int /*depth*/) {
    if (!stage.solutions().empty() || stage.numFailures() == 0) {
      return true;  // keep descending; this stage isn't a failing leaf
    }
    std::map<std::string, size_t> reason_counts;
    for (const auto& failure : stage.failures()) {
      reason_counts[failure->comment()]++;
    }
    std::ostringstream reasons;
    for (const auto& [comment, count] : reason_counts) {
      reasons << "\n    (" << count << "x) " << comment;
    }
    RCLCPP_ERROR(logger, "  %s (0/%zu):%s", stage.name().c_str(), stage.numFailures(), reasons.str().c_str());
    return true;
  });
}

/**
 * @brief MTC's Connect/MoveRelative stages can legitimately return a
 * trivial "no motion needed" solution when the start state already
 * satisfies the goal: every waypoint at the same joint position, all
 * stamped time_from_start=0. That's a valid MTC solution, but
 * arm_controller's joint_trajectory_controller rejects any >=2-point
 * FollowJointTrajectory goal whose time_from_start values aren't
 * strictly increasing ("Time between points 0 and 1 is not strictly
 * increasing"), aborting the whole task execution over a stage that
 * never needed to move. Represent "no motion" the way every other
 * non-motion MTC stage (ModifyPlanningScene, ComputeIK) already is: an
 * empty trajectory, which execute_task_solution simply skips.
 */
void repairDegenerateSubTrajectories(moveit_task_constructor_msgs::msg::Solution& solution,
                                      const rclcpp::Logger& logger) {
  for (auto& sub_traj : solution.sub_trajectory) {
    auto& points = sub_traj.trajectory.joint_trajectory.points;
    if (points.size() < 2) {
      continue;
    }

    bool strictly_increasing = true;
    for (size_t i = 1; i < points.size(); ++i) {
      if (rclcpp::Duration(points[i].time_from_start) <= rclcpp::Duration(points[i - 1].time_from_start)) {
        strictly_increasing = false;
        break;
      }
    }
    if (strictly_increasing) {
      continue;
    }

    bool all_same_position = true;
    for (size_t i = 1; i < points.size(); ++i) {
      if (points[i].positions != points.front().positions) {
        all_same_position = false;
        break;
      }
    }

    if (all_same_position) {
      RCLCPP_WARN(logger,
                  "Stage %u: dropping degenerate zero-motion trajectory (%zu identical "
                  "waypoints, non-increasing times) so arm_controller doesn't reject it",
                  sub_traj.info.stage_id, points.size());
      sub_traj.trajectory.joint_trajectory.points.clear();
      sub_traj.trajectory.joint_trajectory.joint_names.clear();
      continue;
    }

    // Real (non-identical) waypoints with broken timing shouldn't happen in
    // practice, but re-stamp monotonically rather than let the controller
    // reject an otherwise-legitimate plan.
    RCLCPP_WARN(logger, "Stage %u: re-stamping non-monotonic trajectory timing (%zu points)",
                sub_traj.info.stage_id, points.size());
    rclcpp::Duration t(0, 0);
    const rclcpp::Duration step = rclcpp::Duration::from_seconds(0.1);
    for (auto& point : points) {
      point.time_from_start = t;
      t = t + step;
    }
  }
}

const moveit::task_constructor::Stage* findStageByNamePrefix(
    const moveit::task_constructor::SolutionBase& solution, const std::string& name_prefix) {
  if (solution.creator() && solution.creator()->name().rfind(name_prefix, 0) == 0) {
    return solution.creator();
  }
  if (const auto* seq = dynamic_cast<const moveit::task_constructor::SolutionSequence*>(&solution)) {
    for (const auto* sub : seq->solutions()) {
      if (const auto* found = findStageByNamePrefix(*sub, name_prefix)) {
        return found;
      }
    }
  }
  if (const auto* wrapped = dynamic_cast<const moveit::task_constructor::WrappedSolution*>(&solution)) {
    return findStageByNamePrefix(*wrapped->wrapped(), name_prefix);
  }
  return nullptr;
}
}  // namespace

// Namespace alias for MoveIt Task Constructor
namespace mtc = moveit::task_constructor;

/**
 * @brief Class representing the MTC Task Node.
 */
class MTCTaskNode : public rclcpp::Node
{
public:
  MTCTaskNode(const rclcpp::NodeOptions& options);

  bool doTask();
  void setupPlanningScene();

  // One full attempt: fresh perception read (setupPlanningScene) + fresh
  // task (createTask/plan/execute via doTask). Used for both the automatic
  // startup run and the run_pick_place service, so a BT-driven retry gets
  // the same fresh-perception, fresh-random-seed semantics as a restart.
  bool runOnePickPlaceAttempt();

private:
  mtc::Task task_;
  mtc::Task createTask();

  void handleRunPickPlace(const std::shared_ptr<std_srvs::srv::Trigger::Request> request,
                          std::shared_ptr<std_srvs::srv::Trigger::Response> response);

  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr run_pick_place_service_;

  // Builds the same goal message Task::execute() would, but repairs any
  // degenerate zero-motion sub-trajectories first (see
  // repairDegenerateSubTrajectories) before sending it to
  // execute_task_solution — Task::execute() builds and sends that message
  // internally, giving us no hook to patch it otherwise.
  moveit::core::MoveItErrorCode executeSolution(const mtc::SolutionBase& solution);

  void updateObjectParameters(const moveit_msgs::msg::CollisionObject& collision_object);

  bool waitForMoveGroupServices(double timeout_sec);
  bool isSupportSurfaceSane(const moveit_msgs::msg::CollisionObject& support,
                            double support_min_z, double support_max_xy_area) const;
  void installFallbackSupportAndTarget(moveit::planning_interface::PlanningSceneInterface& psi);
  void applyPlanningPadding();

  // Variables for calling the GetPlanningScene service
  std::shared_ptr<GetPlanningSceneClient> planning_scene_client;
  moveit_msgs::msg::PlanningSceneWorld scene_world_;
  sensor_msgs::msg::PointCloud2 full_cloud_;
  sensor_msgs::msg::Image rgb_image_;
  std::string target_object_id_;
  std::string support_surface_id_;
  bool service_success_;
};

/**
 * @brief Constructor for the MTCTaskNode class.
 * @param options Node options for configuration.
 */
MTCTaskNode::MTCTaskNode(const rclcpp::NodeOptions& options)
  : Node("mtc_node", options)
{
  auto declare_parameter = [this](const std::string& name, const auto& default_value, const std::string& description = "") {
    rcl_interfaces::msg::ParameterDescriptor descriptor;
    descriptor.description = description;

    if (!this->has_parameter(name)) {
      this->declare_parameter(name, default_value, descriptor);
    }
  };

  // General parameters
  declare_parameter("execute", true, "Whether to execute the planned task");
  declare_parameter("max_solutions", 25, "Maximum number of solutions to compute");
  // Failures seen this project are RRTConnect random-seed variance (a
  // different link/obstacle grazed each run, ~25% raw success rate observed
  // 2026-08-08 across 4 real-perception runs), not a deterministic bug.
  // Retry-on-failure is handled at the BT layer (ur_bt_planner's
  // RunMTCPickPlace leaf + a Retry decorator) via the run_pick_place
  // service below, not inside this node — each service call is one fresh
  // attempt (new perception read, new random seed).
  declare_parameter("auto_run_on_startup", true,
                    "Run one pick-place attempt automatically at launch, in addition to the run_pick_place service");

  // Controller parameters
  declare_parameter("controller_names", std::vector<std::string>{"arm_controller", "gripper_controller"}, "Names of the controllers to use");

  // Robot configuration parameters
  declare_parameter("arm_group_name", "arm", "Name of the arm group in the SRDF");
  declare_parameter("gripper_group_name", "gripper", "Name of the gripper group in the SRDF");
  declare_parameter("gripper_frame", "robotiq_arg2f_base_link", "Name of the gripper frame");
  declare_parameter("gripper_open_pose", "open", "Name of the gripper open pose");
  declare_parameter("gripper_close_pose", "half_closed", "Name of the gripper closed pose");
  declare_parameter("arm_home_pose", "home", "Name of the arm home pose");
  declare_parameter("arm_transit_clear_pose", "transit_clear",
                    "Named joint-space via that clears the pick-table corridor");
  declare_parameter("use_transit_clear_via", true,
                    "Insert MoveTo(transit_clear) before pick/place Connect stages");
  declare_parameter("transit_planner_id", "RRTConnectkConfigDefault",
                    "OMPL planner_id for narrow-passage transit (Connect + via MoveTo)");
  declare_parameter("planning_robot_padding", 0.004,
                    "Extra robot link padding (m) applied to the planning scene");
  declare_parameter("planning_support_inflation", 0.005,
                    "Grow fallback support box XY/Z by this many metres for planning margin");

  // Scene frame parameters
  declare_parameter("world_frame", "base_link", "Name of the world frame");

  // Object parameters
  declare_parameter("object_name", "object", "Name of the object to be manipulated");
  declare_parameter("object_type", "cylinder", "Type of the object to be manipulated");
  declare_parameter("object_reference_frame", "base_link", "Reference frame for the object");
  declare_parameter("object_dimensions", std::vector<double>{0.35, 0.0125}, "Dimensions of the object [height, radius]");
  declare_parameter("object_pose", std::vector<double>{0.22, 0.12, 0.0, 0.0, 0.0, 0.0}, "Initial pose of the object [x, y, z, roll, pitch, yaw]");
  declare_parameter("fallback_support_dimensions", std::vector<double>{0.30, 0.45, 0.04},
                    "Fallback support surface box [x, y, z] in metres");
  declare_parameter("fallback_support_pose", std::vector<double>{0.275, 0.04, 0.02, 0.0, 0.0, 0.0},
                    "Fallback support surface pose [x, y, z, roll, pitch, yaw] in object_reference_frame");
  declare_parameter("force_fallback_scene", true,
                    "If true, ignore perception collision objects and install fallback table+target");
  declare_parameter("support_min_z", 0.015,
                    "Reject perceived support whose top face is below this z in object_reference_frame");
  declare_parameter("support_max_xy_area", 0.25,
                    "Reject perceived support whose XY area (m^2) exceeds this (mount_table is ~0.4)");
  declare_parameter("move_group_wait_timeout", 30.0,
                    "Seconds to wait for /get_planning_scene and /apply_planning_scene before aborting setup");

  // Grasp and place parameters
declare_parameter("grasp_frame_transform", 
  std::vector<double>{0.0, 0.0, 0.12, 0.0, 1.5708, 0.0}, "Transform from gripper frame to grasp frame [x, y, z, roll, pitch, yaw]");
  declare_parameter("place_pose", std::vector<double>{-0.183, -0.14, 0.0, 0.0, 0.0, 0.0}, "Pose where the object should be placed [x, y, z, roll, pitch, yaw]");

  // Motion planning parameters
  declare_parameter("approach_object_min_dist", 0.0015, "Minimum approach distance to the object");
  declare_parameter("approach_object_max_dist", 0.3, "Maximum approach distance to the object");
  declare_parameter("lift_object_min_dist", 0.005, "Minimum lift distance for the object");
  declare_parameter("lift_object_max_dist", 0.3, "Maximum lift distance for the object");
  declare_parameter("lower_object_min_dist", 0.005, "Minimum distance for lowering object");
  declare_parameter("lower_object_max_dist", 0.4, "Maximum distance for lowering object");

  // Timeout parameters
  declare_parameter("move_to_pick_timeout", 10.0, "Timeout for move to pick stage (seconds)");
  declare_parameter("move_to_place_timeout", 10.0, "Timeout for move to place stage (seconds)");

  // Grasp generation parameters
  declare_parameter("grasp_pose_angle_delta", 0.1309, "Angular resolution for sampling grasp poses (radians)");
  declare_parameter("grasp_pose_max_ik_solutions", 25, "Maximum number of IK solutions for grasp pose generation");
  declare_parameter("grasp_pose_min_solution_distance", 0.5, "Minimum distance in joint-space units between IK solutions for grasp pose");

  // Place generation parameters
  declare_parameter("place_pose_max_ik_solutions", 10, "Maximum number of IK solutions for place pose generation");

  // Cartesian planner parameters
  declare_parameter("cartesian_max_velocity_scaling", 1.0, "Max velocity scaling factor for Cartesian planner");
  declare_parameter("cartesian_max_acceleration_scaling", 1.0, "Max acceleration scaling factor for Cartesian planner");
  declare_parameter("cartesian_step_size", 0.00025, "Step size for Cartesian planner");

  // Direction vector parameters
  declare_parameter("approach_object_direction_z", 1.0, "Z component of approach object direction vector");
  declare_parameter("lift_object_direction_z", 1.0, "Z component of lift object direction vector");
  declare_parameter("lower_object_direction_z", -1.0, "Z component of lower object direction vector");
  declare_parameter("retreat_direction_z", -1.0, "Z component of retreat direction vector");

  // Other parameters
  declare_parameter("place_pose_z_offset_factor", 0.5, "Factor to multiply object height for place pose Z offset");
  declare_parameter("retreat_min_distance", 0.025, "Minimum distance for retreat motion");
  declare_parameter("retreat_max_distance", 0.25, "Maximum distance for retreat motion");

  RCLCPP_INFO(this->get_logger(), "All parameters have been declared with descriptions");

  // Initialize the planning scene client
  planning_scene_client = std::make_shared<GetPlanningSceneClient>();

  // Lets a BT leaf (ur_bt_planner) trigger one fresh attempt on demand and
  // retry on failure — see runOnePickPlaceAttempt().
  run_pick_place_service_ = this->create_service<std_srvs::srv::Trigger>(
    "run_pick_place",
    std::bind(&MTCTaskNode::handleRunPickPlace, this, std::placeholders::_1, std::placeholders::_2));
}

void MTCTaskNode::handleRunPickPlace(const std::shared_ptr<std_srvs::srv::Trigger::Request> /*request*/,
                                     std::shared_ptr<std_srvs::srv::Trigger::Response> response)
{
  bool ok = runOnePickPlaceAttempt();
  response->success = ok;
  response->message = ok ? "Task executed successfully" : "Task failed (see mtc_node log for the reason)";
}

bool MTCTaskNode::runOnePickPlaceAttempt()
{
  RCLCPP_INFO(this->get_logger(), "Setting up planning scene");
  setupPlanningScene();
  RCLCPP_INFO(this->get_logger(), "Executing task");
  return doTask();
}

/**
 * @brief Update the target object parameters after the service call to get planning scene
 */
void MTCTaskNode::updateObjectParameters(const moveit_msgs::msg::CollisionObject& collision_object) {
  // Update object_name
  this->set_parameter(rclcpp::Parameter("object_name", collision_object.id));
  RCLCPP_INFO(this->get_logger(), "Updated object_name: '%s'", collision_object.id.c_str());

  // Update object_type and object_dimensions
  if (!collision_object.primitives.empty()) {
    std::vector<double> dimensions;
    std::string object_type;
    if (collision_object.primitives[0].type == shape_msgs::msg::SolidPrimitive::CYLINDER) {
      object_type = "cylinder";
      dimensions = {
        collision_object.primitives[0].dimensions[shape_msgs::msg::SolidPrimitive::CYLINDER_HEIGHT],
        collision_object.primitives[0].dimensions[shape_msgs::msg::SolidPrimitive::CYLINDER_RADIUS]
      };
    } else if (collision_object.primitives[0].type == shape_msgs::msg::SolidPrimitive::BOX) {
      object_type = "box";
      dimensions = {
        collision_object.primitives[0].dimensions[shape_msgs::msg::SolidPrimitive::BOX_X],
        collision_object.primitives[0].dimensions[shape_msgs::msg::SolidPrimitive::BOX_Y],
        collision_object.primitives[0].dimensions[shape_msgs::msg::SolidPrimitive::BOX_Z]
      };
    } else {
      RCLCPP_WARN(this->get_logger(), "Unsupported object type. Only cylinders and boxes are supported.");
      return;
    }
    this->set_parameter(rclcpp::Parameter("object_type", object_type));
    this->set_parameter(rclcpp::Parameter("object_dimensions", dimensions));
    RCLCPP_INFO(this->get_logger(), "Updated object_type: '%s'", object_type.c_str());
    RCLCPP_INFO(this->get_logger(), "Updated object_dimensions: [%s]",
                std::accumulate(std::next(dimensions.begin()), dimensions.end(),
                                std::to_string(dimensions[0]),
                                [](std::string a, double b) {
                                  return std::move(a) + ", " + std::to_string(b);
                                }).c_str());
  }
}

bool MTCTaskNode::waitForMoveGroupServices(double timeout_sec)
{
  auto get_client = this->create_client<moveit_msgs::srv::GetPlanningScene>("/get_planning_scene");
  auto apply_client = this->create_client<moveit_msgs::srv::ApplyPlanningScene>("/apply_planning_scene");
  const auto deadline =
      std::chrono::steady_clock::now() + std::chrono::duration<double>(timeout_sec);

  RCLCPP_INFO(this->get_logger(),
              "Waiting up to %.1fs for /get_planning_scene and /apply_planning_scene...",
              timeout_sec);
  while (rclcpp::ok() && std::chrono::steady_clock::now() < deadline) {
    if (get_client->service_is_ready() && apply_client->service_is_ready()) {
      RCLCPP_INFO(this->get_logger(), "move_group planning-scene services are ready");
      return true;
    }
    rclcpp::sleep_for(std::chrono::milliseconds(200));
  }
  RCLCPP_ERROR(this->get_logger(),
               "Timed out after %.1fs waiting for move_group planning-scene services. "
               "Is move_group running on this ROS_DOMAIN_ID?",
               timeout_sec);
  return false;
}

bool MTCTaskNode::isSupportSurfaceSane(const moveit_msgs::msg::CollisionObject& support,
                                       double support_min_z, double support_max_xy_area) const
{
  if (support.primitives.empty() || support.primitive_poses.empty()) {
    return false;
  }
  const auto& prim = support.primitives.front();
  const auto& pose = support.primitive_poses.front();
  if (prim.type != shape_msgs::msg::SolidPrimitive::BOX || prim.dimensions.size() < 3) {
    return false;
  }
  const double xy_area = prim.dimensions[0] * prim.dimensions[1];
  const double top_z = pose.position.z + 0.5 * prim.dimensions[2];
  if (top_z < support_min_z) {
    RCLCPP_WARN(this->get_logger(),
                "Support '%s' top_z=%.4f < support_min_z=%.4f (likely mount_table)",
                support.id.c_str(), top_z, support_min_z);
    return false;
  }
  if (xy_area > support_max_xy_area) {
    RCLCPP_WARN(this->get_logger(),
                "Support '%s' XY area=%.3f m^2 > max=%.3f (likely mount_table)",
                support.id.c_str(), xy_area, support_max_xy_area);
    return false;
  }
  return true;
}

void MTCTaskNode::installFallbackSupportAndTarget(
    moveit::planning_interface::PlanningSceneInterface& psi)
{
  auto object_name = this->get_parameter("object_name").as_string();
  auto object_type = this->get_parameter("object_type").as_string();
  auto object_dimensions = this->get_parameter("object_dimensions").as_double_array();
  auto object_pose_param = this->get_parameter("object_pose").as_double_array();
  auto object_reference_frame = this->get_parameter("object_reference_frame").as_string();
  auto support_dims = this->get_parameter("fallback_support_dimensions").as_double_array();
  auto support_pose = this->get_parameter("fallback_support_pose").as_double_array();

  std::vector<std::string> remove_ids = psi.getKnownObjectNames();
  for (const auto& collision_object : scene_world_.collision_objects) {
    if (std::find(remove_ids.begin(), remove_ids.end(), collision_object.id) == remove_ids.end()) {
      remove_ids.push_back(collision_object.id);
    }
  }
  if (!remove_ids.empty()) {
    RCLCPP_WARN(this->get_logger(),
                "Removing %zu collision object(s) before inserting fallback support+target",
                remove_ids.size());
    psi.removeCollisionObjects(remove_ids);
    rclcpp::sleep_for(std::chrono::milliseconds(500));
  }

  if (support_surface_id_.empty()) {
    support_surface_id_ = "support_surface";
  }

  moveit_msgs::msg::CollisionObject support;
  support.id = support_surface_id_;
  support.header.frame_id = object_reference_frame;
  support.operation = moveit_msgs::msg::CollisionObject::ADD;
  shape_msgs::msg::SolidPrimitive support_prim;
  support_prim.type = shape_msgs::msg::SolidPrimitive::BOX;
  const double inflate = this->get_parameter("planning_support_inflation").as_double();
  const double sx = (support_dims.size() > 0 ? support_dims[0] : 0.30) + 2.0 * inflate;
  const double sy = (support_dims.size() > 1 ? support_dims[1] : 0.45) + 2.0 * inflate;
  const double sz = (support_dims.size() > 2 ? support_dims[2] : 0.04) + 2.0 * inflate;
  support_prim.dimensions = {sx, sy, sz};
  support.primitives.push_back(support_prim);
  // Keep XY center; raise Z so the top face rises by `inflate` (bottom drops by same).
  auto inflated_pose = support_pose;
  if (inflated_pose.size() >= 3) {
    inflated_pose[2] = support_pose[2];  // center unchanged; half-height grew equally
  }
  support.primitive_poses.push_back(vectorToPose(inflated_pose));
  if (inflate > 0.0) {
    RCLCPP_INFO(this->get_logger(),
                "Inflated fallback support by %.3fm for planning margin (size now [%.3f, %.3f, %.3f])",
                inflate, sx, sy, sz);
  }

  moveit_msgs::msg::CollisionObject fallback;
  fallback.id = object_name;
  fallback.header.frame_id = object_reference_frame;
  fallback.operation = moveit_msgs::msg::CollisionObject::ADD;

  shape_msgs::msg::SolidPrimitive prim;
  if (object_type == "cylinder") {
    prim.type = shape_msgs::msg::SolidPrimitive::CYLINDER;
    prim.dimensions.resize(2);
    prim.dimensions[shape_msgs::msg::SolidPrimitive::CYLINDER_HEIGHT] = object_dimensions[0];
    prim.dimensions[shape_msgs::msg::SolidPrimitive::CYLINDER_RADIUS] = object_dimensions[1];
  } else {
    prim.type = shape_msgs::msg::SolidPrimitive::BOX;
    prim.dimensions.resize(3);
    prim.dimensions[0] = object_dimensions[0];
    prim.dimensions[1] = (object_dimensions.size() > 1) ? object_dimensions[1] : object_dimensions[0];
    prim.dimensions[2] = (object_dimensions.size() > 2) ? object_dimensions[2] : object_dimensions[0];
  }
  fallback.primitives.push_back(prim);
  fallback.primitive_poses.push_back(vectorToPose(object_pose_param));

  psi.addCollisionObjects({support, fallback});
  rclcpp::sleep_for(std::chrono::milliseconds(3000));
  RCLCPP_INFO(this->get_logger(),
              "Fallback support '%s' at (%.3f, %.3f, %.3f) size [%.3f, %.3f, %.3f]",
              support.id.c_str(), support_pose[0], support_pose[1], support_pose[2],
              support_prim.dimensions[0], support_prim.dimensions[1], support_prim.dimensions[2]);
  RCLCPP_INFO(this->get_logger(), "Fallback object '%s' added at (%.3f, %.3f, %.3f)",
              object_name.c_str(), object_pose_param[0], object_pose_param[1], object_pose_param[2]);
  target_object_id_ = object_name;
}

/**
 * @brief Set up the planning scene with collision objects.
 */
void MTCTaskNode::setupPlanningScene()
{
  const double wait_timeout = this->get_parameter("move_group_wait_timeout").as_double();
  if (!waitForMoveGroupServices(wait_timeout)) {
    throw std::runtime_error(
        "move_group planning-scene services unavailable; aborting setupPlanningScene");
  }

  moveit::planning_interface::PlanningSceneInterface psi;

  auto stale_object_ids = psi.getKnownObjectNames();
  if (!stale_object_ids.empty()) {
    RCLCPP_INFO(this->get_logger(), "Clearing %zu stale collision object(s) from a previous run",
                stale_object_ids.size());
    psi.removeCollisionObjects(stale_object_ids);
    rclcpp::sleep_for(std::chrono::milliseconds(500));
  }

  auto object_name = this->get_parameter("object_name").as_string();
  auto object_type = this->get_parameter("object_type").as_string();
  auto object_dimensions = this->get_parameter("object_dimensions").as_double_array();
  auto object_reference_frame = this->get_parameter("object_reference_frame").as_string();
  const bool force_fallback = this->get_parameter("force_fallback_scene").as_bool();
  const double support_min_z = this->get_parameter("support_min_z").as_double();
  const double support_max_xy_area = this->get_parameter("support_max_xy_area").as_double();

  RCLCPP_INFO(this->get_logger(), "Initial target object parameters:");
  RCLCPP_INFO(this->get_logger(), "  Name: %s", object_name.c_str());
  RCLCPP_INFO(this->get_logger(), "  Type: %s", object_type.c_str());
  RCLCPP_INFO(this->get_logger(), "  Dimensions: [%s]",
              std::accumulate(std::next(object_dimensions.begin()), object_dimensions.end(),
                              std::to_string(object_dimensions[0]),
                              [](std::string a, double b) {
                                return std::move(a) + ", " + std::to_string(b);
                              }).c_str());
  RCLCPP_INFO(this->get_logger(), "  Reference frame: %s", object_reference_frame.c_str());
  RCLCPP_INFO(this->get_logger(), "  force_fallback_scene: %s", force_fallback ? "true" : "false");

  bool use_fallback = force_fallback;
  std::string fallback_reason = force_fallback ? "force_fallback_scene=true" : "";

  if (!force_fallback) {
    RCLCPP_INFO(this->get_logger(), "Sending GetPlanningScene service request...");
    auto response = planning_scene_client->call_service(object_type, object_dimensions);
    RCLCPP_INFO(this->get_logger(), "Service call to the GetPlanningScene service completed.");

    scene_world_ = response.scene_world;
    full_cloud_ = response.full_cloud;
    rgb_image_ = response.rgb_image;
    target_object_id_ = response.target_object_id;
    support_surface_id_ = response.support_surface_id;
    service_success_ = response.success;

    RCLCPP_INFO(this->get_logger(),
                "Adding %zu collision objects from service response to the planning scene...",
                scene_world_.collision_objects.size());
    if (!scene_world_.collision_objects.empty()) {
      psi.addCollisionObjects(scene_world_.collision_objects);
      rclcpp::sleep_for(std::chrono::milliseconds(3000));
      RCLCPP_INFO(this->get_logger(), "Successfully added %zu collision objects to the planning scene",
                  scene_world_.collision_objects.size());
    }

    RCLCPP_INFO(this->get_logger(), "Received target_object_id from service: '%s'",
                target_object_id_.c_str());
    for (const auto& collision_object : scene_world_.collision_objects) {
      if (collision_object.id == target_object_id_) {
        updateObjectParameters(collision_object);
        break;
      }
    }

    if (target_object_id_.empty()) {
      use_fallback = true;
      fallback_reason = "no target object from perception";
    } else {
      const moveit_msgs::msg::CollisionObject* support_ptr = nullptr;
      for (const auto& collision_object : scene_world_.collision_objects) {
        if (collision_object.id == support_surface_id_) {
          support_ptr = &collision_object;
          break;
        }
      }
      if (!support_ptr) {
        use_fallback = true;
        fallback_reason = "missing support_surface in perception response";
      } else if (!isSupportSurfaceSane(*support_ptr, support_min_z, support_max_xy_area)) {
        use_fallback = true;
        fallback_reason = "perceived support_surface failed sanity checks";
      }
    }
  } else {
    support_surface_id_ = "support_surface";
    service_success_ = false;
  }

  if (use_fallback) {
    RCLCPP_WARN(this->get_logger(), "Using fallback pick-table scene (%s).", fallback_reason.c_str());
    installFallbackSupportAndTarget(psi);
  }

  applyPlanningPadding();

  RCLCPP_INFO(this->get_logger(), "Planning scene setup completed");
}

void MTCTaskNode::applyPlanningPadding()
{
  const double padding = this->get_parameter("planning_robot_padding").as_double();
  if (padding <= 0.0) {
    return;
  }

  // Links that graze the pick table during transit. Do NOT pad finger pads —
  // 8mm there falsely collides with torso_link at folded configs.
  static const char* kPaddedLinks[] = {
      "forearm_link", "wrist_1_link", "wrist_2_link", "wrist_3_link",
      "upper_arm_link", "tool0", "robotiq_arg2f_base_link",
  };

  moveit_msgs::msg::PlanningScene scene_msg;
  scene_msg.is_diff = true;
  for (const char* link : kPaddedLinks) {
    moveit_msgs::msg::LinkPadding lp;
    lp.link_name = link;
    lp.padding = padding;
    scene_msg.link_padding.push_back(lp);
  }

  moveit::planning_interface::PlanningSceneInterface psi;
  if (!psi.applyPlanningScene(scene_msg)) {
    RCLCPP_WARN(this->get_logger(), "Failed to apply %.3fm planning link padding", padding);
    return;
  }
  RCLCPP_INFO(this->get_logger(),
              "Applied %.3fm planning padding to %zu robot links (coarse-plan / fine-margin)",
              padding, scene_msg.link_padding.size());
}

/**
 * @brief Plan and/or execute the pick and place task.
 */
moveit::core::MoveItErrorCode MTCTaskNode::executeSolution(const mtc::SolutionBase& solution)
{
  using ExecuteTaskSolution = moveit_task_constructor_msgs::action::ExecuteTaskSolution;

  moveit_task_constructor_msgs::msg::Solution solution_msg;
  solution.toMsg(solution_msg, &task_.introspection());
  repairDegenerateSubTrajectories(solution_msg, this->get_logger());

  auto client_node = rclcpp::Node::make_shared("mtc_execute_repaired_" + std::to_string(this->now().nanoseconds()));
  auto client = rclcpp_action::create_client<ExecuteTaskSolution>(client_node, "execute_task_solution");

  moveit_msgs::msg::MoveItErrorCodes error_code;
  error_code.val = moveit_msgs::msg::MoveItErrorCodes::FAILURE;

  if (!client->wait_for_action_server(std::chrono::milliseconds(500))) {
    RCLCPP_ERROR(this->get_logger(), "Failed to connect to the 'execute_task_solution' action server");
    return error_code;
  }

  ExecuteTaskSolution::Goal goal;
  goal.solution = solution_msg;

  auto goal_handle_future = client->async_send_goal(goal);
  if (rclcpp::spin_until_future_complete(client_node, goal_handle_future) != rclcpp::FutureReturnCode::SUCCESS) {
    RCLCPP_ERROR(this->get_logger(), "Send goal call failed");
    return error_code;
  }

  auto goal_handle = goal_handle_future.get();
  if (!goal_handle) {
    RCLCPP_ERROR(this->get_logger(), "Goal was rejected by server");
    return error_code;
  }

  auto result_future = client->async_get_result(goal_handle);
  // Full pick-place has many sub-trajectories; 120s was too short once the
  // arm actually starts moving under Gazebo.
  if (rclcpp::spin_until_future_complete(client_node, result_future, std::chrono::seconds(300)) !=
      rclcpp::FutureReturnCode::SUCCESS) {
    RCLCPP_ERROR(this->get_logger(), "Get result call failed or timed out");
    return error_code;
  }

  auto result = result_future.get();
  if (result.code != rclcpp_action::ResultCode::SUCCEEDED) {
    RCLCPP_ERROR(this->get_logger(), "Goal was aborted or canceled");
  }
  return result.result->error_code;
}

bool MTCTaskNode::doTask()
{
  RCLCPP_INFO(this->get_logger(), "Starting the pick and place task");

  task_ = createTask();

  // Get parameters
  auto execute = this->get_parameter("execute").as_bool();
  auto max_solutions = this->get_parameter("max_solutions").as_int();

  try
  {
    task_.init();
    RCLCPP_INFO(this->get_logger(), "Task initialized successfully");
  }
  catch (mtc::InitStageException& e)
  {
    // e.what() is just a placeholder ("...RCLCPP_ERROR_STREAM(e) for details") —
    // the real per-stage error text is only available via operator<<.
    std::ostringstream init_error;
    init_error << e;
    RCLCPP_ERROR(this->get_logger(), "Task initialization failed:\n%s", init_error.str().c_str());
    return false;
  }

  // Attempt to plan the task
  if (!task_.plan(max_solutions))
  {
    RCLCPP_ERROR(this->get_logger(), "Task planning failed");
    // Task::plan() already calls printState()/explainFailure() internally, but
    // that goes to a buffered std::cout that never flushes before this process
    // is killed (it stays alive afterward for visualization) — re-run them here
    // targeting a stream we actually log, so the failure reason is visible.
    std::ostringstream diagnostics;
    task_.printState(diagnostics);
    RCLCPP_ERROR(this->get_logger(), "Task failure diagnostics:\n%s", diagnostics.str().c_str());
    // task_.explainFailure() only reports the FIRST failing child it finds
    // (see ContainerBase::explainFailure in container.cpp) — with a
    // Fallbacks container of many grasp candidates that all fail, that
    // hides every reason but the first. Walk the whole tree instead.
    RCLCPP_ERROR(this->get_logger(), "Failing stage(s), all leaves:");
    logAllFailures(this->get_logger(), *task_.stages());
    return false;
  }

  RCLCPP_INFO(this->get_logger(), "Task planning succeeded");

  // Report which grasp candidate (see "Generate Grasp Pose" in createTask())
  // actually won, since the Fallbacks container otherwise hides this.
  if (const auto* winning_stage = findStageByNamePrefix(*task_.solutions().front(), "grasp pose IK ")) {
    RCLCPP_INFO(this->get_logger(), "Winning grasp candidate: %s", winning_stage->name().c_str());
  }

  // Publish the planned solution for visualization
  task_.introspection().publishSolution(*task_.solutions().front());
  RCLCPP_INFO(this->get_logger(), "Published solution for visualization");

  if (!execute)
  {
    RCLCPP_INFO(this->get_logger(), "Execution skipped as per configuration");
    return true;
  }

  // Execute the planned task
  RCLCPP_INFO(this->get_logger(), "Executing the planned task");
  auto result = executeSolution(*task_.solutions().front());
  if (result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS)
  {
    RCLCPP_ERROR(this->get_logger(), "Task execution failed with error code: %d", result.val);
    return false;
  }
  RCLCPP_INFO(this->get_logger(), "Task executed successfully");
  return true;
}

/**
 * @brief Create the MTC task with all necessary stages.
 * @return The created MTC task.
 */
mtc::Task MTCTaskNode::createTask()
{
  RCLCPP_INFO(this->get_logger(), "Creating MTC task");

  // Create a new Task
  mtc::Task task;

  // Set the name of the task
  task.stages()->setName("pick_place_task");

  // Load the robot model into the task
  task.loadRobotModel(shared_from_this(), "robot_description");

  // Get parameters
  // Robot configuration parameters
  auto arm_group_name = this->get_parameter("arm_group_name").as_string();
  auto gripper_group_name = this->get_parameter("gripper_group_name").as_string();
  auto gripper_frame = this->get_parameter("gripper_frame").as_string();
  auto arm_home_pose = this->get_parameter("arm_home_pose").as_string();
  auto arm_transit_clear_pose = this->get_parameter("arm_transit_clear_pose").as_string();
  const bool use_transit_clear_via = this->get_parameter("use_transit_clear_via").as_bool();
  auto transit_planner_id = this->get_parameter("transit_planner_id").as_string();

  // Gripper poses
  auto gripper_open_pose = this->get_parameter("gripper_open_pose").as_string();
  auto gripper_close_pose = this->get_parameter("gripper_close_pose").as_string();

  // Frame parameters
  auto world_frame = this->get_parameter("world_frame").as_string();

  // Controller parameters
  auto controller_names = this->get_parameter("controller_names").as_string_array();

  // Object parameters
  auto object_name = this->get_parameter("object_name").as_string();
  auto object_type = this->get_parameter("object_type").as_string();
  auto object_reference_frame = this->get_parameter("object_reference_frame").as_string();
  auto object_dimensions = this->get_parameter("object_dimensions").as_double_array();
  auto object_pose = this->get_parameter("object_pose").as_double_array();

  // object_dimensions is [height, radius] for a cylinder but [x, y, z] for a
  // box (shape_msgs::SolidPrimitive convention, see prim.dimensions[0..2]
  // below) — dimensions[0] is only the object's height for a cylinder, so
  // callers that want "how tall is this object" must branch on object_type
  // rather than always reading dimensions[0].
  double object_height = 0.0;
  if (object_type == "cylinder" && !object_dimensions.empty()) {
    object_height = object_dimensions[0];
  } else if (object_type == "box" && object_dimensions.size() >= 3) {
    object_height = object_dimensions[2];  // z is up
  }

  RCLCPP_INFO(this->get_logger(), "Creating task for object:");
  RCLCPP_INFO(this->get_logger(), "  Name: %s", object_name.c_str());
  RCLCPP_INFO(this->get_logger(), "  Type: %s", object_type.c_str());
  RCLCPP_INFO(this->get_logger(), "  Dimensions: [%s]",
              std::accumulate(std::next(object_dimensions.begin()), object_dimensions.end(),
                              std::to_string(object_dimensions[0]),
                              [](std::string a, double b) {
                                return std::move(a) + ", " + std::to_string(b);
                              }).c_str());
  RCLCPP_INFO(this->get_logger(), "  Resolved height (type-aware): %.4f m", object_height);

  // Grasp and place parameters
  auto grasp_frame_transform = this->get_parameter("grasp_frame_transform").as_double_array();
  auto place_pose = this->get_parameter("place_pose").as_double_array();

  // Motion planning parameters
  auto approach_object_min_dist = this->get_parameter("approach_object_min_dist").as_double();
  auto approach_object_max_dist = this->get_parameter("approach_object_max_dist").as_double();
  auto lift_object_min_dist = this->get_parameter("lift_object_min_dist").as_double();
  auto lift_object_max_dist = this->get_parameter("lift_object_max_dist").as_double();
  auto lower_object_min_dist = this->get_parameter("lower_object_min_dist").as_double();
  auto lower_object_max_dist = this->get_parameter("lower_object_max_dist").as_double();

  // Timeout parameters
  auto move_to_pick_timeout = this->get_parameter("move_to_pick_timeout").as_double();
  auto move_to_place_timeout = this->get_parameter("move_to_place_timeout").as_double();

  // Grasp generation parameters
  auto grasp_pose_angle_delta = this->get_parameter("grasp_pose_angle_delta").as_double();
  (void)grasp_pose_angle_delta;  // retained param; absolute grasp ladder sets yaw explicitly
  auto grasp_pose_max_ik_solutions = this->get_parameter("grasp_pose_max_ik_solutions").as_int();
  auto grasp_pose_min_solution_distance = this->get_parameter("grasp_pose_min_solution_distance").as_double();

  // Place generation parameters
  auto place_pose_max_ik_solutions = this->get_parameter("place_pose_max_ik_solutions").as_int();

  // Cartesian planner parameters
  auto cartesian_max_velocity_scaling = this->get_parameter("cartesian_max_velocity_scaling").as_double();
  auto cartesian_max_acceleration_scaling = this->get_parameter("cartesian_max_acceleration_scaling").as_double();
  auto cartesian_step_size = this->get_parameter("cartesian_step_size").as_double();

  // Direction vector parameters
  auto approach_object_direction_z = this->get_parameter("approach_object_direction_z").as_double();
  auto lift_object_direction_z = this->get_parameter("lift_object_direction_z").as_double();
  auto lower_object_direction_z = this->get_parameter("lower_object_direction_z").as_double();
  auto retreat_direction_z = this->get_parameter("retreat_direction_z").as_double();

  // Other parameters
  auto place_pose_z_offset_factor = this->get_parameter("place_pose_z_offset_factor").as_double();
  auto retreat_min_distance = this->get_parameter("retreat_min_distance").as_double();
  auto retreat_max_distance = this->get_parameter("retreat_max_distance").as_double();

  // Create planners for different types of motion
  // OMPL planner (generic — approach/retreat may still fall back to this)
  auto ompl_planner_arm = std::make_shared<mtc::solvers::PipelinePlanner>(
    this->shared_from_this(),
    "ompl");
  RCLCPP_INFO(this->get_logger(), "OMPL planner created for the arm group");

  // Narrow-passage transit planner for Connect stages. Prefer a concrete
  // planner config (RRTConnectkConfigDefault / LBKPIECEkConfigDefault) —
  // APS with LBKPIECE in its planners string fails with
  // "No projection evaluator specified" under MoveIt/OMPL.
  auto ompl_planner_transit = std::make_shared<mtc::solvers::PipelinePlanner>(
    this->shared_from_this(),
    "ompl");
  ompl_planner_transit->setPlannerId(transit_planner_id);
  RCLCPP_INFO(this->get_logger(), "Transit OMPL planner_id='%s'", transit_planner_id.c_str());

  // JointInterpolation is a basic planner that is used for simple motions
  // It computes quickly but doesn't support complex motions.
  auto interpolation_planner = std::make_shared<mtc::solvers::JointInterpolationPlanner>();
  RCLCPP_INFO(this->get_logger(), "Joint Interpolation planner created for the gripper group");

  // Cartesian planner
  auto cartesian_planner = std::make_shared<mtc::solvers::CartesianPath>();
  cartesian_planner->setMaxVelocityScalingFactor(cartesian_max_velocity_scaling);
  cartesian_planner->setMaxAccelerationScalingFactor(cartesian_max_acceleration_scaling);
  cartesian_planner->setStepSize(cartesian_step_size);
  RCLCPP_INFO(this->get_logger(), "Cartesian planner created");

  // Set task properties
  task.setProperty("group", arm_group_name); // The main planning group
  task.setProperty("eef", gripper_group_name); // The end-effector group
  task.setProperty("ik_frame", gripper_frame); // The frame for inverse kinematics

  /****************************************************
   *                                                  *
   *               Current State                      *
   *                                                  *
   ***************************************************/
  // Pointer to store the current state (will be used during the grasp pose generation stage)
  mtc::Stage* current_state_ptr = nullptr;

  // Add a stage to capture the current state
  auto stage_state_current = std::make_unique<mtc::stages::CurrentState>("current state");
  current_state_ptr = stage_state_current.get();
  task.add(std::move(stage_state_current));

  /****************************************************
   *                                                  *
   *               Open Gripper                       *
   *                                                  *
   ***************************************************/
  // This stage is responsible for opening the robot's gripper in preparation for picking
  // up an object in the pick-and-place task.
  auto stage_open_gripper =
    std::make_unique<mtc::stages::MoveTo>("open gripper", interpolation_planner);
  stage_open_gripper->setGroup(gripper_group_name);
  stage_open_gripper->setGoal(gripper_open_pose);
  stage_open_gripper->properties().set("trajectory_execution_info",
                      mtc::TrajectoryExecutionInfo().set__controller_names({"gripper_controller"}));
  task.add(std::move(stage_open_gripper));

  /****************************************************
   *                                                  *
   *     Move to transit_clear (joint-space via)      *
   *                                                  *
   ***************************************************/
  // Split the home→pregrasp narrow passage into two easier legs. The via is a
  // named SRDF state whose FK was screened clear of the pick-table AABB
  // (tool0 ≈ (0.17, 0, 0.67)). Joint-space MoveTo — not Cartesian — so the
  // resting wrist singularity cannot break the motion.
  if (use_transit_clear_via) {
    // Joint-space interpolate to the named via (home→transit_clear is short
    // and clear). Fall back to OMPL if the straight joint path is blocked.
    auto via_fallbacks = std::make_unique<mtc::Fallbacks>("move to transit_clear");
    {
      auto stage = std::make_unique<mtc::stages::MoveTo>(
          "transit_clear (joint interp)", interpolation_planner);
      stage->setGroup(arm_group_name);
      stage->setGoal(arm_transit_clear_pose);
      stage->setTimeout(5.0);
      stage->properties().set(
          "trajectory_execution_info",
          mtc::TrajectoryExecutionInfo().set__controller_names(controller_names));
      via_fallbacks->add(std::move(stage));
    }
    {
      auto stage = std::make_unique<mtc::stages::MoveTo>(
          "transit_clear (ompl)", ompl_planner_transit);
      stage->setGroup(arm_group_name);
      stage->setGoal(arm_transit_clear_pose);
      stage->setTimeout(move_to_pick_timeout);
      stage->properties().set(
          "trajectory_execution_info",
          mtc::TrajectoryExecutionInfo().set__controller_names(controller_names));
      via_fallbacks->add(std::move(stage));
    }
    task.add(std::move(via_fallbacks));
    RCLCPP_INFO(this->get_logger(),
                "Inserted joint-space via Fallbacks→'%s' before move-to-pick",
                arm_transit_clear_pose.c_str());
  }

  /****************************************************
   *                                                  *
   *               Move to Pick                       *
   *                                                  *
   ***************************************************/
  // Create a stage to move the arm to a pre-grasp position
  auto stage_move_to_pick = std::make_unique<mtc::stages::Connect>(
      "move to pick",
      mtc::stages::Connect::GroupPlannerVector{
        // Arm only — gripper is already opened in the previous stage; including
        // it here made Connect fail to link the successful grasp IK solutions
        // back to the start state (0 Connect solutions while pick IK succeeded).
        {arm_group_name, ompl_planner_transit}
      });
  stage_move_to_pick->setTimeout(move_to_pick_timeout);
  stage_move_to_pick->properties().configureInitFrom(mtc::Stage::PARENT);
  stage_move_to_pick->properties().set(
      "trajectory_execution_info",
      mtc::TrajectoryExecutionInfo().set__controller_names(controller_names));
  // Transit uses APS/LBKPIECE + joint via + planning padding; path constraints
  // previously made OMPL find nothing within 40s and were reverted.
  task.add(std::move(stage_move_to_pick));
  (void)ompl_planner_arm;  // available for non-transit stages if needed later
  (void)arm_home_pose;

  // Create a pointer for the stage that will attach the object (to be used later)
  // By declaring it at the top level of the function, it can be accessed throughout
  // the entire task creation process.
  // This allows different parts of the code to use and modify this pointer.
  mtc::Stage* attach_object_stage =
      nullptr;  // Forward attach_object_stage to place pose generator

  /****************************************************
   *                                                  *
   *               Pick Object                        *
   *                                                  *
   ***************************************************/
  {
    // Create a serial container for the grasping action
    // This container will hold stages (in order) that will accomplish the picking action
    auto grasp = std::make_unique<mtc::SerialContainer>("pick object");
    task.properties().exposeTo(grasp->properties(), { "eef", "group", "ik_frame" });
    grasp->properties().configureInitFrom(mtc::Stage::PARENT,
                                        { "eef", "group", "ik_frame" });

    /****************************************************
---- *               Approach Object                    *
     ***************************************************/
    {
      // Create a stage for moving the gripper close to the object before trying to grab it.
      // We are doing a movement that is relative to our current position.
      // Cartesian planner will move the gripper in a straight line
      auto stage =
        std::make_unique<mtc::stages::MoveRelative>("approach object", cartesian_planner);

      // Set properties for visualization and planning
      stage->properties().set("marker_ns", "approach_object"); // Namespace for visualization markers
      stage->properties().set("link", gripper_frame); // The link to move (end effector)
      stage->properties().set("trajectory_execution_info",
                      mtc::TrajectoryExecutionInfo().set__controller_names(controller_names));
      stage->properties().configureInitFrom(mtc::Stage::PARENT, { "group" }); // Inherit the 'group' property
      stage->setMinMaxDistance(approach_object_min_dist, approach_object_max_dist);

      // Define the direction that we want the gripper to move (i.e. z direction) from the gripper frame
      geometry_msgs::msg::Vector3Stamped vec;
      vec.header.frame_id = gripper_frame; // Set the frame for the vector
      vec.vector.z = approach_object_direction_z; // Set the direction (in this case, along the z-axis of the gripper frame)
      stage->setDirection(vec);
      grasp->insert(std::move(stage));
    }

    /****************************************************
---- *               Generate Grasp Pose               *
     ***************************************************/
    {
      // Prefer absolute gripper poses in base_link over GenerateGraspPose +
      // setIKFrame(transform). Live probing showed move_group compute_ik
      // succeeds for those absolute top-down poses, while the
      // object-frame + grasp_frame_transform path consistently returned
      // "no IK found" for every Fallbacks candidate (same clearance math).
      auto grasp_ik_candidates = std::make_unique<mtc::Fallbacks>("grasp pose IK");
      grasp->properties().exposeTo(grasp_ik_candidates->properties(), { "eef", "group", "ik_frame" });
      grasp_ik_candidates->properties().configureInitFrom(mtc::Stage::PARENT, { "eef", "group", "ik_frame" });

      auto object_pose_param = this->get_parameter("object_pose").as_double_array();
      const double ox = object_pose_param[0];
      const double oy = object_pose_param[1];
      const double oz = object_pose_param[2];
      const double object_half_height = object_height / 2.0;
      // Palm of robotiq_arg2f_base_link extends ~0.09m past the frame origin.
      const double gripper_reach_offset = 0.090;

      struct GraspCandidate { double clearance; double pitch; double yaw; };
      std::vector<GraspCandidate> candidates;
      for (double pitch : { 3.14159, 2.7, 2.4 }) {
        for (double clearance : { 0.03, 0.05, 0.07 }) {
          // A few yaw samples — full 24-angle sweeps were too slow and did not
          // help when the underlying pose was unreachable.
          for (double yaw : { 0.0, 0.7854, 1.5708, 2.3562 }) {
            candidates.push_back({ clearance, pitch, yaw });
          }
        }
      }

      RCLCPP_INFO(this->get_logger(),
                  "Absolute grasp ladder: %zu candidates above object (%.3f, %.3f, %.3f) h/2=%.3f",
                  candidates.size(), ox, oy, oz, object_half_height);

      for (size_t i = 0; i < candidates.size(); ++i) {
        const double pitch = candidates[i].pitch;
        const double yaw = candidates[i].yaw;
        const double vertical =
            object_half_height + gripper_reach_offset + candidates[i].clearance;
        // Gripper origin for a top-down/tilted approach centered on the object:
        // same offsets_for_clearance math, applied in base_link.
        const double gx = ox - vertical * std::sin(pitch) * std::cos(yaw);
        const double gy = oy - vertical * std::sin(pitch) * std::sin(yaw);
        // For pure Ry(pitch) with yaw about world Z after: keep the simple
        // vertical placement that compute_ik accepted in probing (yaw only
        // changes orientation for pitch≈pi).
        const double gz = oz + vertical * (-std::cos(pitch));

        geometry_msgs::msg::PoseStamped grasp_pose;
        grasp_pose.header.frame_id = world_frame;  // base_link
        grasp_pose.pose.position.x = (std::abs(pitch - 3.14159) < 0.05) ? ox : gx;
        grasp_pose.pose.position.y = (std::abs(pitch - 3.14159) < 0.05) ? oy : gy;
        grasp_pose.pose.position.z = (std::abs(pitch - 3.14159) < 0.05) ? (oz + vertical) : gz;
        // orientation = Rz(yaw) * Ry(pitch)
        Eigen::Quaterniond q = Eigen::AngleAxisd(yaw, Eigen::Vector3d::UnitZ()) *
                               Eigen::AngleAxisd(pitch, Eigen::Vector3d::UnitY());
        grasp_pose.pose.orientation.x = q.x();
        grasp_pose.pose.orientation.y = q.y();
        grasp_pose.pose.orientation.z = q.z();
        grasp_pose.pose.orientation.w = q.w();

        RCLCPP_INFO(this->get_logger(),
                    "  grasp candidate %zu: pos=(%.3f,%.3f,%.3f) pitch=%.3f yaw=%.3f", i,
                    grasp_pose.pose.position.x, grasp_pose.pose.position.y,
                    grasp_pose.pose.position.z, pitch, yaw);

        auto stage = std::make_unique<mtc::stages::GeneratePose>("generate grasp pose " + std::to_string(i));
        stage->properties().configureInitFrom(mtc::Stage::PARENT);
        stage->properties().set("marker_ns", "grasp_pose");
        stage->setPose(grasp_pose);
        stage->setMonitoredStage(current_state_ptr);

        auto wrapper = std::make_unique<mtc::stages::ComputeIK>(
          "grasp pose IK " + std::to_string(i), std::move(stage));
        wrapper->setMaxIKSolutions(grasp_pose_max_ik_solutions);
        wrapper->setMinSolutionDistance(grasp_pose_min_solution_distance);
        wrapper->setTimeout(1.0);
        // Identity IK frame on the gripper — target_pose IS the gripper pose.
        wrapper->setIKFrame(gripper_frame);
        wrapper->properties().configureInitFrom(mtc::Stage::PARENT, { "eef", "group" });
        wrapper->properties().configureInitFrom(mtc::Stage::INTERFACE, { "target_pose" });
        grasp_ik_candidates->add(std::move(wrapper));
      }

      grasp->insert(std::move(grasp_ik_candidates));
    }

    /****************************************************
---- *            Allow Collision (gripper,  object)   *
     ***************************************************/
    {
      // Modify planning scene (w/o altering the robot's pose) to allow touching the object for picking
      auto stage =
        std::make_unique<mtc::stages::ModifyPlanningScene>("allow collision (gripper,object)");
      stage->allowCollisions(
        object_name,
        task.getRobotModel()
        ->getJointModelGroup(gripper_group_name)
        ->getLinkModelNamesWithCollisionGeometry(),
        true);
      grasp->insert(std::move(stage));
    }

    /****************************************************
---- *               Close Gripper                     *
     ***************************************************/
    {
      auto stage = std::make_unique<mtc::stages::MoveTo>("close gripper", interpolation_planner);
      stage->setGroup(gripper_group_name);
      stage->setGoal(gripper_close_pose);
      stage->properties().set("trajectory_execution_info",
                      mtc::TrajectoryExecutionInfo().set__controller_names({"gripper_controller"}));
      grasp->insert(std::move(stage));
    }

    /****************************************************
---- *       Allow collision (object,  support_surface)        *
     ***************************************************/
    {
      // Allows the planner to generate valid trajectories where the object remains in contact
      // with the support surface until it's lifted.
      auto stage = std::make_unique<mtc::stages::ModifyPlanningScene>("allow collision (object,support_surface)");
      stage->allowCollisions({ object_name }, {support_surface_id_}, true);
      grasp->insert(std::move(stage));
    }

    /****************************************************
---- *               Attach Object                     *
     ***************************************************/
    {
       auto stage = std::make_unique<mtc::stages::ModifyPlanningScene>("attach object");
       stage->attachObject(object_name, gripper_frame);  // attach object to gripper_frame
       attach_object_stage = stage.get();
       grasp->insert(std::move(stage));
    }

    /****************************************************
---- *       Lift object                               *
     ***************************************************/
    {
      auto stage = std::make_unique<mtc::stages::MoveRelative>("lift object", cartesian_planner);
      stage->properties().configureInitFrom(mtc::Stage::PARENT, { "group" });
      stage->setMinMaxDistance(lift_object_min_dist, lift_object_max_dist);
      stage->setIKFrame(gripper_frame);
      stage->properties().set("marker_ns", "lift_object");
      stage->properties().set("trajectory_execution_info",
                      mtc::TrajectoryExecutionInfo().set__controller_names(controller_names));

      // We're defining the direction to lift the object
      geometry_msgs::msg::Vector3Stamped vec;
      vec.header.frame_id = world_frame;
      vec.vector.z = lift_object_direction_z;  // This means "straight up"
      stage->setDirection(vec);
      grasp->insert(std::move(stage));
    }
    /****************************************************
---- *       Forbid collision (object, surface)*       *
     ***************************************************/
    {
      // Forbid collisions between the picked object and the support surface.
      // This is important after the object has been lifted to ensure it doesn't accidentally
      // collide with the surface during subsequent movements.
      auto stage = std::make_unique<mtc::stages::ModifyPlanningScene>("forbid collision (object,support_surface)");
      stage->allowCollisions({ object_name }, {support_surface_id_}, false);
      grasp->insert(std::move(stage));
    }

      // Add the serial container to the robot's to-do list
      // This serial container contains all the sequential steps we've created for grasping
      // and lifting the object
      task.add(std::move(grasp));
  }
  /******************************************************
   *                                                    *
   *          Move to Place                             *
   *                                                    *
   *****************************************************/
  {
    // Connect the grasped (lifted) state to the pre-place state.
    // No carry via here: moving to transit_clear with the cylinder attached
    // repeatedly hit torso↔object / support↔object under padding.
    auto stage_move_to_place = std::make_unique<mtc::stages::Connect>(
      "move to place",
      mtc::stages::Connect::GroupPlannerVector{
        {arm_group_name, ompl_planner_transit}
      });
    stage_move_to_place->setTimeout(move_to_place_timeout);
    stage_move_to_place->properties().configureInitFrom(mtc::Stage::PARENT);
    stage_move_to_place->properties().set(
        "trajectory_execution_info",
        mtc::TrajectoryExecutionInfo().set__controller_names(controller_names));
    task.add(std::move(stage_move_to_place));
  }

  /******************************************************
   *                                                    *
   *          Place Object                              *
   *                                                    *
   *****************************************************/
   // All placing sub-stages are collected within a serial container
  {
    auto place = std::make_unique<mtc::SerialContainer>("place object");
    task.properties().exposeTo(place->properties(), { "eef", "group", "ik_frame" });
    place->properties().configureInitFrom(mtc::Stage::PARENT, { "eef", "group", "ik_frame" });

    /******************************************************
---- *          Lower Object                              *
     *****************************************************/
    {
      auto stage = std::make_unique<mtc::stages::MoveRelative>("lower object", cartesian_planner);
      stage->properties().set("marker_ns", "lower_object");
      stage->properties().set("link", gripper_frame);
      stage->properties().set("trajectory_execution_info",
                      mtc::TrajectoryExecutionInfo().set__controller_names(controller_names));
      stage->properties().configureInitFrom(mtc::Stage::PARENT, { "group" });
      stage->setMinMaxDistance(lower_object_min_dist, lower_object_max_dist);

      // Set downward direction
      geometry_msgs::msg::Vector3Stamped vec;
      vec.header.frame_id = world_frame;
      vec.vector.z = lower_object_direction_z;
      stage->setDirection(vec);
      place->insert(std::move(stage));
    }

    /******************************************************
---- *          Generate Place Pose                       *
     *****************************************************/
    {
      // Mirror the pick-side absolute-pose approach. GeneratePlacePose +
      // attached-object ik_frame was returning "no IK found" for every
      // sample even after pick succeeded; place the gripper explicitly.
      auto place_ik = std::make_unique<mtc::Fallbacks>("place pose IK");
      place->properties().exposeTo(place_ik->properties(), { "eef", "group", "ik_frame" });
      place_ik->properties().configureInitFrom(mtc::Stage::PARENT, { "eef", "group", "ik_frame" });

      const double object_half_height = object_height / 2.0;
      const double gripper_reach_offset = 0.090;
      const double px = place_pose[0];
      const double py = place_pose[1];
      // Object center height at place: configured z plus a fraction of height.
      const double pz = place_pose[2] + place_pose_z_offset_factor * object_height;

      size_t idx = 0;
      for (double clearance : { 0.03, 0.05, 0.07, 0.10 }) {
        const double vertical = object_half_height + gripper_reach_offset + clearance;
        geometry_msgs::msg::PoseStamped grasp_pose;
        grasp_pose.header.frame_id = world_frame;
        grasp_pose.pose.position.x = px;
        grasp_pose.pose.position.y = py;
        grasp_pose.pose.position.z = pz + vertical;
        // top-down
        Eigen::Quaterniond q(Eigen::AngleAxisd(3.14159, Eigen::Vector3d::UnitY()));
        grasp_pose.pose.orientation.x = q.x();
        grasp_pose.pose.orientation.y = q.y();
        grasp_pose.pose.orientation.z = q.z();
        grasp_pose.pose.orientation.w = q.w();

        auto stage = std::make_unique<mtc::stages::GeneratePose>(
          "generate place pose " + std::to_string(idx));
        stage->properties().configureInitFrom(mtc::Stage::PARENT);
        stage->properties().set("marker_ns", "place_pose");
        stage->setPose(grasp_pose);
        stage->setMonitoredStage(attach_object_stage);

        auto wrapper = std::make_unique<mtc::stages::ComputeIK>(
          "place pose IK " + std::to_string(idx), std::move(stage));
        wrapper->setMaxIKSolutions(place_pose_max_ik_solutions);
        wrapper->setTimeout(1.0);
        wrapper->setIKFrame(gripper_frame);
        wrapper->properties().configureInitFrom(mtc::Stage::PARENT, { "eef", "group" });
        wrapper->properties().configureInitFrom(mtc::Stage::INTERFACE, { "target_pose" });
        place_ik->add(std::move(wrapper));
        ++idx;
      }
      place->insert(std::move(place_ik));
    }

    /******************************************************
---- *          Open Gripper                              *
     *****************************************************/
    {
      auto stage = std::make_unique<mtc::stages::MoveTo>("open gripper", interpolation_planner);
      stage->setGroup(gripper_group_name);
      stage->setGoal(gripper_open_pose);
      stage->properties().set("trajectory_execution_info",
        mtc::TrajectoryExecutionInfo().set__controller_names({"gripper_controller"}));
      place->insert(std::move(stage));
    }

    /******************************************************
---- *          Forbid collision (gripper, object)        *
     *****************************************************/
    {
      auto stage = std::make_unique<mtc::stages::ModifyPlanningScene>("forbid collision (gripper,object)");
      stage->allowCollisions(object_name, *task.getRobotModel()->getJointModelGroup(gripper_group_name),
        false);
      place->insert(std::move(stage));
    }

    /******************************************************
---- *          Detach Object                             *
     *****************************************************/
    {
      // Update the planning scene to reflect that the object is no longer attached to the gripper.
      auto stage = std::make_unique<mtc::stages::ModifyPlanningScene>("detach object");
      stage->detachObject(object_name, gripper_frame);
      place->insert(std::move(stage));
    }

    /******************************************************
---- *          Retreat Motion                            *
     *****************************************************/
    {
      auto stage = std::make_unique<mtc::stages::MoveRelative>("retreat after place", cartesian_planner);
      stage->properties().set("trajectory_execution_info",
        mtc::TrajectoryExecutionInfo().set__controller_names(controller_names));
      stage->properties().configureInitFrom(mtc::Stage::PARENT, { "group" });
      stage->setMinMaxDistance(retreat_min_distance, retreat_max_distance);
      stage->setIKFrame(gripper_frame);
      stage->properties().set("marker_ns", "retreat");
      geometry_msgs::msg::Vector3Stamped vec;
      vec.header.frame_id = gripper_frame;
      vec.vector.z = retreat_direction_z;
      stage->setDirection(vec);
      place->insert(std::move(stage));
    }

    // Add place container to task
    task.add(std::move(place));
  }

  return task;
}

/**
 * @brief Main function to run the MTC task node.
 * @param argc Number of command-line arguments.
 * @param argv Array of command-line arguments.
 * @return Exit status.
 */
int main(int argc, char** argv)
{
  // Initialize ROS 2
  rclcpp::init(argc, argv);

  int ret = 0;

  try {
    // Set up node options
    rclcpp::NodeOptions options;
    options.automatically_declare_parameters_from_overrides(true);

    // Create the MTC task node
    auto mtc_task_node = std::make_shared<MTCTaskNode>(options);

    // Set up a multi-threaded executor
    rclcpp::executors::MultiThreadedExecutor executor;
    executor.add_node(mtc_task_node);

    // Set up the planning scene and execute the task
    try {
      // run_pick_place service is available as soon as the node exists (see
      // constructor) — a BT-driven launch can start calling it immediately,
      // whether or not this auto-run also fires.
      if (mtc_task_node->get_parameter("auto_run_on_startup").as_bool()) {
        mtc_task_node->runOnePickPlaceAttempt();
        RCLCPP_INFO(mtc_task_node->get_logger(), "Task execution completed. Keeping node alive for visualization. Press Ctrl+C to exit.");
      } else {
        RCLCPP_INFO(mtc_task_node->get_logger(), "auto_run_on_startup=false — waiting for run_pick_place service calls.");
      }

      // Keep the node running until Ctrl+C is pressed
      executor.spin();
    } catch (const std::runtime_error& e) {
      RCLCPP_ERROR(mtc_task_node->get_logger(), "Runtime error occurred: %s", e.what());
      ret = 1;
    } catch (const std::exception& e) {
      RCLCPP_ERROR(mtc_task_node->get_logger(), "An error occurred: %s", e.what());
      ret = 1;
    }
  } catch (const std::exception& e) {
    RCLCPP_ERROR(rclcpp::get_logger("main"), "Error during node setup: %s", e.what());
    ret = 1;
  }

  // Cleanup
  rclcpp::shutdown();
  return ret;
}