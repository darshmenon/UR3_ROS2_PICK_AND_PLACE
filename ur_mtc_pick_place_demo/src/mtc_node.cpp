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

// Other utilities
#include <type_traits>
#include <numeric>
#include <cmath>
#include <map>
#include <sstream>
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

  void doTask();
  void setupPlanningScene();

private:
  mtc::Task task_;
  mtc::Task createTask();

  void updateObjectParameters(const moveit_msgs::msg::CollisionObject& collision_object);

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

  // Controller parameters
  declare_parameter("controller_names", std::vector<std::string>{"arm_controller", "gripper_controller"}, "Names of the controllers to use");

  // Robot configuration parameters
  declare_parameter("arm_group_name", "arm", "Name of the arm group in the SRDF");
  declare_parameter("gripper_group_name", "gripper", "Name of the gripper group in the SRDF");
  declare_parameter("gripper_frame", "robotiq_arg2f_base_link", "Name of the gripper frame");
  declare_parameter("gripper_open_pose", "open", "Name of the gripper open pose");
  declare_parameter("gripper_close_pose", "half_closed", "Name of the gripper closed pose");
  declare_parameter("arm_home_pose", "home", "Name of the arm home pose");

  // Scene frame parameters
  declare_parameter("world_frame", "base_link", "Name of the world frame");

  // Object parameters
  declare_parameter("object_name", "object", "Name of the object to be manipulated");
  declare_parameter("object_type", "cylinder", "Type of the object to be manipulated");
  declare_parameter("object_reference_frame", "base_link", "Reference frame for the object");
  declare_parameter("object_dimensions", std::vector<double>{0.35, 0.0125}, "Dimensions of the object [height, radius]");
  declare_parameter("object_pose", std::vector<double>{0.22, 0.12, 0.0, 0.0, 0.0, 0.0}, "Initial pose of the object [x, y, z, roll, pitch, yaw]");

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

/**
 * @brief Set up the planning scene with collision objects.
 */
void MTCTaskNode::setupPlanningScene()
{

  // Create a planning scene interface to interact with the world
  moveit::planning_interface::PlanningSceneInterface psi;

  // Get target object parameters
  auto object_name = this->get_parameter("object_name").as_string();
  auto object_type = this->get_parameter("object_type").as_string();
  auto object_dimensions = this->get_parameter("object_dimensions").as_double_array();
  auto object_pose_param = this->get_parameter("object_pose").as_double_array();
  auto object_reference_frame = this->get_parameter("object_reference_frame").as_string();

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

  RCLCPP_INFO(this->get_logger(), "Sending GetPlanningScene service request...");

  // Call the service
  auto response = planning_scene_client->call_service(object_type, object_dimensions);

  RCLCPP_INFO(this->get_logger(), "Service call to the GetPlanningScene service completed.");

  // Store the results
  scene_world_ = response.scene_world;
  full_cloud_ = response.full_cloud;
  rgb_image_ = response.rgb_image;
  target_object_id_ = response.target_object_id;
  support_surface_id_ = response.support_surface_id;
  service_success_ = response.success;

  // Add all collision objects to the planning scene (non-blocking topic publish to avoid DDS response timeout)
  RCLCPP_INFO(this->get_logger(), "Adding %zu collision objects from service response to the planning scene...",
    scene_world_.collision_objects.size());
  if (!scene_world_.collision_objects.empty()) {
    psi.addCollisionObjects(scene_world_.collision_objects);
    rclcpp::sleep_for(std::chrono::milliseconds(3000));
    RCLCPP_INFO(this->get_logger(), "Successfully added %zu collision objects to the planning scene",
      scene_world_.collision_objects.size());
  }

  // Find the target object in the collision objects and update parameters
  RCLCPP_INFO(this->get_logger(), "Received target_object_id from service: '%s'", target_object_id_.c_str());
  for (const auto& collision_object : scene_world_.collision_objects) {
    if (collision_object.id == target_object_id_) {
      updateObjectParameters(collision_object);
      break;
    }
  }

  // If the service returned no objects, add the hardcoded target from params so MTC has something to pick
  if (scene_world_.collision_objects.empty()) {
    RCLCPP_WARN(this->get_logger(),
      "Planning scene service returned no objects. Adding fallback '%s' from params.", object_name.c_str());

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

    psi.addCollisionObjects({fallback});
    rclcpp::sleep_for(std::chrono::milliseconds(3000));
    RCLCPP_INFO(this->get_logger(), "Fallback object '%s' added at (%.3f, %.3f, %.3f)",
      object_name.c_str(), object_pose_param[0], object_pose_param[1], object_pose_param[2]);
    target_object_id_ = object_name;
  }

  RCLCPP_INFO(this->get_logger(), "Planning scene setup completed");
}

/**
 * @brief Plan and/or execute the pick and place task.
 */
void MTCTaskNode::doTask()
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
    return;
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
    return;
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

  if (execute)
  {
    // Execute the planned task
    RCLCPP_INFO(this->get_logger(), "Executing the planned task");
    auto result = task_.execute(*task_.solutions().front());
    if (result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS)
    {
      RCLCPP_ERROR(this->get_logger(), "Task execution failed with error code: %d", result.val);
      return;
    }
    RCLCPP_INFO(this->get_logger(), "Task executed successfully");
  }
  else
  {
    RCLCPP_INFO(this->get_logger(), "Execution skipped as per configuration");
  }

  return;
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
  // Pipeline planner for complex movements
  // OMPL planner
  auto ompl_planner_arm = std::make_shared<mtc::solvers::PipelinePlanner>(
    this->shared_from_this(),
    "ompl");
  RCLCPP_INFO(this->get_logger(), "OMPL planner created for the arm group");

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
   *               Move to Pick                       *
   *                                                  *
   ***************************************************/
  // Create a stage to move the arm to a pre-grasp position
  auto stage_move_to_pick = std::make_unique<mtc::stages::Connect>(
      "move to pick",
      mtc::stages::Connect::GroupPlannerVector{
        {arm_group_name, ompl_planner_arm},
        {gripper_group_name, interpolation_planner}
      });
  stage_move_to_pick->setTimeout(move_to_pick_timeout);
  stage_move_to_pick->properties().configureInitFrom(mtc::Stage::PARENT);
  task.add(std::move(stage_move_to_pick));

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
      // A single fixed grasp_frame_transform is fragile for objects close to
      // the arm's base — the collision-free/reachable window is often only
      // 1-8mm wide or nonexistent (see README). Try a ladder of (standoff,
      // pitch) candidates via Fallbacks: MTC uses the first one that's
      // actually collision-free and reachable for this run's real object.
      auto grasp_ik_candidates = std::make_unique<mtc::Fallbacks>("grasp pose IK");
      grasp->properties().exposeTo(grasp_ik_candidates->properties(), { "eef", "group", "ik_frame" });
      grasp_ik_candidates->properties().configureInitFrom(mtc::Stage::PARENT, { "eef", "group", "ik_frame" });

      // Scale standoff off the object's own detected height rather than a
      // hardcoded number, so it adapts to whatever perception reports.
      double object_half_height = object_height / 2.0;

      struct GraspCandidate { double standoff; double pitch; };
      std::vector<GraspCandidate> candidates = {
        { grasp_frame_transform[2], grasp_frame_transform[4] },  // configured value, tried first
      };
      // The standoff translation is applied along gripper_frame's own
      // untilted Z axis, before the pitch rotation — so the real vertical
      // clearance is `standoff * -cos(pitch)`, not `standoff` (1.0 at
      // pitch=pi, dropping to ~0.42 at pitch=2.0). Divide by that factor so
      // "clearance"/"offset" below mean actual vertical clearance.
      auto standoff_for_clearance = [](double vertical_clearance, double pitch) {
        return vertical_clearance / -std::cos(pitch);
      };

      // pitch=pi is straight top-down; the rest tilt off that wrist-singular
      // orientation (see README), trading "no IK" for "in collision" at a
      // nearby standoff — scan a few clearances per pitch for a shot at
      // whatever narrow window exists.
      if (object_half_height > 0.0) {
        for (double pitch : { 3.14159, 2.7, 2.4, 2.0 }) {
          for (double clearance : { 0.03, 0.04, 0.05, 0.06, 0.07 }) {
            candidates.push_back({ standoff_for_clearance(object_half_height + clearance, pitch), pitch });
          }
        }
      } else {
        // Dimensions unavailable (shouldn't normally happen) — offsets from
        // the configured standoff instead of adapting to object height.
        for (double pitch : { 3.14159, 2.7, 2.4, 2.0 }) {
          for (double offset : { 0.02, 0.04, 0.06, 0.08, 0.10 }) {
            candidates.push_back({ standoff_for_clearance(grasp_frame_transform[2] + offset, pitch), pitch });
          }
        }
      }

      for (size_t i = 0; i < candidates.size(); ++i) {
        RCLCPP_INFO(this->get_logger(), "  grasp candidate %zu: standoff=%.4f pitch=%.4f", i,
                    candidates[i].standoff, candidates[i].pitch);
      }

      for (size_t i = 0; i < candidates.size(); ++i) {
        std::vector<double> candidate_transform = grasp_frame_transform;
        candidate_transform[2] = candidates[i].standoff;
        candidate_transform[4] = candidates[i].pitch;

        // Generate the grasp pose
        // This is the stage for computing how the robot should grab the object
        // This stage is a generator stage because it doesn't need information from
        // stages before or after it.
        // When generating solutions, MTC will try to grab the object from many different orientations.
        // Sample grasp pose candidates in angle increments around the z-axis of the object
        auto stage = std::make_unique<mtc::stages::GenerateGraspPose>(
          "generate grasp pose " + std::to_string(i));
        stage->properties().configureInitFrom(mtc::Stage::PARENT);
        stage->properties().set("marker_ns", "grasp_pose");
        stage->setPreGraspPose(gripper_open_pose);
        stage->setObject(object_name);
        stage->setAngleDelta(grasp_pose_angle_delta); // Angular resolution for sampling grasp poses around the object
        stage->setMonitoredStage(current_state_ptr);  // Ensure grasp poses are valid given the initial configuration of the robot

        // Compute IK for sampled grasp poses
        auto wrapper = std::make_unique<mtc::stages::ComputeIK>(
          "grasp pose IK " + std::to_string(i), std::move(stage));
        wrapper->setMaxIKSolutions(grasp_pose_max_ik_solutions);
        wrapper->setMinSolutionDistance(grasp_pose_min_solution_distance);
        wrapper->setIKFrame(vectorToEigen(candidate_transform), gripper_frame); // Transform from gripper frame to tool center point (TCP)
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
    // Connect the grasped state to the pre-place state, i.e. realize the object transport
    // In other words, this stage plans the motion that transports the object from where it was picked up
    // to where it will be placed.
    auto stage_move_to_place = std::make_unique<mtc::stages::Connect>(
      "move to place",
      mtc::stages::Connect::GroupPlannerVector{
        {arm_group_name, ompl_planner_arm},
        {gripper_group_name, interpolation_planner}
      });
    stage_move_to_place->setTimeout(move_to_place_timeout);
    stage_move_to_place->properties().configureInitFrom(mtc::Stage::PARENT);
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
      // Generate Place Pose
      auto stage = std::make_unique<mtc::stages::GeneratePlacePose>("generate place pose");
      stage->properties().configureInitFrom(mtc::Stage::PARENT, { "ik_frame" });
      stage->properties().set("marker_ns", "place_pose");
      stage->setObject(object_name);

      // Set target pose
      geometry_msgs::msg::PoseStamped target_pose_msg;
      target_pose_msg.header.frame_id = world_frame;
      target_pose_msg.pose = vectorToPose(place_pose);
      // object_dimensions[0] is only the object's height for a cylinder — for
      // a box it's the X dimension, which would halve the intended clearance
      // for a tall, narrow box (see object_height above). Use the
      // type-aware height so placement clears the surface by the same
      // fraction of the object's actual height regardless of its shape.
      target_pose_msg.pose.position.z += place_pose_z_offset_factor * object_height;
      stage->setPose(target_pose_msg);
      stage->setMonitoredStage(attach_object_stage);  // hook into successful pick solutions

      // Compute IK
      // Don't hardcode setIKFrame here: with multiple grasp candidates (see
      // "Generate Grasp Pose" above), the real gripper-to-object transform
      // depends on whichever candidate's IK actually succeeded during pick.
      // GeneratePlacePose already publishes the correct one as an "ik_frame"
      // interface property (identity pose in the attached object's own
      // frame, resolved through the object's live attachment transform) —
      // read that instead of assuming the pick-side config.
      auto wrapper = std::make_unique<mtc::stages::ComputeIK>("place pose IK", std::move(stage));
      wrapper->setMaxIKSolutions(place_pose_max_ik_solutions);
      wrapper->properties().configureInitFrom(mtc::Stage::PARENT, { "eef", "group" });
      wrapper->properties().configureInitFrom(mtc::Stage::INTERFACE, { "target_pose", "ik_frame" });
      place->insert(std::move(wrapper));
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
      RCLCPP_INFO(mtc_task_node->get_logger(), "Setting up planning scene");
      mtc_task_node->setupPlanningScene();
      RCLCPP_INFO(mtc_task_node->get_logger(), "Executing task");
      mtc_task_node->doTask();
      RCLCPP_INFO(mtc_task_node->get_logger(), "Task execution completed. Keeping node alive for visualization. Press Ctrl+C to exit.");

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