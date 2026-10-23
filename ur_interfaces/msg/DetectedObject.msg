# A single detected object in the scene
string id              # Unique object identifier, e.g. "red_0"
string label           # Human-readable label, e.g. "red box"
geometry_msgs/Point position  # Position in base_link frame (meters)
geometry_msgs/Vector3 dimensions  # Bounding box dimensions (x=length, y=width, z=height)
float32 confidence     # Detection confidence [0.0, 1.0]
float32 yaw            # Rotation of a box about base_link z (rad, folded to [-pi/4, pi/4)); 0 for round objects
