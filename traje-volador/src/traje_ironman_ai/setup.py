from setuptools import setup

package_name = 'traje_ironman_ai'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', []),
        ('share/' + package_name + '/config', []),
    ],
    install_requires=['setuptools', 'rclpy', 'geometry_msgs', 'sensor_msgs', 'nav_msgs', 'std_msgs'],
    zip_safe=True,
    author='Traje Ironman Team',
    author_email='developer@traje-ironman.dev',
    maintainer='Traje Ironman Team',
    maintainer_email='developer@traje-ironman.dev',
    url='https://github.com/luclopez1/traje-ironman',
    description='ROS2 AI control system for EDF+RCS personal flight suit',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'sensor_fusion = traje_ironman_ai.sensor_fusion_node:main',
            'flight_controller = traje_ironman_ai.flight_controller_node:main',
            'motor_manager = traje_ironman_ai.motor_manager_node:main',
            'obstacle_detection = traje_ironman_ai.obstacle_detection_node:main',
            'route_planner = traje_ironman_ai.route_planner_node:main',
            'pilot_learning = traje_ironman_ai.pilot_learning_node:main',
            'energy_manager = traje_ironman_ai.energy_manager_node:main',
            'emergency = traje_ironman_ai.emergency_node:main',
            'hud_manager = traje_ironman_ai.hud_manager_node:main',
        ],
    },
)
