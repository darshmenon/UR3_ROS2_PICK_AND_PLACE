from glob import glob

from setuptools import setup


package_name = "mujoco_ur_rl_ros2"


setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="darshmenon",
    maintainer_email="darshmenon02@gmail.com",
    description="ROS 2 policy runner and launch files for mujoco-ur-arm-rl.",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "ur_policy_node = mujoco_ur_rl_ros2.ur_policy_node:main",
            "shared_arm_policy_node = mujoco_ur_rl_ros2.shared_arm_policy_node:main",
        ],
    },
)
