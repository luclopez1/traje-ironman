#!/usr/bin/env python3
"""
Sensor Fusion Node - Filters and fuses all sensor data using Extended Kalman Filter.
Publishes optimal state estimation: position, velocity, orientation.
Frequency: 100 Hz (10ms)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, NavSatFix, FluidPressure
from geometry_msgs.msg import PoseWithCovariance, TwistWithCovariance, Pose, Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32
from filterpy.kalman import ExtendedKalmanFilter
from filterpy.common import Q_discrete_white_noise
import numpy as np
from dataclasses import dataclass
from typing import Tuple


@dataclass
class SensorState:
    """Current fusion state"""
    position: np.ndarray  # [x, y, z]
    velocity: np.ndarray  # [vx, vy, vz]
    orientation: np.ndarray  # [qx, qy, qz, qw]
    angular_velocity: np.ndarray  # [wx, wy, wz]
    timestamp: float


class SensorFusionNode(Node):
    def __init__(self):
        super().__init__('sensor_fusion_node')

        # Kalman Filter initialization
        self.ekf = ExtendedKalmanFilter(dim_x=12, dim_z=9)  # 12 states, 9 measurements
        self._init_kalman_filter()

        # State management
        self.state = SensorState(
            position=np.array([0.0, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            orientation=np.array([0.0, 0.0, 0.0, 1.0]),
            angular_velocity=np.array([0.0, 0.0, 0.0]),
            timestamp=0.0
        )

        # Subscriptions
        self.imu_sub = self.create_subscription(Imu, '/imu/data', self._imu_callback, 10)
        self.gps_sub = self.create_subscription(NavSatFix, '/gps/fix', self._gps_callback, 10)
        self.barometer_sub = self.create_subscription(FluidPressure, '/barometer', self._barometer_callback, 10)
        self.lidar_height_sub = self.create_subscription(Float32, '/lidar/height', self._lidar_callback, 10)

        # Publishers
        self.state_pub = self.create_publisher(Odometry, '/state_estimate', 10)
        self.pose_pub = self.create_publisher(Pose, '/pose_estimate', 10)

        # Timer for main loop (100 Hz)
        self.timer = self.create_timer(0.01, self._fusion_loop)

        self.get_logger().info('Sensor Fusion Node started')

    def _init_kalman_filter(self):
        """Initialize EKF parameters"""
        # Initial state [x, y, z, vx, vy, vz, qx, qy, qz, qw, wx, wy, wz]
        self.ekf.x = np.array([0., 0., 0., 0., 0., 0., 0., 0., 0., 1., 0., 0., 0.])

        # Process noise
        q_xyz = Q_discrete_white_noise(dim=2, dt=0.01, var=0.01)
        self.ekf.Q = np.eye(12) * 0.001
        self.ekf.Q[0:2, 0:2] = q_xyz[0:2, 0:2]
        self.ekf.Q[1:3, 1:3] = q_xyz[0:2, 0:2]

        # Measurement noise covariance
        self.ekf.R = np.eye(9) * 0.1

        # Initial state covariance
        self.ekf.P = np.eye(12) * 1.0

    def _imu_callback(self, msg: Imu):
        """Process IMU data"""
        # Store angular velocity
        self.state.angular_velocity = np.array([
            msg.angular_velocity.x,
            msg.angular_velocity.y,
            msg.angular_velocity.z
        ])

    def _gps_callback(self, msg: NavSatFix):
        """Process GPS data - convert to local coordinates"""
        # Simple conversion (should use proper coordinate system in production)
        # Latitude/longitude to meters (approximation)
        earth_radius = 6371000  # meters
        lat_m = np.radians(msg.latitude) * earth_radius
        lon_m = np.radians(msg.longitude) * earth_radius

        # Store in EKF measurement
        self.gps_pos = np.array([lat_m, lon_m])
        self.gps_cov = msg.position_covariance

    def _barometer_callback(self, msg: FluidPressure):
        """Process barometric pressure - convert to altitude"""
        # Simple barometric formula (altitude from pressure)
        P0 = 101325.0  # Sea level pressure in Pa
        T0 = 288.15  # Sea level temperature in K
        L = 0.0065  # Temperature lapse rate

        altitude = (T0 / L) * ((msg.fluid_pressure / P0) ** (-L * 29.271 / 8.314) - 1)
        self.barometer_alt = altitude

    def _lidar_callback(self, msg: Float32):
        """Process LIDAR height measurement"""
        self.lidar_height = msg.data

    def _fusion_loop(self):
        """Main fusion loop - 100 Hz"""
        # Prediction step
        dt = 0.01
        self._ekf_predict(dt)

        # Update step with available measurements
        if hasattr(self, 'gps_pos'):
            z = np.concatenate([self.gps_pos, [self.barometer_alt if hasattr(self, 'barometer_alt') else 0]])
            H = np.zeros((3, 12))
            H[0:2, 0:2] = np.eye(2)  # Position from GPS
            H[2, 2] = 1.0  # Altitude from barometer
            self._ekf_update(z, H)

        # Extract state
        self.state.position = self.ekf.x[0:3]
        self.state.velocity = self.ekf.x[3:6]
        self.state.orientation = self.ekf.x[6:10]

        # Publish state
        self._publish_state()

    def _ekf_predict(self, dt: float):
        """EKF prediction step"""
        # Simple kinematic model
        F = np.eye(12)
        F[0:3, 3:6] = np.eye(3) * dt  # Position += velocity * dt

        self.ekf.F = F
        self.ekf.predict()

    def _ekf_update(self, z: np.ndarray, H: np.ndarray):
        """EKF update step"""
        self.ekf.H = H
        self.ekf.update(z)

    def _publish_state(self):
        """Publish fused state estimation"""
        odometry = Odometry()
        odometry.header.stamp = self.get_clock().now().to_msg()
        odometry.header.frame_id = 'world'

        # Position
        odometry.pose.pose.position.x = float(self.state.position[0])
        odometry.pose.pose.position.y = float(self.state.position[1])
        odometry.pose.pose.position.z = float(self.state.position[2])

        # Orientation (quaternion)
        odometry.pose.pose.orientation.x = float(self.state.orientation[0])
        odometry.pose.pose.orientation.y = float(self.state.orientation[1])
        odometry.pose.pose.orientation.z = float(self.state.orientation[2])
        odometry.pose.pose.orientation.w = float(self.state.orientation[3])

        # Velocity
        odometry.twist.twist.linear.x = float(self.state.velocity[0])
        odometry.twist.twist.linear.y = float(self.state.velocity[1])
        odometry.twist.twist.linear.z = float(self.state.velocity[2])

        # Angular velocity
        odometry.twist.twist.angular.x = float(self.state.angular_velocity[0])
        odometry.twist.twist.angular.y = float(self.state.angular_velocity[1])
        odometry.twist.twist.angular.z = float(self.state.angular_velocity[2])

        self.state_pub.publish(odometry)


def main(args=None):
    rclpy.init(args=args)
    node = SensorFusionNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
