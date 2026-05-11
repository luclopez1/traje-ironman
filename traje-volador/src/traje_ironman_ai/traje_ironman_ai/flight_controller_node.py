#!/usr/bin/env python3
"""
Flight Controller Node - Stabilization and 6-DOF attitude control.
Compares actual state with desired state and calculates control corrections.
Frequency: 100 Hz (10ms)
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, Vector3
from std_msgs.msg import Float32MultiArray
import numpy as np
from dataclasses import dataclass
from typing import Optional


@dataclass
class ControlSetpoint:
    """Desired flight state"""
    position: np.ndarray  # [x, y, z]
    velocity: np.ndarray  # [vx, vy, vz]
    euler_angles: np.ndarray  # [roll, pitch, yaw]
    altitude_mode: bool = True  # True = maintain altitude


class FlightControllerNode(Node):
    def __init__(self):
        super().__init__('flight_controller_node')

        # PID controllers for 6 DOF
        self.pid_controllers = {
            'roll': PIDController(Kp=1.5, Ki=0.1, Kd=0.3),
            'pitch': PIDController(Kp=1.5, Ki=0.1, Kd=0.3),
            'yaw': PIDController(Kp=2.0, Ki=0.05, Kd=0.4),
            'altitude': PIDController(Kp=2.0, Ki=0.2, Kd=0.5),
            'forward': PIDController(Kp=1.0, Ki=0.05, Kd=0.2),
            'lateral': PIDController(Kp=1.0, Ki=0.05, Kd=0.2),
        }

        # Current state
        self.current_state = Odometry()
        self.setpoint = ControlSetpoint(
            position=np.array([0.0, 0.0, 0.0]),
            velocity=np.array([0.0, 0.0, 0.0]),
            euler_angles=np.array([0.0, 0.0, 0.0])
        )

        # Flight parameters
        self.max_tilt_angle = np.radians(45)  # Max 45° tilt
        self.max_vertical_velocity = 2.0  # m/s
        self.control_mode = 'manual'  # manual, assisted, autonomous

        # Subscriptions
        self.state_sub = self.create_subscription(Odometry, '/state_estimate', self._state_callback, 10)
        self.cmd_vel_sub = self.create_subscription(Twist, '/cmd_vel', self._cmd_vel_callback, 10)
        self.setpoint_sub = self.create_subscription(Odometry, '/setpoint', self._setpoint_callback, 10)

        # Publishers
        self.control_output_pub = self.create_publisher(Float32MultiArray, '/control_output', 10)
        self.status_pub = self.create_publisher(Twist, '/flight_status', 10)

        # Timer for main loop (100 Hz)
        self.timer = self.create_timer(0.01, self._control_loop)

        self.get_logger().info('Flight Controller Node started')

    def _state_callback(self, msg: Odometry):
        """Update current state from sensor fusion"""
        self.current_state = msg

    def _cmd_vel_sub(self, msg: Twist):
        """Process velocity commands from pilot/autonomous system"""
        self.setpoint.velocity = np.array([
            msg.linear.x,
            msg.linear.y,
            msg.linear.z
        ])

    def _setpoint_callback(self, msg: Odometry):
        """Update desired state setpoint"""
        self.setpoint.position = np.array([
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            msg.pose.pose.position.z
        ])
        self.setpoint.velocity = np.array([
            msg.twist.twist.linear.x,
            msg.twist.twist.linear.y,
            msg.twist.twist.linear.z
        ])

    def _control_loop(self):
        """Main control loop - 100 Hz"""
        if self.current_state.header.frame_id == '':
            return

        # Extract current state
        pos = np.array([
            self.current_state.pose.pose.position.x,
            self.current_state.pose.pose.position.y,
            self.current_state.pose.pose.position.z
        ])

        vel = np.array([
            self.current_state.twist.twist.linear.x,
            self.current_state.twist.twist.linear.y,
            self.current_state.twist.twist.linear.z
        ])

        # Calculate position errors
        pos_error = self.setpoint.position - pos
        vel_error = self.setpoint.velocity - vel

        # Extract current orientation (quaternion to euler)
        qx = self.current_state.pose.pose.orientation.x
        qy = self.current_state.pose.pose.orientation.y
        qz = self.current_state.pose.pose.orientation.z
        qw = self.current_state.pose.pose.orientation.w
        roll, pitch, yaw = self._quat_to_euler(qx, qy, qz, qw)

        # Control algorithm for 6 DOF

        # 1. Altitude control (Z axis)
        alt_error = pos_error[2]
        alt_correction = self.pid_controllers['altitude'].update(alt_error, 0.01)
        alt_correction = np.clip(alt_correction, -self.max_vertical_velocity, self.max_vertical_velocity)

        # 2. Forward/Backward (X axis) - tilt pitch
        forward_error = pos_error[0]
        forward_correction = self.pid_controllers['forward'].update(forward_error, 0.01)
        pitch_cmd = np.clip(forward_correction, -self.max_tilt_angle, self.max_tilt_angle)

        # 3. Lateral (Y axis) - tilt roll
        lateral_error = pos_error[1]
        lateral_correction = self.pid_controllers['lateral'].update(lateral_error, 0.01)
        roll_cmd = np.clip(lateral_correction, -self.max_tilt_angle, self.max_tilt_angle)

        # 4. Yaw (rotation around Z) - RCS control
        yaw_error = 0.0  # TODO: Get desired yaw from setpoint
        yaw_correction = self.pid_controllers['yaw'].update(yaw_error, 0.01)

        # Stability corrections for small perturbations
        pitch_error = pitch_cmd - pitch
        roll_error = roll_cmd - roll
        yaw_error_stabilize = -yaw  # Return to level

        # Generate control outputs for 8 EDFs + 16 RCS
        control_output = self._generate_motor_commands(
            alt_correction, pitch_error, roll_error, yaw_correction
        )

        # Publish control output
        self._publish_control_output(control_output)

    def _quat_to_euler(self, x: float, y: float, z: float, w: float) -> tuple:
        """Convert quaternion to Euler angles"""
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = np.arctan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        sinp = np.clip(sinp, -1, 1)
        pitch = np.arcsin(sinp)

        # Yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = np.arctan2(siny_cosp, cosy_cosp)

        return roll, pitch, yaw

    def _generate_motor_commands(
        self,
        thrust_correction: float,
        pitch_correction: float,
        roll_correction: float,
        yaw_correction: float
    ) -> np.ndarray:
        """
        Generate commands for 8 EDFs and 16 RCS nozzles.
        Returns array: [edf0...edf7, rcs0...rcs15]
        EDF layout: shoulder0, shoulder1, dorsal0, dorsal1, hip0, hip1, calf0, calf1
        RCS layout: 16 nozzles (pitch, roll, yaw control)
        """
        commands = np.zeros(24)  # 8 EDF + 16 RCS

        # Base thrust for hover (approximately 60% of max to avoid saturation)
        base_thrust = 2500.0  # PWM value 0-5000

        # Distribute thrust among EDFs
        # Vertical: all EDFs contribute equally
        # Pitch: dorsal (front) more than hip (rear)
        # Roll: left/right differential
        # Yaw: handled by RCS only

        shoulder_thrust = base_thrust + thrust_correction * 500
        dorsal_thrust = base_thrust + thrust_correction * 500 + pitch_correction * 300
        hip_thrust = base_thrust + thrust_correction * 500 - pitch_correction * 200
        calf_thrust = base_thrust + thrust_correction * 500

        # Apply roll correction (differential thrust)
        commands[0] = shoulder_thrust - roll_correction * 300  # Left shoulder
        commands[1] = shoulder_thrust + roll_correction * 300  # Right shoulder
        commands[2] = dorsal_thrust - roll_correction * 300    # Left dorsal
        commands[3] = dorsal_thrust + roll_correction * 300    # Right dorsal
        commands[4] = hip_thrust - roll_correction * 300       # Left hip
        commands[5] = hip_thrust + roll_correction * 300       # Right hip
        commands[6] = calf_thrust - roll_correction * 300      # Left calf
        commands[7] = calf_thrust + roll_correction * 300      # Right calf

        # Clamp EDF commands to valid range
        for i in range(8):
            commands[i] = np.clip(commands[i], 1000, 5000)

        # RCS commands (bang-bang control)
        # Nozzles 0-1: pitch front, 2-3: pitch rear
        # Nozzles 4-5: roll left, 6-7: roll right
        # Nozzles 8-15: yaw and additional control
        if abs(pitch_correction) > 0.05:
            if pitch_correction > 0:
                commands[8] = 1 if abs(pitch_correction) > 0.1 else 0  # Pitch up front
            else:
                commands[10] = 1  # Pitch down rear

        if abs(roll_correction) > 0.05:
            if roll_correction > 0:
                commands[12] = 1 if abs(roll_correction) > 0.1 else 0  # Roll right
            else:
                commands[14] = 1  # Roll left

        if abs(yaw_correction) > 0.1:
            if yaw_correction > 0:
                commands[16:18] = 1  # Yaw right
            else:
                commands[18:20] = 1  # Yaw left

        return commands

    def _publish_control_output(self, commands: np.ndarray):
        """Publish motor commands to motor manager"""
        msg = Float32MultiArray()
        msg.data = commands.tolist()
        self.control_output_pub.publish(msg)


class PIDController:
    """Simple PID controller"""

    def __init__(self, Kp: float, Ki: float, Kd: float):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.integral = 0.0
        self.last_error = 0.0

    def update(self, error: float, dt: float) -> float:
        """Update PID and return output"""
        self.integral += error * dt
        self.integral = np.clip(self.integral, -1.0, 1.0)  # Anti-windup

        derivative = (error - self.last_error) / dt if dt > 0 else 0
        self.last_error = error

        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        return output


def main(args=None):
    rclpy.init(args=args)
    node = FlightControllerNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
