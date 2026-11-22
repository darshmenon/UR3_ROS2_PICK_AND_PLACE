#!/usr/bin/env python3
"""Put a posed box into the MoveIt planning scene.

FoundationPose (or any other 6-DoF pose source) publishes a PoseStamped.
This node turns that pose into a collision box so MTC plans against the
object instead of an empty scene. The mesh path is not loaded here: MoveIt
already accepts the box, and the same pose is what a mesh would use.

    ros2 run ur_perception pose_to_scene_node --ros-args \
        -p pose_topic:=/foundationpose/pose -p size:="[0.06, 0.06, 0.08]"
"""

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Pose, PoseStamped
from moveit_msgs.msg import CollisionObject, PlanningScene
from shape_msgs.msg import SolidPrimitive

from ur_perception.scene_geometry import box_at_pose


class PoseToScene(Node):
    def __init__(self):
        super().__init__("pose_to_scene")
        self.declare_parameter("pose_topic", "/foundationpose/pose")
        self.declare_parameter("object_id", "posed_object")
        self.declare_parameter("size", [0.06, 0.06, 0.08])
        self._object_id = self.get_parameter("object_id").value
        self._size = [float(v) for v in self.get_parameter("size").value]
        self._pub = self.create_publisher(PlanningScene, "/planning_scene", 10)
        topic = self.get_parameter("pose_topic").value
        self.create_subscription(PoseStamped, topic, self._on_pose, 10)
        self.get_logger().info(f"pose_to_scene listening on {topic}")

    def _on_pose(self, msg: PoseStamped) -> None:
        p = msg.pose.position
        center, size = box_at_pose((p.x, p.y, p.z), self._size)
        obj = CollisionObject()
        obj.header = msg.header
        obj.id = self._object_id
        prim = SolidPrimitive()
        prim.type = SolidPrimitive.BOX
        prim.dimensions = [float(size[0]), float(size[1]), float(size[2])]
        pose = Pose()
        pose.position.x = float(center[0])
        pose.position.y = float(center[1])
        pose.position.z = float(center[2])
        pose.orientation = msg.pose.orientation
        obj.primitives.append(prim)
        obj.primitive_poses.append(pose)
        obj.operation = CollisionObject.ADD
        scene = PlanningScene()
        scene.is_diff = True
        scene.world.collision_objects.append(obj)
        self._pub.publish(scene)


def main(args=None):
    rclpy.init(args=args)
    node = PoseToScene()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
