/**
 * @file external_wrench_estimator.cpp
 * @brief Estimates external wrench at the arm's end-effector from joint effort readings.
 *
 * No wrist F/T sensor is modeled in this robot, so this estimates external force/torque
 * from joint torques via the Jacobian-transpose relationship: tau = J^T * F, solved as
 * F = pinv(J^T) * tau_ext, where tau_ext = measured joint effort minus the model's
 * predicted gravity torque g(q) (computed via Pinocchio RNEA from the full-body URDF,
 * so gripper mass is accounted for too) minus an optional residual bias.
 *
 * Unlike a plain effort-threshold tare, this stays valid as the arm moves — g(q) is
 * recomputed every cycle from the live joint configuration, not fixed at a single pose.
 * /ft/zero_wrench now only trims residual bias (simulated joint friction, controller
 * steady-state error) that the rigid-body gravity model doesn't capture; it is not
 * required for correctness at other poses the way the old tare-only approach was.
 *
 * J^T is only invertible away from kinematic singularities (e.g. the UR wrist
 * singularity at wrist_2 == 0, which is also this robot's idle pose) — a plain
 * pseudo-inverse there amplifies torque noise into wildly large forces. This uses a
 * damped least-squares inverse (Wampler/Nakamura-style) instead: singular values below
 * ~damping_lambda_ are rolled off rather than blown up.
 */

#include <cmath>
#include <memory>
#include <mutex>
#include <vector>

#include <Eigen/Dense>
#include <geometry_msgs/msg/wrench_stamped.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <pinocchio/algorithm/joint-configuration.hpp>
#include <pinocchio/algorithm/rnea.hpp>
#include <pinocchio/multibody/data.hpp>
#include <pinocchio/multibody/model.hpp>
#include <pinocchio/parsers/urdf.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <std_msgs/msg/bool.hpp>
#include <std_srvs/srv/trigger.hpp>

using moveit::planning_interface::MoveGroupInterface;

class ExternalWrenchEstimator : public rclcpp::Node
{
public:
  ExternalWrenchEstimator() : Node("external_wrench_estimator")
  {
    planning_group_ = declare_parameter("planning_group", std::string("arm"));
    publish_rate_hz_ = declare_parameter("publish_rate_hz", 30.0);
    force_threshold_n_ = declare_parameter("force_threshold_n", 15.0);
    damping_lambda_ = declare_parameter("damping_lambda", 0.05);

    wrench_pub_ = create_publisher<geometry_msgs::msg::WrenchStamped>("/ft/estimated_wrench", 10);
    contact_pub_ = create_publisher<std_msgs::msg::Bool>("/ft/arm_contact_detected", 10);

    zero_service_ = create_service<std_srvs::srv::Trigger>(
      "/ft/zero_wrench",
      std::bind(&ExternalWrenchEstimator::zeroWrenchCallback, this,
                std::placeholders::_1, std::placeholders::_2));
  }

  // Deferred: MoveGroupInterface needs shared_from_this(), which isn't valid inside
  // the constructor, so the arm interface and subscription are created here after
  // construction.
  void init()
  {
    move_group_ = std::make_shared<MoveGroupInterface>(shared_from_this(), planning_group_);
    robot_model_ = move_group_->getRobotModel();
    state_ = std::make_shared<moveit::core::RobotState>(robot_model_);
    state_->setToDefaultValues();
    bias_.setZero(move_group_->getJointNames().size());

    // Build the same robot as a Pinocchio model (whole body, so gripper mass loads the
    // wrist correctly) purely to evaluate g(q) each cycle — moveit::core::RobotState has
    // no dynamics of its own.
    pinocchio::urdf::buildModel(robot_model_->getURDF(), pin_model_, /*verbose=*/false, /*mimic=*/false);
    pin_data_ = pinocchio::Data(pin_model_);

    // Maintain our own RobotState from /joint_states directly rather than polling
    // MoveGroupInterface::getCurrentState(), whose strict freshness check (state stamp
    // must be newer than the request time) spuriously fails whenever the simulation's
    // real-time factor lags the wall clock even slightly.
    joint_state_sub_ = create_subscription<sensor_msgs::msg::JointState>(
      "/joint_states", rclcpp::SensorDataQoS(),
      std::bind(&ExternalWrenchEstimator::jointStateCallback, this, std::placeholders::_1));

    auto period = std::chrono::duration<double>(1.0 / publish_rate_hz_);
    timer_ = create_wall_timer(
      std::chrono::duration_cast<std::chrono::milliseconds>(period),
      std::bind(&ExternalWrenchEstimator::update, this));

    RCLCPP_INFO(get_logger(), "external_wrench_estimator ready for group '%s' (%zu joints)",
                planning_group_.c_str(), bias_.size());
  }

private:
  // Gravity torque g(q) for just the arm joints, computed from the full-body pose so
  // gripper mass is accounted for. Continuous joints (wrist_3_joint has no limit on this
  // robot) are represented in Pinocchio as (cos, sin) pairs (nq==2) rather than a raw
  // angle — handled below, everything else is a plain single-DOF revolute (nq==1).
  Eigen::VectorXd computeArmGravityTorque(
    const moveit::core::RobotState & state,
    const std::vector<const moveit::core::JointModel *> & arm_joints)
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

    Eigen::VectorXd g_arm(arm_joints.size());
    for (size_t i = 0; i < arm_joints.size(); ++i) {
      pinocchio::JointIndex jid = pin_model_.getJointId(arm_joints[i]->getName());
      g_arm(i) = g_full(pin_model_.joints[jid].idx_v());
    }
    return g_arm;
  }

  void jointStateCallback(const sensor_msgs::msg::JointState::SharedPtr msg)
  {
    std::lock_guard<std::mutex> lock(state_mutex_);
    for (size_t i = 0; i < msg->name.size(); ++i) {
      const moveit::core::JointModel * joint = robot_model_->getJointModel(msg->name[i]);
      if (!joint) {
        continue;
      }
      if (i < msg->position.size()) {
        state_->setVariablePosition(msg->name[i], msg->position[i]);
      }
      if (i < msg->velocity.size()) {
        state_->setVariableVelocity(msg->name[i], msg->velocity[i]);
      }
      if (i < msg->effort.size()) {
        state_->setJointEfforts(joint, &msg->effort[i]);
      }
    }
    state_->update();
    state_ready_ = true;
  }

  void update()
  {
    if (!state_ready_) {
      return;
    }

    moveit::core::RobotState state(robot_model_);
    {
      std::lock_guard<std::mutex> lock(state_mutex_);
      state = *state_;
    }

    const moveit::core::JointModelGroup * jmg = state.getJointModelGroup(planning_group_);
    if (!jmg) {
      return;
    }

    const std::vector<const moveit::core::JointModel *> & joints = jmg->getActiveJointModels();
    Eigen::VectorXd tau(joints.size());
    for (size_t i = 0; i < joints.size(); ++i) {
      const double * effort = state.getJointEffort(joints[i]);
      tau(i) = effort ? effort[0] : 0.0;
    }

    Eigen::VectorXd gravity_arm = computeArmGravityTorque(state, joints);

    Eigen::VectorXd bias;
    {
      std::lock_guard<std::mutex> lock(bias_mutex_);
      bias = bias_;
    }
    if (bias.size() != tau.size()) {
      bias.setZero(tau.size());
    }
    Eigen::VectorXd tau_ext = tau - gravity_arm - bias;

    Eigen::MatrixXd jacobian = state.getJacobian(jmg);
    Eigen::MatrixXd jacobian_t = jacobian.transpose();  // N x 6

    // Damped least-squares inverse: rolls off small singular values instead of
    // inverting them outright, so torque noise near a singularity (e.g. this robot's
    // idle pose, which sits at the UR wrist singularity) doesn't blow up into a huge
    // spurious force.
    Eigen::JacobiSVD<Eigen::MatrixXd> svd(jacobian_t, Eigen::ComputeThinU | Eigen::ComputeThinV);
    const Eigen::VectorXd & singular_values = svd.singularValues();
    Eigen::VectorXd damped_inv_singular_values(singular_values.size());
    for (int i = 0; i < singular_values.size(); ++i) {
      double s = singular_values(i);
      damped_inv_singular_values(i) = s / (s * s + damping_lambda_ * damping_lambda_);
    }
    Eigen::VectorXd wrench =
      svd.matrixV() * damped_inv_singular_values.asDiagonal() * svd.matrixU().transpose() * tau_ext;

    geometry_msgs::msg::WrenchStamped msg;
    msg.header.stamp = now();
    msg.header.frame_id = move_group_->getPlanningFrame();
    msg.wrench.force.x = wrench(0);
    msg.wrench.force.y = wrench(1);
    msg.wrench.force.z = wrench(2);
    msg.wrench.torque.x = wrench(3);
    msg.wrench.torque.y = wrench(4);
    msg.wrench.torque.z = wrench(5);
    wrench_pub_->publish(msg);

    std_msgs::msg::Bool contact;
    contact.data = wrench.head<3>().norm() > force_threshold_n_;
    contact_pub_->publish(contact);

    last_residual_ = tau - gravity_arm;
  }

  void zeroWrenchCallback(
    const std::shared_ptr<std_srvs::srv::Trigger::Request>,
    std::shared_ptr<std_srvs::srv::Trigger::Response> response)
  {
    if (last_residual_.size() == 0) {
      response->success = false;
      response->message = "No joint effort reading yet";
      return;
    }
    {
      std::lock_guard<std::mutex> lock(bias_mutex_);
      bias_ = last_residual_;
    }
    response->success = true;
    response->message = "Residual bias trimmed at current pose";
    RCLCPP_INFO(get_logger(), "Residual bias trimmed (gravity already compensated by model)");
  }

  std::string planning_group_;
  double publish_rate_hz_;
  double force_threshold_n_;
  double damping_lambda_;

  std::shared_ptr<MoveGroupInterface> move_group_;
  moveit::core::RobotModelConstPtr robot_model_;
  pinocchio::Model pin_model_;
  pinocchio::Data pin_data_;
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;
  rclcpp::Publisher<geometry_msgs::msg::WrenchStamped>::SharedPtr wrench_pub_;
  rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr contact_pub_;
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr zero_service_;

  std::mutex state_mutex_;
  moveit::core::RobotStatePtr state_;
  bool state_ready_ = false;

  std::mutex bias_mutex_;
  Eigen::VectorXd bias_;
  Eigen::VectorXd last_residual_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<ExternalWrenchEstimator>();

  // Spin in a background thread first: MoveGroupInterface's constructor (called from
  // init() below) makes blocking calls that require the node's executor to already be
  // spinning concurrently, same pattern as ur_moveit_demos/src/hello_moveit.cpp.
  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  auto spinner = std::thread([&executor]() { executor.spin(); });

  node->init();

  spinner.join();
  rclcpp::shutdown();
  return 0;
}
