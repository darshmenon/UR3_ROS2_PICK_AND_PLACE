from setuptools import setup

package_name = "ur_sorting_demo"

setup(
    name=package_name,
    version="0.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/sorting_demo.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="darsh",
    maintainer_email="darshmenon02@gmail.com",
    description="Multi-object color sorting coordinator for UR3",
    license="MIT",
    entry_points={
        "console_scripts": [
            "sorting_node.py = ur_sorting_demo.sorting_node:main",
        ],
    },
)
