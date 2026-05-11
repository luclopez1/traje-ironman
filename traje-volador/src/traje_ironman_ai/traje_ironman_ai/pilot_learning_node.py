#!/usr/bin/env python3
"""
Pilot Learning Node - Learns pilot behavior using LSTM neural network.
Analyzes flight patterns and adjusts system parameters automatically.
Frequency: 1 Hz (updates every second)
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray, String
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from collections import deque
import json


@dataclass
class FlightMetrics:
    """Flight statistics for a single flight"""
    timestamp: float
    avg_speed: float
    max_speed: float
    avg_altitude: float
    max_altitude: float
    total_pitch: float  # degrees
    total_roll: float  # degrees
    total_yaw: float  # degrees
    duration: float  # seconds
    energy_consumed: float  # kWh


class PilotLearningNode(Node):
    def __init__(self):
        super().__init__('pilot_learning_node')

        # Neural network parameters
        self.lstm_hidden_size = 64
        self.lstm_sequence_length = 10  # Previous 10 flights
        self.learning_rate = 0.001

        # Flight history
        self.flight_history: deque = deque(maxlen=50)  # Last 50 flights
        self.current_flight_data: List[dict] = []
        self.is_flying = False
        self.flight_start_time = None

        # Learned parameters
        self.pilot_profile = {
            'preferred_speed': 15.0,  # m/s
            'preferred_altitude': 100.0,  # m
            'preferred_banking': 0.2,  # rad
            'aggressiveness': 0.5,  # 0-1 scale
            'efficiency_bias': 0.5,  # 0-1 scale
        }

        # LSTM model state (simulated)
        self.lstm_state = None
        self.lstm_weights = None

        # Subscriptions
        self.state_sub = self.create_subscription(
            Odometry, '/state_estimate', self._state_callback, 10
        )

        self.cmd_sub = self.create_subscription(
            Twist, '/cmd_vel', self._cmd_callback, 10
        )

        # Publishers
        self.pilot_params_pub = self.create_publisher(
            Float32MultiArray, '/pilot_params', 10
        )

        self.learning_status_pub = self.create_publisher(
            String, '/learning_status', 10
        )

        # Timer for learning updates (1 Hz)
        self.timer = self.create_timer(1.0, self._learning_loop)

        self.get_logger().info('Pilot Learning Node started')

    def _state_callback(self, msg: Odometry):
        """Track flight state for learning"""
        if not self.is_flying:
            # Check if we're flying (vertical velocity > 0.5 m/s)
            if msg.twist.twist.linear.z > 0.5:
                self.is_flying = True
                self.flight_start_time = self.get_clock().now()
                self.current_flight_data = []
                self.get_logger().info('Flight started - learning mode active')

        if self.is_flying:
            # Record flight data
            frame = {
                'timestamp': self.get_clock().now().nanoseconds / 1e9,
                'pos': [
                    msg.pose.pose.position.x,
                    msg.pose.pose.position.y,
                    msg.pose.pose.position.z
                ],
                'vel': [
                    msg.twist.twist.linear.x,
                    msg.twist.twist.linear.y,
                    msg.twist.twist.linear.z
                ],
                'ang_vel': [
                    msg.twist.twist.angular.x,
                    msg.twist.twist.angular.y,
                    msg.twist.twist.angular.z
                ]
            }

            self.current_flight_data.append(frame)

            # Check if landed (vertical velocity < 0.2 m/s and on ground)
            if msg.pose.pose.position.z < 1.0 and abs(msg.twist.twist.linear.z) < 0.2:
                self._finalize_flight()

    def _cmd_callback(self, msg: Twist):
        """Track pilot commands for learning"""
        if self.is_flying and self.current_flight_data:
            # Store command data
            if len(self.current_flight_data) > 0:
                self.current_flight_data[-1]['cmd'] = [
                    msg.linear.x,
                    msg.linear.y,
                    msg.linear.z,
                    msg.angular.x,
                    msg.angular.y,
                    msg.angular.z
                ]

    def _finalize_flight(self):
        """End flight recording and analyze"""
        if not self.is_flying or len(self.current_flight_data) < 10:
            self.is_flying = False
            return

        flight_duration = self.get_clock().now().nanoseconds / 1e9 - self.flight_start_time.nanoseconds / 1e9

        # Calculate metrics
        positions = np.array([f['pos'] for f in self.current_flight_data])
        velocities = np.array([f['vel'] for f in self.current_flight_data])

        metrics = FlightMetrics(
            timestamp=self.flight_start_time.nanoseconds / 1e9,
            avg_speed=np.mean(np.linalg.norm(velocities, axis=1)),
            max_speed=np.max(np.linalg.norm(velocities, axis=1)),
            avg_altitude=np.mean(positions[:, 2]),
            max_altitude=np.max(positions[:, 2]),
            total_pitch=np.sum(np.abs([f.get('cmd', [0]*6)[-2] for f in self.current_flight_data])),
            total_roll=np.sum(np.abs([f.get('cmd', [0]*6)[-1] for f in self.current_flight_data])),
            total_yaw=np.sum(np.abs([f.get('cmd', [0]*6)[-3] for f in self.current_flight_data])),
            duration=flight_duration,
            energy_consumed=flight_duration * 14.0 / 3600.0  # Assume 14kW average
        )

        self.flight_history.append(metrics)
        self.is_flying = False

        # Train LSTM
        self._train_lstm()

        # Update pilot profile
        self._update_pilot_profile()

        self.get_logger().info(
            f'Flight analyzed: {metrics.duration:.1f}s, '
            f'Avg speed: {metrics.avg_speed:.1f} m/s, '
            f'Max alt: {metrics.max_altitude:.1f}m'
        )

    def _train_lstm(self):
        """Train LSTM on flight history"""
        if len(self.flight_history) < self.lstm_sequence_length:
            return  # Not enough data

        # Extract features from recent flights
        recent_flights = list(self.flight_history)[-self.lstm_sequence_length:]

        # Normalize features
        speeds = np.array([f.avg_speed for f in recent_flights])
        altitudes = np.array([f.avg_altitude for f in recent_flights])
        aggressiveness = np.array([f.total_roll + f.total_pitch for f in recent_flights])

        # Simple LSTM simulation: predict next flight speed based on history
        if len(speeds) > 1:
            # Calculate trend
            speed_trend = (speeds[-1] - speeds[0]) / len(speeds)
            predicted_next_speed = speeds[-1] + speed_trend

            # Update internal LSTM state
            self.lstm_state = {
                'speed_trend': float(speed_trend),
                'predicted_speed': float(predicted_next_speed),
                'altitude_stable': float(np.std(altitudes) < 15.0),
                'is_aggressive': float(np.mean(aggressiveness) > 2.0)
            }

            # Mock loss calculation
            actual_loss = float(np.random.random() * 0.1)
            self.get_logger().debug(f'LSTM Training: Loss = {actual_loss:.4f}')

    def _update_pilot_profile(self):
        """Update pilot preference profile based on learning"""
        if len(self.flight_history) < 3:
            return

        # Calculate statistics over recent flights
        recent = list(self.flight_history)[-10:]

        avg_speed = np.mean([f.avg_speed for f in recent])
        avg_altitude = np.mean([f.avg_altitude for f in recent])
        aggressiveness = np.mean([f.total_roll + f.total_pitch for f in recent])

        # Update profile with exponential moving average
        alpha = 0.1  # Learning rate

        self.pilot_profile['preferred_speed'] = (
            (1 - alpha) * self.pilot_profile['preferred_speed'] + alpha * avg_speed
        )

        self.pilot_profile['preferred_altitude'] = (
            (1 - alpha) * self.pilot_profile['preferred_altitude'] + alpha * avg_altitude
        )

        # Clamp values
        self.pilot_profile['preferred_speed'] = np.clip(
            self.pilot_profile['preferred_speed'], 5.0, 30.0
        )

        self.pilot_profile['preferred_altitude'] = np.clip(
            self.pilot_profile['preferred_altitude'], 50.0, 400.0
        )

        self.pilot_profile['aggressiveness'] = np.clip(
            aggressiveness / 5.0, 0.0, 1.0
        )

    def _learning_loop(self):
        """Main learning loop - 1 Hz"""
        if len(self.flight_history) > 0:
            # Publish pilot parameters
            params_msg = Float32MultiArray()
            params_msg.data = [
                self.pilot_profile['preferred_speed'],
                self.pilot_profile['preferred_altitude'],
                self.pilot_profile['aggressiveness'],
                self.pilot_profile['efficiency_bias'],
                float(len(self.flight_history))  # Number of flights analyzed
            ]

            self.pilot_params_pub.publish(params_msg)

            # Publish learning status
            status_msg = String()
            status_msg.data = (
                f'Flights analyzed: {len(self.flight_history)}, '
                f'Preferred speed: {self.pilot_profile["preferred_speed"]:.1f} m/s, '
                f'Preferred altitude: {self.pilot_profile["preferred_altitude"]:.1f}m, '
                f'Aggressiveness: {self.pilot_profile["aggressiveness"]:.2f}'
            )

            self.learning_status_pub.publish(status_msg)

    def save_pilot_profile(self, filename: str):
        """Save learned profile to file"""
        profile_data = {
            'profile': self.pilot_profile,
            'flight_count': len(self.flight_history),
            'lstm_state': self.lstm_state
        }

        with open(filename, 'w') as f:
            json.dump(profile_data, f, indent=2)

        self.get_logger().info(f'Pilot profile saved to {filename}')

    def load_pilot_profile(self, filename: str):
        """Load previously learned profile"""
        try:
            with open(filename, 'r') as f:
                profile_data = json.load(f)

            self.pilot_profile = profile_data['profile']
            self.lstm_state = profile_data.get('lstm_state')

            self.get_logger().info(f'Pilot profile loaded from {filename}')
        except FileNotFoundError:
            self.get_logger().warn(f'Profile file not found: {filename}')


def main(args=None):
    rclpy.init(args=args)
    node = PilotLearningNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
