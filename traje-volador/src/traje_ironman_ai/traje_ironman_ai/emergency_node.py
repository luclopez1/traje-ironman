#!/usr/bin/env python3
"""
Emergency Node - Monitors pilot health and manages emergency procedures.
Detects unconsciousness, system failures, and initiates safety protocols.
Frequency: 10 Hz (100ms updates for critical monitoring)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Bool, String, Float32MultiArray
from geometry_msgs.msg import PoseStamped, Point
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
import numpy as np
from dataclasses import dataclass
from typing import Optional
from enum import Enum
from collections import deque


class PilotStatus(Enum):
    """Pilot health status"""
    CONSCIOUS = 1
    DEGRADED = 2
    UNCONSCIOUS = 3
    CRITICAL = 4


@dataclass
class PilotVitals:
    """Pilot health metrics"""
    heart_rate: float  # BPM
    blood_oxygen: float  # SpO2 percentage
    body_temperature: float  # Celsius
    respiration_rate: float  # breaths per minute
    eye_open: bool
    movement_detected: bool
    voice_responsive: bool


class EmergencyNode(Node):
    def __init__(self):
        super().__init__('emergency_node')

        # Pilot vitals monitoring
        self.pilot_vitals = PilotVitals(
            heart_rate=70.0,
            blood_oxygen=98.0,
            body_temperature=37.0,
            respiration_rate=15.0,
            eye_open=True,
            movement_detected=True,
            voice_responsive=True
        )

        # Emergency state tracking
        self.pilot_status = PilotStatus.CONSCIOUS
        self.unconscious_counter = 0
        self.unconscious_threshold = 30  # 3 seconds at 10Hz
        self.last_response_time = None

        # Emergency response protocol
        self.emergency_active = False
        self.home_position = np.array([0.0, 0.0, 0.0])
        self.current_position = np.array([0.0, 0.0, 0.0])
        self.descent_rate = 0.5  # m/s for emergency descent

        # System faults
        self.critical_faults: deque = deque(maxlen=10)
        self.motor_faults = [False] * 8
        self.sensor_failures = []

        # Emergency contacts and settings
        self.emergency_contact = '+1-234-567-8900'
        self.gps_location = None
        self.emergency_message = ''

        # Subscriptions
        self.vitals_sub = self.create_subscription(
            Float32MultiArray, '/pilot_vitals', self._vitals_callback, 10
        )

        self.imu_sub = self.create_subscription(
            Imu, '/imu/data', self._imu_callback, 10
        )

        self.state_sub = self.create_subscription(
            Odometry, '/state_estimate', self._state_callback, 10
        )

        self.motor_status_sub = self.create_subscription(
            Float32MultiArray, '/motor_status', self._motor_status_callback, 10
        )

        self.battery_warning_sub = self.create_subscription(
            Bool, '/battery_warning', self._battery_warning_callback, 10
        )

        # Publishers
        self.pilot_status_pub = self.create_publisher(String, '/pilot_status', 10)
        self.emergency_landing_pub = self.create_publisher(Bool, '/emergency_landing', 10)
        self.home_return_pub = self.create_publisher(PoseStamped, '/home_position', 10)
        self.alert_pub = self.create_publisher(String, '/system_alert', 10)
        self.water_sprayer_pub = self.create_publisher(Bool, '/water_sprayer', 10)

        # Timer for monitoring (10 Hz)
        self.timer = self.create_timer(0.1, self._emergency_check_loop)

        self.get_logger().info('Emergency Node started')

    def _vitals_callback(self, msg: Float32MultiArray):
        """Update pilot vitals from biometric sensors"""
        if len(msg.data) >= 6:
            self.pilot_vitals.heart_rate = msg.data[0]
            self.pilot_vitals.blood_oxygen = msg.data[1]
            self.pilot_vitals.body_temperature = msg.data[2]
            self.pilot_vitals.respiration_rate = msg.data[3]
            self.pilot_vitals.eye_open = bool(msg.data[4])
            self.pilot_vitals.movement_detected = bool(msg.data[5])

    def _imu_callback(self, msg: Imu):
        """Detect pilot movement from IMU"""
        # Check for significant body acceleration
        linear_accel = np.array([
            msg.linear_acceleration.x,
            msg.linear_acceleration.y,
            msg.linear_acceleration.z
        ])

        total_accel = np.linalg.norm(linear_accel) - 9.81  # Subtract gravity
        if abs(total_accel) > 1.0:  # >1 m/s² indicates movement
            self.pilot_vitals.movement_detected = True

    def _state_callback(self, msg: Odometry):
        """Update current position for emergency returns"""
        self.current_position = np.array([
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            msg.pose.pose.position.z
        ])

    def _motor_status_callback(self, msg: Float32MultiArray):
        """Monitor motor health"""
        # Check for motor faults
        if len(msg.data) >= 8:
            currents = msg.data[8:16] if len(msg.data) >= 16 else [0] * 8
            for i, current in enumerate(currents):
                if current > 80.0 or (current < 0.1 and i not in self.motor_faults):
                    self.motor_faults[i] = True
                    self.critical_faults.append(f'Motor {i} failure')

    def _battery_warning_callback(self, msg: Bool):
        """Monitor battery status"""
        if msg.data:
            self.critical_faults.append('Battery critical level')

    def _emergency_check_loop(self):
        """Main emergency monitoring loop - 10 Hz"""
        # Check pilot consciousness
        self._check_pilot_consciousness()

        # Check system integrity
        self._check_system_integrity()

        # Manage emergency response
        if self.emergency_active:
            self._execute_emergency_response()

        # Publish status
        self._publish_emergency_status()

    def _check_pilot_consciousness(self):
        """Monitor pilot consciousness using multiple indicators"""
        # Calculate consciousness score (0-10)
        consciousness_score = 10.0

        # Heart rate check (normal: 60-100 bpm)
        if self.pilot_vitals.heart_rate < 40 or self.pilot_vitals.heart_rate > 140:
            consciousness_score -= 3.0
        elif self.pilot_vitals.heart_rate < 50 or self.pilot_vitals.heart_rate > 120:
            consciousness_score -= 1.5

        # Blood oxygen check (normal: >95%)
        if self.pilot_vitals.blood_oxygen < 90:
            consciousness_score -= 3.0
        elif self.pilot_vitals.blood_oxygen < 94:
            consciousness_score -= 1.0

        # Eye open check
        if not self.pilot_vitals.eye_open:
            consciousness_score -= 2.0

        # Movement check
        if not self.pilot_vitals.movement_detected:
            consciousness_score -= 1.0

        # Voice responsiveness
        if not self.pilot_vitals.voice_responsive:
            consciousness_score -= 2.0

        # Body temperature check (normal: 36.5-37.5°C)
        temp_diff = abs(self.pilot_vitals.body_temperature - 37.0)
        if temp_diff > 2.0:
            consciousness_score -= 2.0
        elif temp_diff > 1.0:
            consciousness_score -= 1.0

        # Determine status
        if consciousness_score < 2:
            self.unconscious_counter += 1
        else:
            self.unconscious_counter = max(0, self.unconscious_counter - 1)

        # Update pilot status
        if self.unconscious_counter >= self.unconscious_threshold:
            old_status = self.pilot_status
            self.pilot_status = PilotStatus.UNCONSCIOUS

            if old_status != PilotStatus.UNCONSCIOUS:
                self.get_logger().critical('PILOT UNCONSCIOUS - INITIATING EMERGENCY RESPONSE')
                self.emergency_active = True

        elif consciousness_score < 5:
            self.pilot_status = PilotStatus.DEGRADED

        else:
            self.pilot_status = PilotStatus.CONSCIOUS
            self.emergency_active = False

    def _check_system_integrity(self):
        """Check for critical system failures"""
        critical_failures = 0

        # Check motor failures
        failed_motors = sum(self.motor_faults)
        if failed_motors > 2:  # More than 2 motors failed
            critical_failures += 1
            if failed_motors == 8:  # All motors failed
                self.emergency_active = True
                self.get_logger().fatal('ALL MOTORS FAILED - EMERGENCY DESCENT')

        # Check sensor failures
        if len(self.sensor_failures) > 0:
            self.get_logger().error(f'Sensor failures: {self.sensor_failures}')

    def _execute_emergency_response(self):
        """Execute emergency response protocol"""
        response_stage = min(self.unconscious_counter // 10, 3)

        if response_stage == 0:
            # 30-60 seconds: Verbal warning and vibration
            if self.unconscious_counter == 0:
                self.get_logger().warn('ALERT: Pilot unresponsive - "Are you okay?" prompt')
                # TODO: Send audio/vibration alert
                self.emergency_message = 'Asking pilot status'

        elif response_stage == 1:
            # 60-90 seconds: Initiate gentle descent
            self.emergency_message = 'Initiating gentle descent'
            self._initiate_gentle_descent()

        elif response_stage == 2:
            # 90-120 seconds: Activate automatic return to home
            self.emergency_message = 'Returning to home location'
            self._initiate_return_to_home()

        elif response_stage >= 3:
            # >120 seconds: Emergency landing
            self.emergency_message = 'Emergency landing initiated'
            self._initiate_emergency_landing()

    def _initiate_gentle_descent(self):
        """Start slow controlled descent"""
        descent_cmd = PoseStamped()
        descent_cmd.header.stamp = self.get_clock().now().to_msg()
        descent_cmd.header.frame_id = 'world'

        # Set descent waypoint
        descent_cmd.pose.position.x = float(self.current_position[0])
        descent_cmd.pose.position.y = float(self.current_position[1])
        descent_cmd.pose.position.z = float(max(0.5, self.current_position[2] - self.descent_rate))

        self.home_return_pub.publish(descent_cmd)

    def _initiate_return_to_home(self):
        """Return to home position automatically"""
        home_cmd = PoseStamped()
        home_cmd.header.stamp = self.get_clock().now().to_msg()
        home_cmd.header.frame_id = 'world'

        home_cmd.pose.position.x = float(self.home_position[0])
        home_cmd.pose.position.y = float(self.home_position[1])
        home_cmd.pose.position.z = float(max(self.home_position[2], 50.0))

        self.home_return_pub.publish(home_cmd)

    def _initiate_emergency_landing(self):
        """Emergency landing protocol"""
        emergency_landing_msg = Bool()
        emergency_landing_msg.data = True
        self.emergency_landing_pub.publish(emergency_landing_msg)

        # Activate water sprayers if fire detected
        self._activate_safety_systems()

        # Send emergency alert
        self._send_emergency_alert()

    def _activate_safety_systems(self):
        """Activate protective systems"""
        # Water sprayers for fire suppression
        sprayer_cmd = Bool()
        sprayer_cmd.data = True
        self.water_sprayer_pub.publish(sprayer_cmd)

        self.get_logger().warn('Safety systems activated: water sprayers')

    def _send_emergency_alert(self):
        """Send emergency alerts and notifications"""
        # In production: send SMS/4G emergency call
        self.get_logger().critical(
            f'EMERGENCY ALERT: Pilot {self.pilot_status.name} at GPS {self.gps_location} - '
            f'Contact: {self.emergency_contact}'
        )

        # Publish alert
        alert_msg = String()
        alert_msg.data = (
            f'EMERGENCY: {self.emergency_message} - '
            f'Pilot status: {self.pilot_status.name} - '
            f'Position: {self.current_position}'
        )
        self.alert_pub.publish(alert_msg)

    def _publish_emergency_status(self):
        """Publish current emergency status"""
        status_msg = String()

        status_parts = [
            f'Pilot: {self.pilot_status.name}',
            f'HR: {self.pilot_vitals.heart_rate:.0f} BPM',
            f'SpO2: {self.pilot_vitals.blood_oxygen:.1f}%',
            f'Temp: {self.pilot_vitals.body_temperature:.1f}°C'
        ]

        if self.motor_faults.count(True) > 0:
            status_parts.append(f'Motor faults: {self.motor_faults.count(True)}')

        if self.emergency_active:
            status_parts.append(f'EMERGENCY: {self.emergency_message}')

        status_msg.data = ' | '.join(status_parts)
        self.pilot_status_pub.publish(status_msg)


def main(args=None):
    rclpy.init(args=args)
    node = EmergencyNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
