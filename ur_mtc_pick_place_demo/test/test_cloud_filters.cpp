#include <cmath>
#include <vector>

#include <gtest/gtest.h>
#include <Eigen/Dense>

#include "ur_mtc_pick_place_demo/cloud_filters.hpp"

TEST(CloudFilters, MaskDropsPointsInsideRadiusOnly) {
  const std::vector<Eigen::Vector3d> links = {Eigen::Vector3d(0.2, 0.0, 0.4)};
  EXPECT_TRUE(ur_mtc::pointNearLinks(0.25, 0.0, 0.4, links, 0.12));
  EXPECT_FALSE(ur_mtc::pointNearLinks(0.40, 0.0, 0.4, links, 0.12));
  EXPECT_FALSE(ur_mtc::pointNearLinks(0.25, 0.0, 0.4, links, 0.0));
  EXPECT_FALSE(ur_mtc::pointNearLinks(0.25, 0.0, 0.4, {}, 0.12));
}

TEST(CloudFilters, HeightPercentileIgnoresAStrayHighPoint) {
  std::vector<double> z(50, 0.10);
  z.push_back(0.80);
  EXPECT_NEAR(ur_mtc::percentile(z, 0.98), 0.10, 1e-9);
  EXPECT_NEAR(ur_mtc::percentile(z, 1.0), 0.80, 1e-9);
}

TEST(CloudFilters, StableIdsSurviveASwappedClusterOrder) {
  std::vector<ur_mtc::ObjectTrack> tracks;
  int next = 0;
  const auto first = ur_mtc::assignStableIds(
      {"cylinder", "cylinder"}, {0.30, 0.30}, {0.10, -0.10}, tracks, 0.04, next);
  const auto second = ur_mtc::assignStableIds(
      {"cylinder", "cylinder"}, {0.30, 0.31}, {-0.10, 0.11}, tracks, 0.04, next);
  EXPECT_EQ(first[0], second[1]);
  EXPECT_EQ(first[1], second[0]);
  const auto jumped = ur_mtc::assignStableIds(
      {"cylinder"}, {0.30}, {0.40}, tracks, 0.04, next);
  EXPECT_NE(jumped[0], first[0]);
  EXPECT_NE(jumped[0], first[1]);
}

TEST(CloudFilters, SizeGateRejectsTheRobotAndKeepsAGraspableObject) {
  EXPECT_TRUE(ur_mtc::rejectBySize(0.05, 0.05, 0.40, 0.30, 0.20, 0.01, 0.20, 0.05));
  EXPECT_TRUE(ur_mtc::rejectBySize(0.30, 0.05, 0.05, 0.30, 0.20, 0.01, 0.20, 0.05));
  EXPECT_TRUE(ur_mtc::rejectBySize(0.05, 0.05, 0.005, 0.30, 0.20, 0.01, 0.20, 0.05));
  EXPECT_TRUE(ur_mtc::rejectBySize(0.05, 0.05, 0.05, 0.00, 0.20, 0.01, 0.20, 0.05));
  EXPECT_FALSE(ur_mtc::rejectBySize(0.05, 0.05, 0.05, 0.30, 0.20, 0.01, 0.20, 0.05));
}
