#!/usr/bin/env python3
"""
HUD Manager Node - Formats and displays flight data on the helmet HUD.
Real-time telemetry display with augmented reality overlays.
Frequency: 30 Hz (33ms updates for visual responsiveness)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32MultiArray, Bool
from geometry_msgs.msg import Twist, Vector3, Polygon, Point32
from nav_msgs.msg import Odometry, Path
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum


class HUDMode(Enum):
    """HUD display modes"""
    MANUAL = 1
    ASSISTED = 2
    AUTONOMOUS = 3


@dataclass
class HUDElement:
    """A HUD display element"""
    label: str
    value: str
    x_pos: float  # 0-1 normalized
    y_pos: float  # 0-1 normalized
    color: str  # hex color
    critical: bool = False
    warning: bool = False


class HUDManagerNode(Node):
    def __init__(self):
        super().__init__('hud_manager_node')

        # HUD configuration
        self.hud_mode = HUDMode.MANUAL
        self.hud_brightness = 0.8  # 0-1
        self.hud_contrast = 0.7
        self.ar_overlay_enabled = True

        # Flight data cache
        self.current_state = Odometry()
        self.energy_status = [0.8, 400, 0, 0, 0.5, 0, 100, 12000, 60, 1]
        self.pilot_status = 'CONSCIOUS'
        self.threat_vector = np.array([0.0, 0.0, 0.0])
        self.detected_obstacles: List[Tuple[float, float, float]] = []
        self.next_waypoint = None
        self.remaining_flight_time = 75.0  # minutes

        # HUD elements
        self.hud_elements: List[HUDElement] = []

        # Subscriptions
        self.state_sub = self.create_subscription(
            Odometry, '/state_estimate', self._state_callback, 10
        )

        self.energy_sub = self.create_subscription(
            Float32MultiArray, '/energy_status', self._energy_callback, 10
        )

        self.pilot_status_sub = self.create_subscription(
            String, '/pilot_status', self._pilot_status_callback, 10
        )

        self.threat_sub = self.create_subscription(
            Vector3, '/threat_vector', self._threat_callback, 10
        )

        self.obstacles_sub = self.create_subscription(
            Polygon, '/detected_obstacles', self._obstacles_callback, 10
        )

        self.next_waypoint_sub = self.create_subscription(
            Twist, '/next_waypoint', self._waypoint_callback, 10
        )

        self.mode_sub = self.create_subscription(
            String, '/power_mode', self._mode_callback, 10
        )

        self.remaining_time_sub = self.create_subscription(
            Float32MultiArray, '/remaining_flight_time', self._time_callback, 10
        )

        # Publishers
        self.hud_display_pub = self.create_publisher(String, '/hud_display', 10)
        self.hud_overlay_pub = self.create_publisher(Float32MultiArray, '/hud_overlay', 10)
        self.hud_warning_pub = self.create_publisher(String, '/hud_warning', 10)

        # Timer for HUD updates (30 Hz)
        self.timer = self.create_timer(1.0 / 30.0, self._hud_update_loop)

        self.get_logger().info('HUD Manager Node started')

    def _state_callback(self, msg: Odometry):
        """Update flight state"""
        self.current_state = msg

    def _energy_callback(self, msg: Float32MultiArray):
        """Update energy status"""
        if len(msg.data) >= 10:
            self.energy_status = msg.data

    def _pilot_status_callback(self, msg: String):
        """Update pilot status text"""
        self.pilot_status = msg.data

    def _threat_callback(self, msg: Vector3):
        """Update threat vector for obstacle avoidance display"""
        self.threat_vector = np.array([msg.x, msg.y, msg.z])

    def _obstacles_callback(self, msg: Polygon):
        """Update detected obstacles for AR display"""
        self.detected_obstacles = []
        for point in msg.points:
            self.detected_obstacles.append((point.x, point.y, point.z))

    def _waypoint_callback(self, msg: Twist):
        """Update next waypoint"""
        self.next_waypoint = np.array([msg.linear.x, msg.linear.y, msg.linear.z])

    def _mode_callback(self, msg: String):
        """Update power mode"""
        # Map power mode to HUD mode
        if 'EMERGENCY' in msg.data:
            self.hud_brightness = 1.0  # Brighten in emergency
            self.hud_contrast = 1.0

    def _time_callback(self, msg: Float32MultiArray):
        """Update remaining flight time"""
        if len(msg.data) > 0:
            self.remaining_flight_time = msg.data[0]

    def _hud_update_loop(self):
        """Main HUD update loop - 30 Hz"""
        # Clear previous elements
        self.hud_elements = []

        # Build HUD display
        self._build_flight_instruments()
        self._build_energy_display()
        self._build_navigation_display()
        self._build_threat_display()
        self._build_pilot_info()
        self._build_system_alerts()

        # Publish HUD content
        self._publish_hud_content()

    def _build_flight_instruments(self):
        """Primary flight instruments (top-left)"""
        # Altitude
        altitude = self.current_state.pose.pose.position.z
        alt_color = '#00FF00' if 50 < altitude < 500 else '#FFFF00'
        self.hud_elements.append(HUDElement(
            label='ALT', value=f'{altitude:.0f}m', x_pos=0.05, y_pos=0.1,
            color=alt_color
        ))

        # Vertical velocity
        v_z = self.current_state.twist.twist.linear.z
        v_color = '#00FF00' if abs(v_z) < 2.0 else '#FF6600'
        self.hud_elements.append(HUDElement(
            label='V/S', value=f'{v_z:+.2f}m/s', x_pos=0.05, y_pos=0.15,
            color=v_color
        ))

        # Ground speed
        v_xy = np.sqrt(
            self.current_state.twist.twist.linear.x**2 +
            self.current_state.twist.twist.linear.y**2
        )
        spd_color = '#00FF00' if v_xy < 30 else '#FF0000'
        self.hud_elements.append(HUDElement(
            label='SPD', value=f'{v_xy:.1f}m/s', x_pos=0.05, y_pos=0.2,
            color=spd_color
        ))

        # Heading
        qx = self.current_state.pose.pose.orientation.x
        qy = self.current_state.pose.pose.orientation.y
        qz = self.current_state.pose.pose.orientation.z
        qw = self.current_state.pose.pose.orientation.w

        yaw = np.arctan2(2*(qw*qz + qx*qy), 1 - 2*(qy**2 + qz**2))
        heading = np.degrees(yaw) % 360

        self.hud_elements.append(HUDElement(
            label='HDG', value=f'{heading:.0f}°', x_pos=0.05, y_pos=0.25,
            color='#00FF00'
        ))

    def _build_energy_display(self):
        """Energy status display (top-right)"""
        battery_soc = self.energy_status[0]
        fuel_soc = self.energy_status[4]
        remaining_time = self.energy_status[8]

        # Battery percentage
        battery_color = '#00FF00' if battery_soc > 0.3 else '#FF0000'
        self.hud_elements.append(HUDElement(
            label='BAT', value=f'{battery_soc*100:.0f}%', x_pos=0.85, y_pos=0.1,
            color=battery_color, critical=battery_soc < 0.15, warning=battery_soc < 0.3
        ))

        # Fuel cell status
        self.hud_elements.append(HUDElement(
            label='H2', value=f'{fuel_soc*100:.0f}%', x_pos=0.85, y_pos=0.15,
            color='#00FF00'
        ))

        # Remaining flight time
        time_color = '#00FF00' if remaining_time > 30 else '#FF0000'
        self.hud_elements.append(HUDElement(
            label='TIME', value=f'{remaining_time:.0f}m', x_pos=0.85, y_pos=0.2,
            color=time_color, critical=remaining_time < 10
        ))

        # Power mode
        power_mode = 'NORMAL'
        if battery_soc < 0.2:
            power_mode = 'EMERGENCY'
        elif battery_soc < 0.3:
            power_mode = 'EFFICIENT'

        power_color = '#FF0000' if power_mode == 'EMERGENCY' else '#00FF00'
        self.hud_elements.append(HUDElement(
            label='PWR', value=power_mode, x_pos=0.85, y_pos=0.25,
            color=power_color, critical=power_mode == 'EMERGENCY'
        ))

    def _build_navigation_display(self):
        """Navigation display (bottom)"""
        if self.next_waypoint is not None:
            # Distance to next waypoint
            wp_vec = self.next_waypoint - np.array([
                self.current_state.pose.pose.position.x,
                self.current_state.pose.pose.position.y,
                self.current_state.pose.pose.position.z
            ])
            wp_distance = np.linalg.norm(wp_vec)

            self.hud_elements.append(HUDElement(
                label='WP', value=f'{wp_distance:.0f}m', x_pos=0.5, y_pos=0.9,
                color='#00FFFF'
            ))

            # Course to waypoint
            if wp_distance > 1.0:
                wp_bearing = np.degrees(np.arctan2(wp_vec[1], wp_vec[0]))
                self.hud_elements.append(HUDElement(
                    label='CRS', value=f'{wp_bearing:.0f}°', x_pos=0.5, y_pos=0.95,
                    color='#00FFFF'
                ))

    def _build_threat_display(self):
        """Threat and obstacle display (center with AR)"""
        threat_magnitude = np.linalg.norm(self.threat_vector)

        if threat_magnitude > 0.1:
            threat_color = '#FF0000'
            threat_label = 'THREAT!'
        else:
            threat_color = '#00FF00'
            threat_label = 'CLEAR'

        self.hud_elements.append(HUDElement(
            label='THREAT', value=threat_label, x_pos=0.5, y_pos=0.45,
            color=threat_color, critical=threat_magnitude > 0.5
        ))

        # Display closest obstacle
        if len(self.detected_obstacles) > 0:
            closest = min(self.detected_obstacles, key=lambda x: np.linalg.norm(x))
            distance = np.linalg.norm(closest)

            obs_color = '#FF0000' if distance < 10 else '#FF9900'
            self.hud_elements.append(HUDElement(
                label='OBS', value=f'{distance:.0f}m', x_pos=0.5, y_pos=0.5,
                color=obs_color, warning=distance < 10
            ))

    def _build_pilot_info(self):
        """Pilot health and system status"""
        # Extract status from pilot_status string
        if 'CONSCIOUS' in self.pilot_status:
            pilot_color = '#00FF00'
        elif 'UNCONSCIOUS' in self.pilot_status:
            pilot_color = '#FF0000'
        else:
            pilot_color = '#FF9900'

        self.hud_elements.append(HUDElement(
            label='PILOT', value='OK' if 'CONSCIOUS' in self.pilot_status else 'ALERT',
            x_pos=0.05, y_pos=0.5, color=pilot_color
        ))

        # Vitals (from pilot_status string)
        if 'HR:' in self.pilot_status:
            # Parse HR value
            parts = self.pilot_status.split('HR:')
            if len(parts) > 1:
                hr_str = parts[1].split()[0]
                self.hud_elements.append(HUDElement(
                    label='HR', value=f'{hr_str}', x_pos=0.05, y_pos=0.55,
                    color='#00FF00'
                ))

    def _build_system_alerts(self):
        """Critical system alerts"""
        if self.energy_status[0] < 0.15:
            self.hud_elements.append(HUDElement(
                label='!!!', value='BATTERY CRITICAL', x_pos=0.5, y_pos=0.05,
                color='#FF0000', critical=True
            ))

        if len(self.detected_obstacles) > 0:
            closest = min(self.detected_obstacles, key=lambda x: np.linalg.norm(x))
            if np.linalg.norm(closest) < 5:
                self.hud_elements.append(HUDElement(
                    label='!!!', value='COLLISION WARNING', x_pos=0.5, y_pos=0.08,
                    color='#FF0000', critical=True
                ))

    def _publish_hud_content(self):
        """Publish HUD content for display"""
        # Create formatted HUD string
        hud_text = self._format_hud_display()

        hud_msg = String()
        hud_msg.data = hud_text
        self.hud_display_pub.publish(hud_msg)

        # Also publish as array for AR overlay coordinates
        overlay_data = []
        for elem in self.hud_elements:
            overlay_data.extend([elem.x_pos, elem.y_pos, len(elem.label)])

        if overlay_data:
            overlay_msg = Float32MultiArray()
            overlay_msg.data = overlay_data
            self.hud_overlay_pub.publish(overlay_msg)

    def _format_hud_display(self) -> str:
        """Format HUD elements into display string"""
        # Create simple text-based HUD representation
        lines = []

        # Header
        lines.append('╔════════════════════════════════════════╗')

        # Flight instruments (left column)
        lines.append(f'║ ALT  {self.current_state.pose.pose.position.z:>6.0f}m              ║')
        lines.append(f'║ SPD  {np.sqrt(self.current_state.twist.twist.linear.x**2 + self.current_state.twist.twist.linear.y**2):>6.1f}m/s            ║')

        # Energy (right column)
        battery = self.energy_status[0] * 100
        lines.append(f'║ BAT  {battery:>5.0f}%              ║')

        # Center: threat/navigation
        lines.append('║                                        ║')
        lines.append('║       CLEAR - PROCEED                  ║')
        lines.append('║                                        ║')

        # Warnings if any
        critical_alerts = [e for e in self.hud_elements if e.critical]
        if critical_alerts:
            lines.append('║ ⚠️  CRITICAL ALERTS:')
            for alert in critical_alerts:
                lines.append(f'║   {alert.label}: {alert.value}')

        lines.append('╚════════════════════════════════════════╝')

        return '\n'.join(lines)


def main(args=None):
    rclpy.init(args=args)
    node = HUDManagerNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
