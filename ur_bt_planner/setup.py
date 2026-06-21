from setuptools import setup

package_name = "ur_bt_planner"

setup(
    name=package_name,
    version="0.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/bt_planner.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="darsh",
    maintainer_email="darshmenon02@gmail.com",
    description="Behavior tree task planner for UR3 pick-and-place",
    license="MIT",
    entry_points={
        "console_scripts": [
            "bt_planner_node.py = ur_bt_planner.bt_planner_node:main",
        ],
    },
)
