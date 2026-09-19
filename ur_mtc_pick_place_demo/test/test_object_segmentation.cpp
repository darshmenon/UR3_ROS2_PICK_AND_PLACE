/**
 * @file test_object_segmentation.cpp
 * @brief Unit tests for estimateClusterTiltQuaternion (PCA-based tilt
 * estimation added 2026-09-19) against synthetic point clouds, since this
 * logic has never been exercised via a live sim run.
 */

#include <cmath>

#include <gtest/gtest.h>
#include <Eigen/Dense>

#include "ur_mtc_pick_place_demo/object_segmentation.h"

namespace {

// Build a synthetic partial-view cylindrical-shell point cloud: points on a
// cylinder's curved surface, visible from one side (a ~180-degree arc), with
// its axis rotated by `axis_tilt_rad` away from world +Z about the X axis.
// This approximates what a real depth camera would see of a cylinder resting
// on (or tilted against) a support surface -- not a full solid cylinder.
pcl::PointCloud<PointXYZRGBNormalRSD>::Ptr makeTiltedCylinderCluster(
    double axis_tilt_rad, double radius = 0.018, double height = 0.14,
    int n_height = 20, int n_arc = 20) {
  auto cloud = pcl::PointCloud<PointXYZRGBNormalRSD>::Ptr(
      new pcl::PointCloud<PointXYZRGBNormalRSD>());

  Eigen::Matrix3d tilt = Eigen::AngleAxisd(axis_tilt_rad, Eigen::Vector3d::UnitX()).toRotationMatrix();

  for (int i = 0; i < n_height; ++i) {
    double h = (static_cast<double>(i) / (n_height - 1)) * height;
    for (int j = 0; j < n_arc; ++j) {
      double theta = M_PI * static_cast<double>(j) / (n_arc - 1) - M_PI_2;  // front-facing arc
      Eigen::Vector3d local(radius * std::cos(theta), radius * std::sin(theta), h);
      Eigen::Vector3d world = tilt * local;

      PointXYZRGBNormalRSD pt;
      pt.x = static_cast<float>(world.x());
      pt.y = static_cast<float>(world.y());
      pt.z = static_cast<float>(world.z());
      pt.normal_x = 0.0f;
      pt.normal_y = 0.0f;
      pt.normal_z = 1.0f;
      pt.curvature = 0.0f;
      pt.r_min = 0.0f;
      pt.r_max = 0.0f;
      cloud->points.push_back(pt);
    }
  }
  cloud->width = cloud->points.size();
  cloud->height = 1;
  cloud->is_dense = true;
  return cloud;
}

}  // namespace

TEST(EstimateClusterTiltQuaternion, UprightClusterReturnsIdentity) {
  auto cluster = makeTiltedCylinderCluster(0.0);
  Eigen::Quaterniond q = estimateClusterTiltQuaternion(cluster);
  EXPECT_NEAR(std::abs(q.w()), 1.0, 1e-6);
}

TEST(EstimateClusterTiltQuaternion, SmallTiltBelowThresholdStaysIdentity) {
  // 5 degrees, well under the default ~15-degree threshold.
  auto cluster = makeTiltedCylinderCluster(5.0 * M_PI / 180.0);
  Eigen::Quaterniond q = estimateClusterTiltQuaternion(cluster);
  EXPECT_NEAR(std::abs(q.w()), 1.0, 1e-3);
}

TEST(EstimateClusterTiltQuaternion, ThirtyDegreeTiltIsDetectedAccurately) {
  const double true_tilt_rad = 30.0 * M_PI / 180.0;
  auto cluster = makeTiltedCylinderCluster(true_tilt_rad);
  Eigen::Quaterniond q = estimateClusterTiltQuaternion(cluster);

  // Recover the tilt angle the quaternion actually represents: the angle
  // between world +Z rotated by q and world +Z itself.
  Eigen::Vector3d rotated_up = q * Eigen::Vector3d::UnitZ();
  double recovered_tilt = std::acos(std::clamp(rotated_up.dot(Eigen::Vector3d::UnitZ()), -1.0, 1.0));

  EXPECT_NEAR(recovered_tilt, true_tilt_rad, 0.05)  // ~3 degrees tolerance
      << "Expected ~30 degree tilt, got " << (recovered_tilt * 180.0 / M_PI) << " degrees";
}

TEST(EstimateClusterTiltQuaternion, SixtyDegreeToppledClusterIsDetected) {
  const double true_tilt_rad = 60.0 * M_PI / 180.0;
  auto cluster = makeTiltedCylinderCluster(true_tilt_rad);
  Eigen::Quaterniond q = estimateClusterTiltQuaternion(cluster);

  Eigen::Vector3d rotated_up = q * Eigen::Vector3d::UnitZ();
  double recovered_tilt = std::acos(std::clamp(rotated_up.dot(Eigen::Vector3d::UnitZ()), -1.0, 1.0));

  EXPECT_NEAR(recovered_tilt, true_tilt_rad, 0.05)
      << "Expected ~60 degree tilt, got " << (recovered_tilt * 180.0 / M_PI) << " degrees";
}

int main(int argc, char** argv) {
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
