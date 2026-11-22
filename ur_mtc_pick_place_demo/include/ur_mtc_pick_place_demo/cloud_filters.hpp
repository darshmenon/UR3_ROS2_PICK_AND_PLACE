#ifndef UR_MTC_PICK_PLACE_DEMO__CLOUD_FILTERS_HPP_
#define UR_MTC_PICK_PLACE_DEMO__CLOUD_FILTERS_HPP_

#include <algorithm>
#include <cmath>
#include <string>
#include <tuple>
#include <vector>

#include <Eigen/Dense>

namespace ur_mtc {

// True when (x, y, z) lies inside `radius` of any link origin. radius <= 0 or an empty
// centre list keeps every point (the mask is off).
inline bool pointNearLinks(double x, double y, double z,
                           const std::vector<Eigen::Vector3d>& centers, double radius) {
  if (radius <= 0.0 || centers.empty()) return false;
  const double r2 = radius * radius;
  for (const auto& c : centers) {
    const double dx = x - c.x();
    const double dy = y - c.y();
    const double dz = z - c.z();
    if (dx * dx + dy * dy + dz * dz < r2) return true;
  }
  return false;
}

// q in [0, 1]. Matches the detector: index = q * (n - 1) after an ascending sort, truncated.
inline double percentile(std::vector<double> values, double q) {
  if (values.empty()) return 0.0;
  std::sort(values.begin(), values.end());
  const double pos = std::clamp(q, 0.0, 1.0) * static_cast<double>(values.size() - 1);
  return values[static_cast<size_t>(pos)];
}

// The simple detector's size gate. A cluster is dropped when its footprint is too big,
// its height is outside [min_height, max_height], or its centre is left of min_x.
inline bool rejectBySize(double footprint_w, double footprint_l, double height, double ox,
                         double max_footprint, double min_height, double max_height, double min_x) {
  return std::max(footprint_w, footprint_l) > max_footprint || height < min_height ||
         height > max_height || ox < min_x;
}

// One previously seen cluster. Ids stay with the object when the detector
// emits clusters in a different order next frame.
struct ObjectTrack {
  std::string id;
  std::string shape;
  double x;
  double y;
};

// Match each detection to the nearest unused same-shape track inside match_m.
// Anything farther away keeps a new id so a swapped cluster order cannot rename
// a stationary object. Tracks that disappear are kept, so the id is still there
// if the object returns inside the match radius.
inline std::vector<std::string> assignStableIds(const std::vector<std::string>& shapes,
                                                const std::vector<double>& xs,
                                                const std::vector<double>& ys,
                                                std::vector<ObjectTrack>& tracks,
                                                double match_m, int& next_index) {
  const size_t n = shapes.size();
  std::vector<std::string> ids(n);
  std::vector<std::tuple<double, size_t, size_t>> pairs;
  pairs.reserve(n * tracks.size());
  for (size_t d = 0; d < n; ++d) {
    for (size_t t = 0; t < tracks.size(); ++t) {
      if (tracks[t].shape != shapes[d]) continue;
      const double dist = std::hypot(tracks[t].x - xs[d], tracks[t].y - ys[d]);
      if (dist <= match_m) pairs.emplace_back(dist, d, t);
    }
  }
  std::sort(pairs.begin(), pairs.end(),
            [](const auto& a, const auto& b) { return std::get<0>(a) < std::get<0>(b); });
  std::vector<bool> det_used(n, false);
  std::vector<bool> track_used(tracks.size(), false);
  for (const auto& pair : pairs) {
    const size_t d = std::get<1>(pair);
    const size_t t = std::get<2>(pair);
    if (det_used[d] || track_used[t]) continue;
    det_used[d] = true;
    track_used[t] = true;
    tracks[t].x = xs[d];
    tracks[t].y = ys[d];
    ids[d] = tracks[t].id;
  }
  for (size_t d = 0; d < n; ++d) {
    if (det_used[d]) continue;
    ObjectTrack created;
    created.shape = shapes[d];
    created.x = xs[d];
    created.y = ys[d];
    created.id = shapes[d] + "_" + std::to_string(next_index++);
    ids[d] = created.id;
    tracks.push_back(created);
  }
  return ids;
}

}  // namespace ur_mtc

#endif
