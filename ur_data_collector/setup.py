from setuptools import setup

package_name = 'ur_data_collector'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='darsh',
    maintainer_email='darshmenon02@gmail.com',
    description='Records robot demonstrations for behavior cloning and VLA fine-tuning',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'collector_node = ur_data_collector.collector_node:main',
        ],
    },
)
