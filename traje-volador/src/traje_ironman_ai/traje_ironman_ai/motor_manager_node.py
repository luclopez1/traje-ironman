#!/usr/bin/env python3
"""
Motor Manager Node - Distributes control commands to STM32 microcontrollers.
Handles PID loops for each EDF motor and RCS nozzle firing.
Frequency: 1000 Hz (1ms) for motor control via CAN bus
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Float32
from geometry_msgs.msg import Vector3
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class MotorState:
    """State of a single EDF motor"""
    motor_id: int
    target_pwm: float = 0.0
    current_pwm: float = 0.0
    current_rpm: float = 0.0
    current_amp: float = 0.0
    temperature_c: float = 25.0
    error_code: int = 0
    is_armed: bool = False


@dataclass
class RCSNozzle:
    """State of a single RCS nozzle"""
    nozzle_id: int
    is_firing: bool = False
    pulse_duration_ms: int = 0
    pressure_bar: float = 0.0


class MotorManagerNode(Node):
    def __init__(self):
        super().__init__('motor_manager_node')

        # Motor configuration
        self.num_edfs = 8
        self.num_rcs = 16

        # Motor states
        self.edf_motors: List[MotorState] = [
            MotorState(motor_id=i) for i in range(self.num_edfs)
        ]

        self.rcs_nozzles: List[RCSNozzle] = [
            RCSNozzle(nozzle_id=i) for i in range(self.num_rcs)
        ]

        # Motor parameters
        self.motor_min_pwm = 1000
        self.motor_max_pwm = 5000
        self.motor_max_rpm = 12000
        self.motor_max_temp = 85.0  # degrees C
        self.motor_max_amp = 80.0  # Amps per motor

        # Safety limits
        self.emergency_stop = False
        self.min_armed_thrust = 1200  # Minimum PWM to prevent damage
        self.max_voltage_sag = 0.95  # Allow 5% voltage sag

        # Subscriptions
        self.control_input_sub = self.create_subscription(
            Float32MultiArray, '/control_output', self._control_input_callback, 10
        )

        self.motor_feedback_sub = self.create_subscription(
            Float32MultiArray, '/motor_feedback', self._motor_feedback_callback, 10
        )

        # Publishers
        self.pwm_command_pub = self.create_publisher(Float32MultiArray, '/pwm_commands', 10)
        self.rcs_command_pub = self.create_publisher(Float32MultiArray, '/rcs_commands', 10)
        self.motor_status_pub = self.create_publisher(Float32MultiArray, '/motor_status', 10)

        # Timer for main loop (1000 Hz for real-time motor control)
        self.timer = self.create_timer(0.001, self._motor_control_loop)

        # Timer for slower diagnostics (10 Hz)
        self.diag_timer = self.create_timer(0.1, self._publish_diagnostics)

        self.get_logger().info('Motor Manager Node started')

    def _control_input_callback(self, msg: Float32MultiArray):
        """Receive control commands from flight controller"""
        if len(msg.data) != 24:  # 8 EDFs + 16 RCS
            self.get_logger().warn(f'Invalid control input size: {len(msg.data)}')
            return

        # Extract EDF commands (indices 0-7)
        for i in range(self.num_edfs):
            self.edf_motors[i].target_pwm = float(msg.data[i])

        # Extract RCS commands (indices 8-23)
        for i in range(self.num_rcs):
            self.rcs_nozzles[i].is_firing = bool(msg.data[8 + i])

    def _motor_feedback_callback(self, msg: Float32MultiArray):
        """Receive motor feedback from STM32 controllers"""
        # Expected format: [rpm0...rpm7, amp0...amp7, temp0...temp7, errors0...errors7]
        if len(msg.data) < 8 * 4:
            return

        offset = 0
        # RPM feedback
        for i in range(self.num_edfs):
            self.edf_motors[i].current_rpm = msg.data[offset + i]

        offset += self.num_edfs
        # Current feedback
        for i in range(self.num_edfs):
            self.edf_motors[i].current_amp = msg.data[offset + i]

        offset += self.num_edfs
        # Temperature feedback
        for i in range(self.num_edfs):
            self.edf_motors[i].temperature_c = msg.data[offset + i]

        offset += self.num_edfs
        # Error codes
        for i in range(self.num_edfs):
            self.edf_motors[i].error_code = int(msg.data[offset + i])

    def _motor_control_loop(self):
        """Main motor control loop - 1000 Hz"""
        if self.emergency_stop:
            self._handle_emergency_stop()
            return

        # Check motor safety limits
        self._check_motor_limits()

        # Apply PID control for each motor
        pwm_commands = np.zeros(self.num_edfs)
        for i, motor in enumerate(self.edf_motors):
            pwm_commands[i] = self._compute_motor_pid(motor)

        # Publish PWM commands to STM32
        self._publish_pwm_commands(pwm_commands)

        # Handle RCS nozzle firing
        self._handle_rcs_control()

    def _compute_motor_pid(self, motor: MotorState) -> float:
        """Compute PID correction for individual motor"""
        # Simple PID: compare target RPM vs current RPM
        target_rpm = self._pwm_to_rpm(motor.target_pwm)
        error_rpm = target_rpm - motor.current_rpm

        # PID parameters (tuned for EDF motors)
        Kp = 0.02
        Ki = 0.001
        Kd = 0.005

        # Mock PID (in production, would maintain state)
        pwm_correction = Kp * error_rpm * 0.01

        # Apply limits
        final_pwm = motor.target_pwm + pwm_correction
        final_pwm = np.clip(final_pwm, self.motor_min_pwm, self.motor_max_pwm)

        return final_pwm

    def _pwm_to_rpm(self, pwm: float) -> float:
        """Convert PWM value to expected RPM"""
        # Linear approximation: 1000 PWM = 0 RPM, 5000 PWM = 12000 RPM
        pwm_range = self.motor_max_pwm - self.motor_min_pwm
        pwm_norm = (pwm - self.motor_min_pwm) / pwm_range
        rpm = pwm_norm * self.motor_max_rpm
        return max(0, rpm)

    def _check_motor_limits(self):
        """Check for over-temperature, over-current, and other faults"""
        for motor in self.edf_motors:
            # Over-temperature protection
            if motor.temperature_c > self.motor_max_temp:
                self.get_logger().error(f'Motor {motor.motor_id} over-temperature: {motor.temperature_c}°C')
                motor.target_pwm = self.motor_min_pwm
                self.emergency_stop = True

            # Over-current protection
            if motor.current_amp > self.motor_max_amp:
                self.get_logger().error(f'Motor {motor.motor_id} over-current: {motor.current_amp}A')
                motor.target_pwm = self.motor_min_pwm
                self.emergency_stop = True

            # Motor error codes
            if motor.error_code != 0:
                self.get_logger().warn(f'Motor {motor.motor_id} error code: {motor.error_code}')

    def _handle_rcs_control(self):
        """Process RCS nozzle firing commands"""
        rcs_commands = np.zeros(self.num_rcs)

        for i, nozzle in enumerate(self.rcs_nozzles):
            if nozzle.is_firing:
                rcs_commands[i] = 1.0  # Fire signal
                nozzle.pulse_duration_ms = min(50, nozzle.pulse_duration_ms + 1)
            else:
                nozzle.pulse_duration_ms = max(0, nozzle.pulse_duration_ms - 1)

        # Publish RCS commands
        msg = Float32MultiArray()
        msg.data = rcs_commands.tolist()
        self.rcs_command_pub.publish(msg)

    def _publish_pwm_commands(self, pwm_commands: np.ndarray):
        """Publish PWM commands to STM32 controllers"""
        msg = Float32MultiArray()
        msg.data = pwm_commands.tolist()
        self.pwm_command_pub.publish(msg)

    def _publish_diagnostics(self):
        """Publish motor diagnostics"""
        status = []
        for motor in self.edf_motors:
            status.extend([
                motor.current_pwm,
                motor.current_rpm,
                motor.current_amp,
                motor.temperature_c
            ])

        msg = Float32MultiArray()
        msg.data = status
        self.motor_status_pub.publish(msg)

    def _handle_emergency_stop(self):
        """Safely shutdown all motors"""
        for motor in self.edf_motors:
            motor.target_pwm = 0.0

        pwm_commands = np.zeros(self.num_edfs)
        self._publish_pwm_commands(pwm_commands)

        # Disable RCS
        rcs_commands = np.zeros(self.num_rcs)
        msg = Float32MultiArray()
        msg.data = rcs_commands.tolist()
        self.rcs_command_pub.publish(msg)

        self.get_logger().fatal('EMERGENCY STOP ACTIVATED')


def main(args=None):
    rclpy.init(args=args)
    node = MotorManagerNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
