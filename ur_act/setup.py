from setuptools import setup

package_name = 'ur_act'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='darsh',
    maintainer_email='darshmenon02@gmail.com',
    description='ACT policy for UR3 pick-and-place',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'act_policy_node = ur_act.act_policy_node:main',
        ],
    },
)
