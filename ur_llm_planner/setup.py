from setuptools import setup

package_name = 'ur_llm_planner'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/llm_planner.launch.py']),
        ('share/' + package_name + '/config', ['config/planner_params.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='darsh',
    maintainer_email='darshmenon02@gmail.com',
    description='LLM-driven task planning for UR robot using Ollama',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'llm_planner_node = ur_llm_planner.llm_planner_node:main',
        ],
    },
)
