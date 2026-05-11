#!/usr/bin/env python3
"""
Route Planner Node - Plans autonomous routes using A* algorithm in 3D.
Manages waypoints, handles dynamic obstacle avoidance, and route optimization.
Frequency: 10 Hz (routes updated every 100ms)
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Pose, Point
from nav_msgs.msg import Path
from std_msgs.msg import String, Bool, Float32
from geometry_msgs.msg import Vector3, Polygon
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
import heapq
from math import sqrt


@dataclass
class Node:
    """A* node"""
    position: np.ndarray
    parent: Optional['Node'] = None
    g: float = 0.0  # Cost from start
    h: float = 0.0  # Heuristic cost to goal
    f: float = 0.0  # Total cost

    def __lt__(self, other):
        return self.f < other.f


@dataclass
class Waypoint:
    """Navigation waypoint"""
    position: np.ndarray
    speed_ms: float = 15.0  # m/s
    hold_time: float = 0.0  # seconds


class RoutePlannerNode(Node):
    def __init__(self):
        super().__init__('route_planner_node')

        # Route configuration
        self.current_position = np.array([0.0, 0.0, 0.0])
        self.current_destination = None
        self.waypoints: List[Waypoint] = []
        self.current_waypoint_idx = 0

        # A* grid parameters
        self.grid_resolution = 10.0  # meters per grid cell
        self.max_altitude = 500.0  # meters
        self.min_altitude = 50.0   # meters
        self.search_radius = 1000.0  # meters

        # Planning modes
        self.planning_mode = 'safe'  # safe, fast, efficient

        # Obstacle map (updated from obstacle_detection)
        self.obstacle_map: Dict[Tuple[int, int, int], float] = {}
        self.restricted_zones = []

        # Route optimization
        self.replan_distance_threshold = 20.0  # Replan if deviated >20m
        self.replan_timer_count = 0
        self.replan_interval = 10  # Replan every 100ms (at 10Hz)

        # Subscriptions
        self.pose_sub = self.create_subscription(
            PoseStamped, '/pose_estimate', self._pose_callback, 10
        )

        self.destination_sub = self.create_subscription(
            PoseStamped, '/goal_pose', self._destination_callback, 10
        )

        self.obstacles_sub = self.create_subscription(
            Polygon, '/detected_obstacles', self._obstacles_callback, 10
        )

        self.mode_sub = self.create_subscription(
            String, '/planning_mode', self._mode_callback, 10
        )

        # Publishers
        self.path_pub = self.create_publisher(Path, '/planned_path', 10)
        self.next_waypoint_pub = self.create_publisher(PoseStamped, '/next_waypoint', 10)
        self.route_status_pub = self.create_publisher(String, '/route_status', 10)

        # Timer for route update (10 Hz)
        self.timer = self.create_timer(0.1, self._route_update_loop)

        self.get_logger().info('Route Planner Node started')

    def _pose_callback(self, msg: PoseStamped):
        """Update current position"""
        self.current_position = np.array([
            msg.pose.position.x,
            msg.pose.position.y,
            msg.pose.position.z
        ])

    def _destination_callback(self, msg: PoseStamped):
        """Receive new destination and start planning"""
        destination = np.array([
            msg.pose.position.x,
            msg.pose.position.y,
            msg.pose.position.z
        ])

        self.current_destination = destination
        self.current_waypoint_idx = 0

        # Plan route
        self.waypoints = self._plan_route(self.current_position, destination)

        if self.waypoints:
            status_msg = String()
            status_msg.data = f'Route planned: {len(self.waypoints)} waypoints'
            self.route_status_pub.publish(status_msg)
            self.get_logger().info(f'Route planned with {len(self.waypoints)} waypoints')
        else:
            status_msg = String()
            status_msg.data = 'Route planning failed'
            self.route_status_pub.publish(status_msg)
            self.get_logger().error('Route planning failed')

    def _obstacles_callback(self, msg: Polygon):
        """Update obstacle map from detected obstacles"""
        # Clear old obstacles and update with new ones
        self.obstacle_map.clear()

        for point in msg.points:
            # Quantize to grid
            grid_x = int(point.x / self.grid_resolution)
            grid_y = int(point.y / self.grid_resolution)
            grid_z = int(point.z / self.grid_resolution)

            # Mark grid cell as obstacle
            self.obstacle_map[(grid_x, grid_y, grid_z)] = 1.0

            # Mark surrounding cells with reduced cost
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    for dz in range(-1, 2):
                        key = (grid_x + dx, grid_y + dy, grid_z + dz)
                        if key not in self.obstacle_map:
                            self.obstacle_map[key] = 0.5

    def _mode_callback(self, msg: String):
        """Change planning mode"""
        if msg.data in ['safe', 'fast', 'efficient']:
            self.planning_mode = msg.data
            self.get_logger().info(f'Planning mode changed to: {msg.data}')

    def _plan_route(self, start: np.ndarray, goal: np.ndarray) -> List[Waypoint]:
        """Plan route from start to goal using A*"""
        start_grid = self._pos_to_grid(start)
        goal_grid = self._pos_to_grid(goal)

        if self._is_blocked(goal_grid):
            self.get_logger().error('Goal position blocked by obstacle')
            return []

        # A* search
        open_set = [Node(position=start_grid, g=0, h=self._heuristic(start_grid, goal_grid))]
        open_set[0].f = open_set[0].h
        closed_set = set()
        came_from: Dict[Tuple, Optional[Node]] = {}

        iteration_count = 0
        max_iterations = 1000

        while open_set and iteration_count < max_iterations:
            iteration_count += 1

            # Pop node with lowest f score
            current = heapq.heappop(open_set)
            current_key = tuple(current.position)

            if current_key in closed_set:
                continue

            closed_set.add(current_key)

            # Check if goal reached
            if np.allclose(current.position, goal_grid, atol=1):
                return self._reconstruct_path(current, start, goal)

            # Expand neighbors
            for neighbor_pos in self._get_neighbors(current.position):
                neighbor_key = tuple(neighbor_pos)

                if neighbor_key in closed_set or self._is_blocked(neighbor_pos):
                    continue

                # Calculate costs
                g = current.g + np.linalg.norm(neighbor_pos - current.position)
                h = self._heuristic(neighbor_pos, goal_grid)
                f = g + h

                # Check if this is a new node or better path
                neighbor = Node(
                    position=neighbor_pos,
                    parent=current,
                    g=g,
                    h=h,
                    f=f
                )

                heapq.heappush(open_set, neighbor)
                came_from[neighbor_key] = current

        self.get_logger().warn(f'No path found after {iteration_count} iterations')
        return []

    def _reconstruct_path(
        self,
        final_node: Node,
        start: np.ndarray,
        goal: np.ndarray
    ) -> List[Waypoint]:
        """Reconstruct path from A* search"""
        waypoints = []
        node = final_node

        while node is not None:
            # Convert grid to position
            pos = self._grid_to_pos(node.position)
            waypoint = Waypoint(position=pos)

            # Assign speed based on mode
            if self.planning_mode == 'fast':
                waypoint.speed_ms = 25.0  # Max speed
            elif self.planning_mode == 'efficient':
                waypoint.speed_ms = 15.0  # Cruise speed
            else:  # safe
                waypoint.speed_ms = 12.0  # Conservative speed

            waypoints.insert(0, waypoint)
            node = node.parent

        # Add goal as final waypoint
        goal_waypoint = Waypoint(position=goal, speed_ms=0.0, hold_time=5.0)
        waypoints.append(goal_waypoint)

        return waypoints

    def _pos_to_grid(self, pos: np.ndarray) -> np.ndarray:
        """Convert world position to grid coordinates"""
        return np.round(pos / self.grid_resolution).astype(int)

    def _grid_to_pos(self, grid: np.ndarray) -> np.ndarray:
        """Convert grid coordinates to world position"""
        return grid.astype(float) * self.grid_resolution

    def _heuristic(self, current: np.ndarray, goal: np.ndarray) -> float:
        """Euclidean distance heuristic"""
        return np.linalg.norm(goal - current)

    def _get_neighbors(self, pos: np.ndarray) -> List[np.ndarray]:
        """Get valid neighboring grid cells (26-connected in 3D)"""
        neighbors = []

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    if dx == 0 and dy == 0 and dz == 0:
                        continue

                    neighbor = pos + np.array([dx, dy, dz])

                    # Check bounds
                    if (self.min_altitude <= neighbor[2] * self.grid_resolution <= self.max_altitude and
                        abs(neighbor[0]) * self.grid_resolution <= self.search_radius and
                        abs(neighbor[1]) * self.grid_resolution <= self.search_radius):
                        neighbors.append(neighbor)

        return neighbors

    def _is_blocked(self, grid_pos: np.ndarray) -> bool:
        """Check if grid cell is blocked by obstacle"""
        key = tuple(grid_pos)
        return self.obstacle_map.get(key, 0.0) >= 0.8

    def _route_update_loop(self):
        """Main route update loop - 10 Hz"""
        if not self.waypoints:
            return

        # Check if we need to replan
        self.replan_timer_count += 1
        if self.replan_timer_count >= self.replan_interval:
            self.replan_timer_count = 0

            # Check deviation from planned route
            if self.current_destination is not None:
                deviation = np.linalg.norm(
                    self.current_position - self.waypoints[self.current_waypoint_idx].position
                )

                if deviation > self.replan_distance_threshold:
                    self.get_logger().info('Replanning route due to deviation')
                    self.waypoints = self._plan_route(self.current_position, self.current_destination)

        # Publish current waypoint
        if self.current_waypoint_idx < len(self.waypoints):
            waypoint = self.waypoints[self.current_waypoint_idx]

            # Check if waypoint reached
            dist_to_waypoint = np.linalg.norm(
                self.current_position - waypoint.position
            )

            if dist_to_waypoint < 5.0:  # 5m tolerance
                self.current_waypoint_idx += 1
                if self.current_waypoint_idx >= len(self.waypoints):
                    status_msg = String()
                    status_msg.data = 'Route completed'
                    self.route_status_pub.publish(status_msg)
                    self.current_destination = None
                    return

            # Publish next waypoint
            next_wp = self.waypoints[self.current_waypoint_idx]
            wp_msg = PoseStamped()
            wp_msg.header.stamp = self.get_clock().now().to_msg()
            wp_msg.header.frame_id = 'world'
            wp_msg.pose.position.x = float(next_wp.position[0])
            wp_msg.pose.position.y = float(next_wp.position[1])
            wp_msg.pose.position.z = float(next_wp.position[2])
            wp_msg.pose.orientation.w = 1.0

            self.next_waypoint_pub.publish(wp_msg)

            # Publish full path
            path_msg = Path()
            path_msg.header.stamp = self.get_clock().now().to_msg()
            path_msg.header.frame_id = 'world'

            for wp in self.waypoints[self.current_waypoint_idx:]:
                pose = PoseStamped()
                pose.header = path_msg.header
                pose.pose.position.x = float(wp.position[0])
                pose.pose.position.y = float(wp.position[1])
                pose.pose.position.z = float(wp.position[2])
                pose.pose.orientation.w = 1.0
                path_msg.poses.append(pose)

            self.path_pub.publish(path_msg)


def main(args=None):
    rclpy.init(args=args)
    node = RoutePlannerNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
