from setuptools import setup

package_name = "ur_conveyor"

setup(
    name=package_name,
    version="0.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/conveyor.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="darsh",
    maintainer_email="darshmenon02@gmail.com",
    description="Conveyor belt simulation for UR3",
    license="MIT",
    entry_points={
        "console_scripts": [
            "conveyor_node.py = ur_conveyor.conveyor_node:main",
        ],
    },
)
