#!/usr/bin/env python3
"""
Energy Manager Node - Manages battery, hydrogen fuel cell, solar, and electrolyzer.
Optimizes power distribution and predicts remaining flight time.
Frequency: 5 Hz (200ms updates)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String, Bool
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32MultiArray
import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple
from enum import Enum


class EnergyMode(Enum):
    """Power management modes"""
    NORMAL = 1
    EFFICIENT = 2
    EMERGENCY = 3


@dataclass
class PowerSystem:
    """Power system state"""
    name: str
    voltage: float  # Volts
    current: float  # Amps
    power: float  # Watts (= voltage * current)
    soc: float  # State of charge (0-1)
    capacity: float  # Wh or g for fuel
    available: bool = True
    max_power: float = 5000  # Max power in Watts


class EnergyManagerNode(Node):
    def __init__(self):
        super().__init__('energy_manager_node')

        # Power systems
        self.battery = PowerSystem(
            name='Solid-State Battery',
            voltage=400.0,  # 400V nominal
            current=0.0,
            power=0.0,
            soc=0.8,
            capacity=20000,  # 20 kWh
            max_power=20000  # 20 kW max
        )

        self.fuel_cell = PowerSystem(
            name='H2 Fuel Cell',
            voltage=48.0,  # Low voltage fuel cell
            current=0.0,
            power=0.0,
            soc=0.5,  # 50% H2 tank
            capacity=0.2,  # 200g H2
            max_power=3000  # 3 kW continuous
        )

        self.solar = PowerSystem(
            name='Solar Panels',
            voltage=48.0,
            current=0.0,
            power=0.0,
            soc=1.0,
            capacity=150,  # 150W at peak
            max_power=150
        )

        self.electrolyzer = PowerSystem(
            name='Electrolyzer',
            voltage=48.0,
            current=0.0,
            power=0.0,
            soc=1.0,  # Water tank level
            capacity=3.0,  # 3 liters water
            max_power=500  # 500W max
        )

        # Energy tracking
        self.total_power_consumed = 0.0  # Wh
        self.flight_start_time = None
        self.energy_mode = EnergyMode.NORMAL

        # Safety thresholds
        self.battery_warning_level = 0.3  # 30% alert
        self.battery_critical_level = 0.2  # 20% force descent
        self.battery_emergency_level = 0.15  # 15% emergency landing

        # Subscriptions
        self.motor_feedback_sub = self.create_subscription(
            Float32MultiArray, '/motor_status', self._motor_feedback_callback, 10
        )

        self.aux_power_sub = self.create_subscription(
            Float32, '/auxiliary_power', self._aux_power_callback, 10
        )

        self.state_sub = self.create_subscription(
            Twist, '/flight_status', self._flight_status_callback, 10
        )

        # Publishers
        self.energy_status_pub = self.create_publisher(Float32MultiArray, '/energy_status', 10)
        self.power_mode_pub = self.create_publisher(String, '/power_mode', 10)
        self.remaining_time_pub = self.create_publisher(Float32, '/remaining_flight_time', 10)
        self.battery_warning_pub = self.create_publisher(Bool, '/battery_warning', 10)
        self.fuel_cell_cmd_pub = self.create_publisher(Float32, '/fuel_cell_power_request', 10)
        self.electrolyzer_cmd_pub = self.create_publisher(Float32, '/electrolyzer_power_request', 10)

        # Timer for energy updates (5 Hz)
        self.timer = self.create_timer(0.2, self._energy_management_loop)

        # Power consumption estimates (Watts)
        self.power_consumption = {
            'motors': 0.0,  # Will be updated from feedback
            'computing': 74.0,  # Jetson Orin
            'cooling': 25.0,  # Liquid cooling
            'communications': 15.0,
            'joints': 8.0,
            'helmet': 20.0,
            'emergency': 5.0
        }

        self.get_logger().info('Energy Manager Node started')

    def _motor_feedback_callback(self, msg: Float32MultiArray):
        """Update motor power consumption"""
        # Expected: [pwm0...pwm7, current0...current7, ...]
        if len(msg.data) >= 16:
            motor_currents = msg.data[8:16]  # Second 8 values are currents
            # Approximate power: 400V * current
            self.power_consumption['motors'] = sum(motor_currents) * 400.0

    def _aux_power_callback(self, msg: Float32):
        """Update auxiliary power consumption"""
        # Sum of non-motor auxiliary systems
        self.power_consumption['auxiliary'] = msg.data

    def _flight_status_callback(self, msg: Twist):
        """Monitor flight intensity for power estimation"""
        # Current velocity indicates flight intensity
        velocity = np.linalg.norm([msg.linear.x, msg.linear.y, msg.linear.z])

        # Adjust power estimate based on velocity
        if velocity > 20.0:  # Fast flight
            self.power_consumption['motors'] = 15000.0
        elif velocity > 10.0:  # Normal flight
            self.power_consumption['motors'] = 12000.0
        else:  # Slow flight or hover
            self.power_consumption['motors'] = 8000.0

    def _energy_management_loop(self):
        """Main energy management loop - 5 Hz"""
        # Calculate total power consumption
        total_power = sum(self.power_consumption.values())

        # Update battery discharge
        dt = 0.2  # 200ms
        self.battery.current = total_power / self.battery.voltage
        self.battery.power = self.battery.voltage * self.battery.current

        # Energy consumed in this cycle
        energy_consumed = self.battery.power * dt / 3600  # Wh
        self.total_power_consumed += energy_consumed

        # Update battery SOC
        energy_available = self.battery.capacity * self.battery.soc
        energy_available -= energy_consumed
        self.battery.soc = max(0.0, energy_available / self.battery.capacity)

        # Solar charging (if available)
        solar_power = self._estimate_solar_power()
        self.solar.power = solar_power
        self.battery.power -= solar_power  # Solar reduces net power draw

        # Fuel cell management
        self._manage_fuel_cell()

        # Electrolyzer management
        self._manage_electrolyzer()

        # Determine energy mode
        self._determine_energy_mode()

        # Check battery warnings
        self._check_battery_warnings()

        # Publish status
        self._publish_energy_status()

    def _estimate_solar_power(self) -> float:
        """Estimate available solar power (simple model)"""
        # Assume panels facing up, variable due to weather
        # In production, would use actual weather data
        base_power = 100.0  # 100W baseline
        variation = 50.0 * np.sin(self.get_clock().now().nanoseconds / 1e9)  # Clouds
        solar_power = max(0.0, base_power + variation)
        return solar_power

    def _manage_fuel_cell(self):
        """Control fuel cell operation"""
        # Start fuel cell if battery low and have H2
        if self.battery.soc < 0.6 and self.fuel_cell.soc > 0.05:
            # Ramp up fuel cell
            self.fuel_cell.power = min(3000, 1000 + (0.6 - self.battery.soc) * 5000)
            self.fuel_cell.current = self.fuel_cell.power / self.fuel_cell.voltage

            # Fuel cell charges battery
            charge_power = min(self.fuel_cell.power, 2000)  # Limited charge rate
            self.battery.power -= charge_power

            # Update H2 consumption
            h2_consumption = self.fuel_cell.power * 0.2 / 3600  # g H2 per second
            self.fuel_cell.soc = max(0.0, (self.fuel_cell.capacity - h2_consumption) / self.fuel_cell.capacity)

            cmd_msg = Float32()
            cmd_msg.data = self.fuel_cell.power
            self.fuel_cell_cmd_pub.publish(cmd_msg)

        elif self.battery.soc > 0.8 or self.fuel_cell.soc < 0.02:
            # Shut down fuel cell
            self.fuel_cell.power = 0.0
            cmd_msg = Float32()
            cmd_msg.data = 0.0
            self.fuel_cell_cmd_pub.publish(cmd_msg)

    def _manage_electrolyzer(self):
        """Control electrolyzer for H2 production"""
        # Produce H2 when battery is full and weather is good
        if (self.battery.soc > 0.9 and self.solar.power > 80.0 and
            self.fuel_cell.soc < 0.8 and self.electrolyzer.soc > 0.2):

            electrolyzer_power = min(500, self.solar.power * 2)  # Use excess solar
            self.electrolyzer.power = electrolyzer_power

            # H2 production: ~0.00042 g/Wh
            h2_produced = electrolyzer_power * 0.00042 * 0.2 / 3600
            self.fuel_cell.soc = min(1.0, self.fuel_cell.soc + h2_produced / self.fuel_cell.capacity)

            # Water consumption
            water_consumed = h2_produced * 9  # 9:1 water to H2
            self.electrolyzer.soc = max(0.0, (self.electrolyzer.capacity - water_consumed) / self.electrolyzer.capacity)

            cmd_msg = Float32()
            cmd_msg.data = electrolyzer_power
            self.electrolyzer_cmd_pub.publish(cmd_msg)

        else:
            self.electrolyzer.power = 0.0
            cmd_msg = Float32()
            cmd_msg.data = 0.0
            self.electrolyzer_cmd_pub.publish(cmd_msg)

    def _determine_energy_mode(self):
        """Determine optimal energy mode"""
        if self.battery.soc < self.battery_emergency_level:
            self.energy_mode = EnergyMode.EMERGENCY
        elif self.battery.soc < self.battery_critical_level:
            self.energy_mode = EnergyMode.EMERGENCY
        elif self.battery.soc < self.battery_warning_level:
            self.energy_mode = EnergyMode.EFFICIENT
        else:
            self.energy_mode = EnergyMode.NORMAL

    def _check_battery_warnings(self):
        """Publish battery warnings"""
        warning = False

        if self.battery.soc < self.battery_warning_level:
            warning = True
            self.get_logger().warn(
                f'Battery low: {self.battery.soc * 100:.1f}% remaining'
            )

        if self.battery.soc < self.battery_critical_level:
            self.get_logger().error(
                f'BATTERY CRITICAL: {self.battery.soc * 100:.1f}% - INITIATE DESCENT'
            )

        warning_msg = Bool()
        warning_msg.data = warning
        self.battery_warning_pub.publish(warning_msg)

    def _publish_energy_status(self):
        """Publish comprehensive energy status"""
        status_msg = Float32MultiArray()

        status_msg.data = [
            self.battery.soc,
            self.battery.voltage,
            self.battery.current,
            self.battery.power,
            self.fuel_cell.soc,
            self.fuel_cell.power,
            self.solar.power,
            sum(self.power_consumption.values()),
            self._estimate_remaining_time(),
            float(self.energy_mode.value)
        ]

        self.energy_status_pub.publish(status_msg)

        # Publish mode string
        mode_msg = String()
        mode_msg.data = self.energy_mode.name

        self.power_mode_pub.publish(mode_msg)

        # Publish remaining flight time
        remaining_time = self._estimate_remaining_time()
        time_msg = Float32()
        time_msg.data = remaining_time
        self.remaining_time_pub.publish(time_msg)

    def _estimate_remaining_time(self) -> float:
        """Estimate remaining flight time in minutes"""
        current_power = sum(self.power_consumption.values())

        if current_power < 100:  # Not flying
            return 0.0

        # Energy available for flight
        available_wh = self.battery.capacity * self.battery.soc

        # Account for fuel cell
        if self.fuel_cell.soc > 0.05:
            available_wh += self.fuel_cell.capacity * 50000 * self.fuel_cell.soc  # 50 kWh per kg H2

        # Subtract reserve (15%)
        available_wh *= 0.85

        remaining_hours = available_wh / current_power
        remaining_minutes = remaining_hours * 60

        return remaining_minutes


def main(args=None):
    rclpy.init(args=args)
    node = EnergyManagerNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
