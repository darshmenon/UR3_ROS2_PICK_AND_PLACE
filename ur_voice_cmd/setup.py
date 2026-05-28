from setuptools import setup

package_name = "ur_voice_cmd"

setup(
    name=package_name,
    version="0.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/voice_cmd.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="darsh",
    maintainer_email="darshmenon02@gmail.com",
    description="Voice-to-command bridge: mic -> STT -> LLM planner",
    license="MIT",
    entry_points={
        "console_scripts": [
            "voice_cmd_node.py = ur_voice_cmd.voice_cmd_node:main",
        ],
    },
)
