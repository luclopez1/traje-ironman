#!/usr/bin/env python3
"""
Obstacle Detection Node - Real-time object detection using YOLO v8.
Processes 4 camera feeds and detects obstacles within 50m radius.
Frequency: 30 Hz (assumes 60fps camera downsampled to 30Hz)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Polygon, Point32, Vector3
from std_msgs.msg import Float32MultiArray
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple
import cv2
from cv_bridge import CvBridge


@dataclass
class DetectedObstacle:
    """Detected obstacle in 3D space"""
    label: str
    confidence: float
    bbox_2d: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    center_3d: np.ndarray  # [x, y, z] in meters
    distance: float  # meters from suit
    camera_id: int  # which camera detected it


class ObstacleDetectionNode(Node):
    def __init__(self):
        super().__init__('obstacle_detection_node')

        # YOLO model simulation (in production, load actual YOLO v8)
        self.device = 'cpu'  # Should use 'cuda' if available
        self.confidence_threshold = 0.5
        self.iou_threshold = 0.45

        # Camera calibration parameters
        self.camera_fov = np.radians(90)  # 90° field of view
        self.camera_height_offset = 0.15  # Helmet camera 15cm above center

        # Obstacle tracking
        self.detected_obstacles: List[DetectedObstacle] = []
        self.threat_distance = 10.0  # Alert if obstacle < 10m

        # Subscriptions for 4 cameras
        self.cam_subscriptions = []
        for i in range(4):
            sub = self.create_subscription(
                Image, f'/camera{i}/image_raw', self._camera_callback, 10
            )
            self.cam_subscriptions.append(sub)

        # Publishers
        self.obstacles_pub = self.create_publisher(Polygon, '/detected_obstacles', 10)
        self.threat_pub = self.create_publisher(Vector3, '/threat_vector', 10)
        self.debug_image_pub = self.create_publisher(Image, '/obstacle_detection_debug', 10)

        # Timer for detection pipeline
        self.timer = self.create_timer(1.0 / 30.0, self._detection_loop)  # 30 Hz

        self.cv_bridge = CvBridge()
        self.camera_frames = {}

        self.get_logger().info('Obstacle Detection Node started')

    def _camera_callback(self, msg: Image):
        """Receive and store camera frame"""
        # Extract camera ID from topic
        # Parse '/camera{i}/image_raw' → i
        parts = msg.header.frame_id.split('_')
        if len(parts) > 0:
            try:
                camera_id = int(parts[-1])
                self.camera_frames[camera_id] = msg
            except:
                pass

    def _detection_loop(self):
        """Main detection loop - 30 Hz"""
        self.detected_obstacles = []

        # Process each camera
        for camera_id in range(4):
            if camera_id not in self.camera_frames:
                continue

            frame_msg = self.camera_frames[camera_id]
            try:
                frame = self.cv_bridge.imgmsg_to_cv2(frame_msg, 'bgr8')
            except:
                self.get_logger().warn(f'Failed to convert camera {camera_id} image')
                continue

            # Run YOLO detection
            detections = self._run_yolo_inference(frame, camera_id)
            self.detected_obstacles.extend(detections)

        # Analyze threats and publish
        self._analyze_and_publish_threats()

    def _run_yolo_inference(self, frame: np.ndarray, camera_id: int) -> List[DetectedObstacle]:
        """Run YOLO v8 inference on frame"""
        detections = []

        # Resize frame for faster processing
        frame_h, frame_w = frame.shape[:2]
        inference_size = 640
        scale = inference_size / max(frame_h, frame_w)
        resized_frame = cv2.resize(frame, None, fx=scale, fy=scale)

        # Mock YOLO inference (in production, use actual YOLO model)
        # This simulates detecting different obstacle types
        detected_boxes = self._mock_yolo_detection(resized_frame)

        for box_info in detected_boxes:
            x1, y1, x2, y2, label, confidence = box_info

            # Scale back to original coordinates
            x1, y1, x2, y2 = [int(v / scale) for v in [x1, y1, x2, y2]]

            if confidence < self.confidence_threshold:
                continue

            # Convert 2D detection to 3D position estimate
            center_3d = self._2d_to_3d_position(
                frame_h, frame_w, x1, y1, x2, y2, camera_id
            )

            distance = np.linalg.norm(center_3d)

            if distance < 50.0:  # Only track obstacles within 50m
                obstacle = DetectedObstacle(
                    label=label,
                    confidence=confidence,
                    bbox_2d=(x1, y1, x2, y2),
                    center_3d=center_3d,
                    distance=distance,
                    camera_id=camera_id
                )
                detections.append(obstacle)

                # Draw detection on frame for debugging
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f'{label} {confidence:.2f} {distance:.1f}m',
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )

        # Publish debug image
        debug_msg = self.cv_bridge.cv2_to_imgmsg(frame, 'bgr8')
        debug_msg.header.frame_id = f'camera_{camera_id}_debug'
        self.debug_image_pub.publish(debug_msg)

        return detections

    def _mock_yolo_detection(self, frame: np.ndarray) -> List[tuple]:
        """Mock YOLO detection for simulation"""
        h, w = frame.shape[:2]
        detections = []

        # Simulate detecting buildings, trees, people, etc.
        # In production, this would be replaced with actual YOLO inference

        # Detect high-contrast regions as potential obstacles
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours[:5]:  # Limit to 5 detections per frame
            x, y, bw, bh = cv2.boundingRect(contour)
            if bw > 20 and bh > 20:  # Minimum size
                label = 'obstacle'
                confidence = 0.6 + np.random.random() * 0.3
                detections.append((x, y, x + bw, y + bh, label, confidence))

        return detections

    def _2d_to_3d_position(
        self,
        frame_h: int,
        frame_w: int,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        camera_id: int
    ) -> np.ndarray:
        """Estimate 3D position from 2D bounding box"""
        # Camera positions relative to suit center
        camera_positions = [
            np.array([0.0, 0.0, 0.2]),      # Front
            np.array([0.0, 0.15, 0.0]),     # Right
            np.array([0.0, -0.15, 0.0]),    # Left
            np.array([0.0, 0.0, -0.2])      # Rear
        ]

        camera_orientations = [
            (0, 0, 0),      # Front: looking forward
            (-90, 0, 0),    # Right: looking right
            (90, 0, 0),     # Left: looking left
            (180, 0, 0)     # Rear: looking backward
        ]

        # Get camera position and orientation
        camera_pos = camera_positions[min(camera_id, 3)]
        camera_yaw = camera_orientations[min(camera_id, 3)][0]

        # Object bounding box center in image
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        bbox_height = y2 - y1

        # Estimate distance based on object size (simple heuristic)
        # Assume standard obstacle height of ~2 meters
        assumed_height = 2.0
        focal_length = frame_h / (2 * np.tan(self.camera_fov / 2))
        distance = (assumed_height * focal_length) / bbox_height if bbox_height > 0 else 10.0

        # Convert image coordinates to 3D
        # Normalize to [-1, 1]
        u = (cx - frame_w / 2) / (frame_w / 2)
        v = (cy - frame_h / 2) / (frame_h / 2)

        # Ray direction in camera frame
        ray_x = u * distance * np.tan(self.camera_fov / 2)
        ray_y = v * distance * np.tan(self.camera_fov / 2)
        ray_z = distance

        # Apply camera rotation
        yaw_rad = np.radians(camera_yaw)
        rotated_x = ray_x * np.cos(yaw_rad) - ray_z * np.sin(yaw_rad)
        rotated_z = ray_x * np.sin(yaw_rad) + ray_z * np.cos(yaw_rad)

        # Final position relative to suit center
        pos_3d = camera_pos + np.array([rotated_x, ray_y, rotated_z])

        return pos_3d

    def _analyze_and_publish_threats(self):
        """Analyze detected obstacles and publish threat vectors"""
        if not self.detected_obstacles:
            return

        # Find closest obstacle
        closest = min(self.detected_obstacles, key=lambda x: x.distance)

        if closest.distance < self.threat_distance:
            # Generate evasive maneuver vector
            threat_dir = -closest.center_3d / (closest.distance + 0.1)
            evasive_mag = max(0.0, (self.threat_distance - closest.distance) / self.threat_distance)

            threat_msg = Vector3()
            threat_msg.x = float(threat_dir[0] * evasive_mag)
            threat_msg.y = float(threat_dir[1] * evasive_mag)
            threat_msg.z = float(threat_dir[2] * evasive_mag)

            self.threat_pub.publish(threat_msg)

            self.get_logger().warn(
                f'THREAT DETECTED: {closest.label} at {closest.distance:.1f}m'
            )

        # Publish all detected obstacles
        polygon_msg = Polygon()
        for obstacle in self.detected_obstacles:
            pt = Point32()
            pt.x = float(obstacle.center_3d[0])
            pt.y = float(obstacle.center_3d[1])
            pt.z = float(obstacle.center_3d[2])
            polygon_msg.points.append(pt)

        self.obstacles_pub.publish(polygon_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleDetectionNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
