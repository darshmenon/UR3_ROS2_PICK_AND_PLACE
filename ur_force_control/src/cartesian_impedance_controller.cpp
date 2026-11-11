/**
 * @brief Cartesian impedance control of a tool frame: tau = J^T [K (x_des - x) - D v] + g(q).
 *
 * Reads /joint_states and the URDF from the /robot_description topic, builds a Pinocchio model, and publishes joint
 * efforts to /forward_command_controller_effort/commands (the arm must be switched to that controller first).
 * Poses are expressed in the URDF root frame (base_link).
 *
 * Topics:
 *   sub  ~/target_pose   geometry_msgs/PoseStamped   desired tip pose (position + orientation)
 *   sub  ~/stiffness     std_msgs/Float64MultiArray  [kx ky kz krx kry krz], changes impedance on the fly
 *   pub  ~/tip_pose      geometry_msgs/PoseStamped   measured tip pose
 *   srv  ~/hold_current_pose  std_srvs/Trigger       re-capture the target at the current tip pose
 * Damping is critical per axis: d = 2 sqrt(k m_eff) with the m_eff parameters (kg for translation, kg m^2 rotation).
 */
#include <algorithm>
#include <chrono>
#include <cmath>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

#include <Eigen/Dense>

#include <pinocchio/algorithm/frames.hpp>
#include <pinocchio/algorithm/jacobian.hpp>
#include <pinocchio/algorithm/joint-configuration.hpp>
#include <pinocchio/algorithm/rnea.hpp>
#include <pinocchio/multibody/data.hpp>
#include <pinocchio/multibody/model.hpp>
#include <pinocchio/parsers/urdf.hpp>

#include <geometry_msgs/msg/pose_stamped.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joint_state.hpp>
#include <std_msgs/msg/float64_multi_array.hpp>
#include <std_msgs/msg/string.hpp>
#include <std_srvs/srv/trigger.hpp>

class CartesianImpedanceController : public rclcpp::Node
{
public:
  CartesianImpedanceController() : Node("cartesian_impedance_controller")
  {
    joint_names_ = declare_parameter(
      "joint_names", std::vector<std::string>{
        "shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
        "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"});
    tip_frame_ = declare_parameter("tip_frame", std::string("peg_tip"));
    stiffness_ = declare_parameter(
      "stiffness", std::vector<double>{800.0, 800.0, 800.0, 30.0, 30.0, 30.0});
    m_eff_lin_ = declare_parameter("m_eff_lin", 0.3);
    m_eff_rot_ = declare_parameter("m_eff_rot", 0.0005);
    joint_damping_ = declare_parameter("joint_damping", 0.1);   // extra viscous term, N m s/rad (UR3 wrists are very light: keep d*dt/I < 2)
    effort_limits_ = declare_parameter(
      "effort_limits", std::vector<double>{56.0, 56.0, 28.0, 12.0, 12.0, 12.0});
    gravity_scale_ = declare_parameter("gravity_scale", 1.0);
    rate_hz_ = declare_parameter("publish_rate_hz", 500.0);
    sim_time_timer_ = declare_parameter("sim_time_timer", true);
    if (joint_names_.size() != 6 || stiffness_.size() != 6 || effort_limits_.size() != 6) {
      throw std::runtime_error("joint_names, stiffness and effort_limits must have 6 entries");
    }

    target_sub_ = create_subscription<geometry_msgs::msg::PoseStamped>(
      "~/target_pose", 10,
      [this](geometry_msgs::msg::PoseStamped::SharedPtr m) {
        std::lock_guard<std::mutex> l(m_);
        x_des_ = Eigen::Vector3d(m->pose.position.x, m->pose.position.y, m->pose.position.z);
        R_des_ = Eigen::Quaterniond(
          m->pose.orientation.w, m->pose.orientation.x, m->pose.orientation.y,
          m->pose.orientation.z).normalized().toRotationMatrix();
        target_set_ = true;
      });
    stiff_sub_ = create_subscription<std_msgs::msg::Float64MultiArray>(
      "~/stiffness", 10,
      [this](std_msgs::msg::Float64MultiArray::SharedPtr m) {
        if (m->data.size() != 6) {
          RCLCPP_WARN(get_logger(), "stiffness needs 6 values, got %zu", m->data.size());
          return;
        }
        for (double v : m->data) {
          if (!std::isfinite(v) || v < 0.0) {
            return;
          }
        }
        std::lock_guard<std::mutex> l(m_);
        stiffness_ = m->data;
      });
    hold_srv_ = create_service<std_srvs::srv::Trigger>(
      "~/hold_current_pose",
      [this](const std::shared_ptr<std_srvs::srv::Trigger::Request>,
        std::shared_ptr<std_srvs::srv::Trigger::Response> res) {
        std::lock_guard<std::mutex> l(m_);
        res->success = state_ready_;
        res->message = state_ready_ ? "target = current tip pose" : "no joint state yet";
        if (state_ready_) {
          x_des_ = x_; R_des_ = R_; target_set_ = true;
        }
      });

    rclcpp::QoS latched(1);
    latched.transient_local().reliable();
    urdf_sub_ = create_subscription<std_msgs::msg::String>(
      "/robot_description", latched,
      [this](std_msgs::msg::String::SharedPtr m) {
        if (model_ready_) {
          return;
        }
        try {
          pinocchio::urdf::buildModelFromXML(m->data, model_);
          data_ = pinocchio::Data(model_);
          tip_id_ = model_.getFrameId(tip_frame_);
          if (tip_id_ >= static_cast<pinocchio::FrameIndex>(model_.nframes)) {
            RCLCPP_ERROR(get_logger(), "frame '%s' not in URDF", tip_frame_.c_str());
            return;
          }
          model_ready_ = true;
          RCLCPP_INFO(get_logger(), "model built: nq=%d nv=%d tip=%s", model_.nq, model_.nv, tip_frame_.c_str());
        } catch (const std::exception & e) {
          RCLCPP_ERROR(get_logger(), "URDF parse failed: %s", e.what());
        }
      });
    js_sub_ = create_subscription<sensor_msgs::msg::JointState>(
      "/joint_states", rclcpp::SensorDataQoS(),
      [this](sensor_msgs::msg::JointState::SharedPtr m) {
        std::lock_guard<std::mutex> l(m_);
        for (size_t i = 0; i < m->name.size(); ++i) {
          for (size_t j = 0; j < 6; ++j) {
            if (m->name[i] == joint_names_[j]) {
              if (i < m->position.size()) { q_[j] = m->position[i]; seen_[j] = true; }
              if (i < m->velocity.size()) { qd_[j] = m->velocity[i]; }
            }
          }
        }
        state_ready_ = std::all_of(seen_.begin(), seen_.end(), [](bool b) { return b; });
      });
    cmd_pub_ = create_publisher<std_msgs::msg::Float64MultiArray>(
      "/forward_command_controller_effort/commands", 10);
    tip_pub_ = create_publisher<geometry_msgs::msg::PoseStamped>("~/tip_pose", 10);

    const auto period = std::chrono::nanoseconds(static_cast<long>(1e9 / rate_hz_));
    if (sim_time_timer_) {
      timer_ = rclcpp::create_timer(this, get_clock(), rclcpp::Duration(period), [this]() { update(); });
    } else {
      timer_ = create_wall_timer(period, [this]() { update(); });
    }
  }

private:
  void update()
  {
    if (!model_ready_) {
      return;
    }
    Eigen::VectorXd q = pinocchio::neutral(model_);
    Eigen::VectorXd v = Eigen::VectorXd::Zero(model_.nv);
    Eigen::Matrix<double, 6, 1> k;
    Eigen::Vector3d x_des;
    Eigen::Matrix3d R_des;
    {
      std::lock_guard<std::mutex> l(m_);
      if (!state_ready_) {
        return;
      }
      for (size_t j = 0; j < 6; ++j) {
        const auto jid = model_.getJointId(joint_names_[j]);
        q(model_.joints[jid].idx_q()) = q_[j];
        v(model_.joints[jid].idx_v()) = qd_[j];
      }
      for (int i = 0; i < 6; ++i) { k(i) = stiffness_[i]; }
      x_des = x_des_; R_des = R_des_;
    }

    pinocchio::forwardKinematics(model_, data_, q, v);
    pinocchio::computeJointJacobians(model_, data_, q);
    pinocchio::updateFramePlacements(model_, data_);
    Eigen::Matrix<double, 6, Eigen::Dynamic> J(6, model_.nv);
    J.setZero();
    pinocchio::getFrameJacobian(model_, data_, tip_id_, pinocchio::LOCAL_WORLD_ALIGNED, J);
    const auto & T = data_.oMf[tip_id_];
    const Eigen::Vector3d x = T.translation();
    const Eigen::Matrix3d R = T.rotation();
    const Eigen::Matrix<double, 6, 1> vel = J * v;

    {
      std::lock_guard<std::mutex> l(m_);
      x_ = x; R_ = R;
      if (!target_set_) {      // first tick: hold wherever the tip is
        x_des_ = x; R_des_ = R; target_set_ = true;
        return;
      }
    }

    const Eigen::Matrix3d Re = R_des * R.transpose();
    const Eigen::Vector3d e_rot = 0.5 * Eigen::Vector3d(
      Re(2, 1) - Re(1, 2), Re(0, 2) - Re(2, 0), Re(1, 0) - Re(0, 1));
    Eigen::Matrix<double, 6, 1> wrench;
    for (int i = 0; i < 3; ++i) {
      const double d = 2.0 * std::sqrt(k(i) * m_eff_lin_);
      wrench(i) = k(i) * (x_des(i) - x(i)) - d * vel(i);
    }
    for (int i = 0; i < 3; ++i) {
      const double d = 2.0 * std::sqrt(k(3 + i) * m_eff_rot_);
      wrench(3 + i) = k(3 + i) * e_rot(i) - d * vel(3 + i);
    }

    const Eigen::VectorXd g = pinocchio::computeGeneralizedGravity(model_, data_, q);
    Eigen::VectorXd tau = J.transpose() * wrench + gravity_scale_ * g - joint_damping_ * v;

    std_msgs::msg::Float64MultiArray cmd;
    cmd.data.resize(6);
    for (size_t j = 0; j < 6; ++j) {
      const auto jid = model_.getJointId(joint_names_[j]);
      cmd.data[j] = std::clamp(tau(model_.joints[jid].idx_v()), -effort_limits_[j], effort_limits_[j]);
    }
    cmd_pub_->publish(cmd);

    geometry_msgs::msg::PoseStamped tip;
    tip.header.stamp = now();
    tip.header.frame_id = "base_link";
    tip.pose.position.x = x.x(); tip.pose.position.y = x.y(); tip.pose.position.z = x.z();
    const Eigen::Quaterniond qt(R);
    tip.pose.orientation.w = qt.w(); tip.pose.orientation.x = qt.x();
    tip.pose.orientation.y = qt.y(); tip.pose.orientation.z = qt.z();
    tip_pub_->publish(tip);
  }

  std::vector<std::string> joint_names_;
  std::string tip_frame_;
  std::vector<double> stiffness_, effort_limits_;
  double m_eff_lin_, m_eff_rot_, joint_damping_, gravity_scale_, rate_hz_;
  bool sim_time_timer_;

  pinocchio::Model model_;
  pinocchio::Data data_;
  pinocchio::FrameIndex tip_id_{0};
  bool model_ready_{false};

  std::mutex m_;
  std::array<double, 6> q_{}, qd_{};
  std::array<bool, 6> seen_{};
  bool state_ready_{false}, target_set_{false};
  Eigen::Vector3d x_des_{Eigen::Vector3d::Zero()}, x_{Eigen::Vector3d::Zero()};
  Eigen::Matrix3d R_des_{Eigen::Matrix3d::Identity()}, R_{Eigen::Matrix3d::Identity()};

  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Subscription<geometry_msgs::msg::PoseStamped>::SharedPtr target_sub_;
  rclcpp::Subscription<std_msgs::msg::Float64MultiArray>::SharedPtr stiff_sub_;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr urdf_sub_;
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr js_sub_;
  rclcpp::Publisher<std_msgs::msg::Float64MultiArray>::SharedPtr cmd_pub_;
  rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr tip_pub_;
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr hold_srv_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<CartesianImpedanceController>());
  rclcpp::shutdown();
  return 0;
}
