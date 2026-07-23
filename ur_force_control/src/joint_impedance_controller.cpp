/**
 * @file joint_impedance_controller.cpp
 * @brief Joint-space impedance control for the arm: tau = K*(q_des - q) - D*qdot + g(q).
 *
 * Requires the arm to be in effort command mode first:
 *   ros2 control switch_controllers --deactivate arm_controller \
 *     --activate forward_command_controller_effort
 *
 * Publishes torque commands to /forward_command_controller_effort/commands at
 * publish_rate_hz. g(q) is computed every cycle via Pinocchio RNEA from the full-body
 * URDF (same approach as external_wrench_estimator), so the arm doesn't sag under its
 * own weight even with zero stiffness. The equilibrium pose defaults to wherever the arm
 * is when this node starts (hold-current-pose) and can be moved via
 * /joint_impedance_controller/target_positions or re-captured via
 * /joint_impedance_controller/hold_current_pose.
 *
 * Commanded torque is clamped to each joint's effort limit (matching
 * moveit_config/config/ur.ros2_control.xacro) before publishing, as a safety margin
 * against a bad gravity estimate or a stiffness/damping combination that would otherwise
 * spike the command.
 */

#include <algorithm>
#include <cmath>
#include <chrono>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

#include <Eigen/Dense>
#include <moveit/move_group_interface/move_group_interface.h>
#include <pinocchio/algorithm/joint-configuration.hpp>
#include <pinocchio/algorithm/rnea.hpp>
#include <pinocchio/multibody/data.hpp>
#include <pinocchio/multibody/model.hpp>
#include <pinocchio/parsers/urdf.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <std_srvs/srv/trigger.hpp>

using moveit::planning_interface::MoveGroupInterface;

class JointImpedanceController : public rclcpp::Node
{
public:
  JointImpedanceController() : Node("joint_impedance_controller")
  {
    joint_names_ = declare_parameter(
      "joint_names", std::vector<std::string>{
        "shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
        "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"});
    stiffness_ = declare_parameter(
      "stiffness", std::vector<double>{80.0, 80.0, 60.0, 15.0, 15.0, 15.0});
    damping_ = declare_parameter(
      "damping", std::vector<double>{8.0, 8.0, 6.0, 1.5, 1.5, 1.5});
    effort_limits_ = declare_parameter(
      "effort_limits", std::vector<double>{56.0, 56.0, 28.0, 12.0, 12.0, 12.0});
    publish_rate_hz_ = declare_parameter("publish_rate_hz", 200.0);
    debug_logging_ = declare_parameter("debug_logging", false);
    debug_log_period_ms_ = declare_parameter("debug_log_period_ms", 200);

    validateParameters();

    target_sub_ = create_subscription<std_msgs::msg::Float64MultiArray>(
      "/joint_impedance_controller/target_positions", 10,
      std::bind(&JointImpedanceController::targetCallback, this, std::placeholders::_1));

    hold_pose_service_ = create_service<std_srvs::srv::Trigger>(
      "/joint_impedance_controller/hold_current_pose",
      std::bind(&JointImpedanceController::holdCurrentPoseCallback, this,
                std::placeholders::_1, std::placeholders::_2));
  }

  // Deferred for the same reason as external_wrench_estimator: MoveGroupInterface needs
  // shared_from_this(), invalid inside the constructor.
  void init()
  {
    move_group_ = std::make_shared<MoveGroupInterface>(shared_from_this(), "arm");
    robot_model_ = move_group_->getRobotModel();
    state_ = std::make_shared<moveit::core::RobotState>(robot_model_);
    state_->setToDefaultValues();

    pinocchio::urdf::buildModel(robot_model_->getURDF(), pin_model_, /*verbose=*/false, /*mimic=*/false);
    pin_data_ = pinocchio::Data(pin_model_);
    validateModelJoints();

    command_pub_ = create_publisher<std_msgs::msg::Float64MultiArray>(
      "/forward_command_controller_effort/commands", 10);

    joint_state_sub_ = create_subscription<sensor_msgs::msg::JointState>(
      "/joint_states", rclcpp::SensorDataQoS(),
      std::bind(&JointImpedanceController::jointStateCallback, this, std::placeholders::_1));

    auto period = std::chrono::duration<double>(1.0 / publish_rate_hz_);
    timer_ = create_wall_timer(
      std::chrono::duration_cast<std::chrono::nanoseconds>(period),
      std::bind(&JointImpedanceController::update, this));

    RCLCPP_INFO(
      get_logger(),
      "joint_impedance_controller ready (%zu joints). Arm must be switched to "
      "forward_command_controller_effort before this has any effect.",
      joint_names_.size());
  }

private:
  void validateParameters() const
  {
    if (joint_names_.empty()) {
      throw std::runtime_error("joint_names must not be empty");
    }
    if (stiffness_.size() != joint_names_.size()) {
      throw std::runtime_error("stiffness size must match joint_names size");
    }
    if (damping_.size() != joint_names_.size()) {
      throw std::runtime_error("damping size must match joint_names size");
    }
    if (effort_limits_.size() != joint_names_.size()) {
      throw std::runtime_error("effort_limits size must match joint_names size");
    }
    if (publish_rate_hz_ <= 0.0 || !std::isfinite(publish_rate_hz_)) {
      throw std::runtime_error("publish_rate_hz must be finite and > 0");
    }
    if (debug_log_period_ms_ <= 0) {
      throw std::runtime_error("debug_log_period_ms must be > 0");
    }
    for (size_t i = 0; i < joint_names_.size(); ++i) {
      if (joint_names_[i].empty()) {
        throw std::runtime_error("joint_names entries must not be empty");
      }
      if (!std::isfinite(stiffness_[i]) || stiffness_[i] < 0.0) {
        throw std::runtime_error("stiffness values must be finite and >= 0");
      }
      if (!std::isfinite(damping_[i]) || damping_[i] < 0.0) {
        throw std::runtime_error("damping values must be finite and >= 0");
      }
      if (!std::isfinite(effort_limits_[i]) || effort_limits_[i] <= 0.0) {
        throw std::runtime_error("effort_limits values must be finite and > 0");
      }
    }
  }

  void validateModelJoints() const
  {
    for (const auto & joint_name : joint_names_) {
      if (!robot_model_->hasJointModel(joint_name)) {
        throw std::runtime_error("Joint '" + joint_name + "' not found in MoveIt robot model");
      }
      pinocchio::JointIndex jid = pin_model_.getJointId(joint_name);
      if (jid >= static_cast<pinocchio::JointIndex>(pin_model_.njoints)) {
        throw std::runtime_error("Joint '" + joint_name + "' not found in Pinocchio model");
      }
    }
  }

  Eigen::VectorXd computeGravityTorque(const moveit::core::RobotState & state)
  {
    Eigen::VectorXd q_full = pinocchio::neutral(pin_model_);
    for (pinocchio::JointIndex jid = 1; jid < static_cast<pinocchio::JointIndex>(pin_model_.njoints);
         ++jid) {
      const std::string & name = pin_model_.names[jid];
      if (!robot_model_->hasJointModel(name)) {
        continue;
      }
      double angle = state.getVariablePosition(name);
      int idx_q = pin_model_.joints[jid].idx_q();
      int nq = pin_model_.joints[jid].nq();
      if (nq == 1) {
        q_full(idx_q) = angle;
      } else if (nq == 2) {
        q_full(idx_q) = std::cos(angle);
        q_full(idx_q + 1) = std::sin(angle);
      }
    }

    const Eigen::VectorXd & g_full =
      pinocchio::computeGeneralizedGravity(pin_model_, pin_data_, q_full);

    Eigen::VectorXd g_arm(joint_names_.size());
    for (size_t i = 0; i < joint_names_.size(); ++i) {
      pinocchio::JointIndex jid = pin_model_.getJointId(joint_names_[i]);
      if (jid >= static_cast<pinocchio::JointIndex>(pin_model_.njoints)) {
        throw std::runtime_error("Joint '" + joint_names_[i] + "' not found in Pinocchio model");
      }
      g_arm(i) = g_full(pin_model_.joints[jid].idx_v());
    }
    return g_arm;
  }

  void jointStateCallback(const sensor_msgs::msg::JointState::SharedPtr msg)
  {
    std::lock_guard<std::mutex> lock(state_mutex_);
    for (size_t i = 0; i < msg->name.size(); ++i) {
      if (!robot_model_->hasJointModel(msg->name[i])) {
        continue;
      }
      if (i < msg->position.size()) {
        state_->setVariablePosition(msg->name[i], msg->position[i]);
      }
      if (i < msg->velocity.size()) {
        state_->setVariableVelocity(msg->name[i], msg->velocity[i]);
      }
    }
    state_->update();

    if (!target_set_) {
      // First joint_states message: hold wherever the arm currently is.
      target_.resize(joint_names_.size());
      for (size_t i = 0; i < joint_names_.size(); ++i) {
        target_(i) = state_->getVariablePosition(joint_names_[i]);
      }
      target_set_ = true;
    }
    state_ready_ = true;
  }

  void targetCallback(const std_msgs::msg::Float64MultiArray::SharedPtr msg)
  {
    if (msg->data.size() != joint_names_.size()) {
      RCLCPP_WARN(
        get_logger(), "target_positions expected %zu values, got %zu — ignoring",
        joint_names_.size(), msg->data.size());
      return;
    }
    if (!std::all_of(msg->data.begin(), msg->data.end(), [](double value) {
        return std::isfinite(value);
      })) {
      RCLCPP_WARN(get_logger(), "target_positions contains non-finite values — ignoring");
      return;
    }
    std::lock_guard<std::mutex> lock(target_mutex_);
    target_ = Eigen::Map<const Eigen::VectorXd>(msg->data.data(), msg->data.size());
    target_set_ = true;
  }

  void holdCurrentPoseCallback(
    const std::shared_ptr<std_srvs::srv::Trigger::Request>,
    std::shared_ptr<std_srvs::srv::Trigger::Response> response)
  {
    if (!state_ready_) {
      response->success = false;
      response->message = "No joint state received yet";
      return;
    }
    Eigen::VectorXd new_target(joint_names_.size());
    {
      std::lock_guard<std::mutex> lock(state_mutex_);
      for (size_t i = 0; i < joint_names_.size(); ++i) {
        new_target(i) = state_->getVariablePosition(joint_names_[i]);
      }
    }
    {
      std::lock_guard<std::mutex> lock(target_mutex_);
      target_ = new_target;
      target_set_ = true;
    }
    response->success = true;
    response->message = "Equilibrium pose re-captured at current joint positions";
    RCLCPP_INFO(get_logger(), "Equilibrium pose re-captured at current joint positions");
  }

  void update()
  {
    if (!state_ready_ || !target_set_) {
      return;
    }

    moveit::core::RobotState state(robot_model_);
    Eigen::VectorXd q(joint_names_.size());
    Eigen::VectorXd qdot(joint_names_.size());
    {
      std::lock_guard<std::mutex> lock(state_mutex_);
      state = *state_;
      for (size_t i = 0; i < joint_names_.size(); ++i) {
        q(i) = state.getVariablePosition(joint_names_[i]);
        qdot(i) = state.getVariableVelocity(joint_names_[i]);
      }
    }

    Eigen::VectorXd target;
    {
      std::lock_guard<std::mutex> lock(target_mutex_);
      target = target_;
    }

    Eigen::VectorXd gravity = computeGravityTorque(state);
    Eigen::VectorXd spring_term(joint_names_.size());
    Eigen::VectorXd damping_term(joint_names_.size());
    Eigen::VectorXd raw_tau(joint_names_.size());
    Eigen::VectorXd clamped_tau(joint_names_.size());
    bool saturated = false;

    std_msgs::msg::Float64MultiArray msg;
    msg.data.resize(joint_names_.size());
    for (size_t i = 0; i < joint_names_.size(); ++i) {
      spring_term(i) = stiffness_[i] * (target(i) - q(i));
      damping_term(i) = -damping_[i] * qdot(i);
      raw_tau(i) = spring_term(i) + damping_term(i) + gravity(i);
      const double limit = effort_limits_[i];
      clamped_tau(i) = std::clamp(raw_tau(i), -limit, limit);
      saturated = saturated || (clamped_tau(i) != raw_tau(i));
      msg.data[i] = clamped_tau(i);
    }
    command_pub_->publish(msg);

    if (debug_logging_) {
      RCLCPP_INFO_THROTTLE(
        get_logger(), *get_clock(), debug_log_period_ms_,
        "impedance_debug q=[%.4f %.4f %.4f %.4f %.4f %.4f] "
        "qdot=[%.4f %.4f %.4f %.4f %.4f %.4f] "
        "target=[%.4f %.4f %.4f %.4f %.4f %.4f] "
        "gravity=[%.4f %.4f %.4f %.4f %.4f %.4f] "
        "spring=[%.4f %.4f %.4f %.4f %.4f %.4f] "
        "damping=[%.4f %.4f %.4f %.4f %.4f %.4f] "
        "raw_tau=[%.4f %.4f %.4f %.4f %.4f %.4f] "
        "cmd_tau=[%.4f %.4f %.4f %.4f %.4f %.4f] saturated=%s",
        q(0), q(1), q(2), q(3), q(4), q(5),
        qdot(0), qdot(1), qdot(2), qdot(3), qdot(4), qdot(5),
        target(0), target(1), target(2), target(3), target(4), target(5),
        gravity(0), gravity(1), gravity(2), gravity(3), gravity(4), gravity(5),
        spring_term(0), spring_term(1), spring_term(2), spring_term(3), spring_term(4), spring_term(5),
        damping_term(0), damping_term(1), damping_term(2), damping_term(3), damping_term(4), damping_term(5),
        raw_tau(0), raw_tau(1), raw_tau(2), raw_tau(3), raw_tau(4), raw_tau(5),
        clamped_tau(0), clamped_tau(1), clamped_tau(2), clamped_tau(3), clamped_tau(4), clamped_tau(5),
        saturated ? "true" : "false");
    }
  }

  std::vector<std::string> joint_names_;
  std::vector<double> stiffness_;
  std::vector<double> damping_;
  std::vector<double> effort_limits_;
  double publish_rate_hz_;
  bool debug_logging_;
  int debug_log_period_ms_;

  std::shared_ptr<MoveGroupInterface> move_group_;
  moveit::core::RobotModelConstPtr robot_model_;
  pinocchio::Model pin_model_;
  pinocchio::Data pin_data_;

  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
  rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr target_sub_;
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr command_pub_;
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr hold_pose_service_;

  std::mutex state_mutex_;
  moveit::core::RobotStatePtr state_;
  bool state_ready_ = false;

  std::mutex target_mutex_;
  Eigen::VectorXd target_;
  bool target_set_ = false;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<JointImpedanceController>();

  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  auto spinner = std::thread([&executor]() { executor.spin(); });

  node->init();

  spinner.join();
  rclcpp::shutdown();
  return 0;
}
