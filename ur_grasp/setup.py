from setuptools import find_packages, setup
import os
from glob import glob

package_name = "ur_grasp"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", glob("launch/*.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="darshmenon",
    maintainer_email="darshmenon02@gmail.com",
    description="Grasp detection for UR3 + Robotiq 2F-85",
    license="MIT",
    entry_points={
        "console_scripts": [
            "grasp_node = ur_grasp.grasp_node:main",
        ],
    },
)
