import os
from glob import glob
from setuptools import setup

package_name = 'ur_scene_from_splat'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='darsh',
    maintainer_email='darshmenon02@gmail.com',
    description='Gaussian-splat point cloud to Gazebo scene exporter',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'splat2scene = ur_scene_from_splat.splat2scene:main',
        ],
    },
)
