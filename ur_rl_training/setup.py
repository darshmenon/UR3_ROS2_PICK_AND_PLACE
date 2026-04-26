from setuptools import find_packages, setup
import os
from glob import glob

package_name = "ur_rl_training"

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
    description="RL training and deployment for UR3 pick-and-place",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "policy_node = ur_rl_training.policy_node:main",
        ],
    },
)
