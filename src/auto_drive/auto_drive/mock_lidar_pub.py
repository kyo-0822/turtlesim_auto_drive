import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import random
import math

ANGLE_MIN_DEG = 0
ANGLE_MAX_DEG = 359
ANGLE_INCREMENT_DEG = 1
NUM_POINTS = 360
RANGE_MIN = 0.12 # 미터
RANGE_MAX = 3.5 # 미터

# ㅡㅡㅡㅡ 모의 센서 데이터 생성 ㅡㅡㅡㅡ
class MockScanGenerator :
    def __init__(self) :
        self.ANGLE_MIN_DEG = 0
        self.ANGLE_MAX_DEG = 359
        self.ANGLE_INCREMENT_DEG = 1
        self.NUM_POINTS = 360
        self.RANGE_MIN = 0.12 # 미터
        self.RANGE_MAX = 3.5 # 미터
        self.AVAILABLE_PATTERNS = ["front_wall", "left_wall", "right_wall", "clear"]

    def create_empty_scan(self):
        ranges = [self.RANGE_MAX for _ in range(self.NUM_POINTS)]
        intensities = [100.0 for _ in range(self.NUM_POINTS)]
        scan = {
            "angle_min": math.radians(self.ANGLE_MIN_DEG),
            "angle_max": math.radians(self.ANGLE_MAX_DEG),
            "angle_increment": math.radians(self.ANGLE_INCREMENT_DEG),
            "range_min": self.RANGE_MIN,
            "range_max": self.RANGE_MAX,
            "ranges": ranges,
            "intensities": intensities
        }
        return scan

    def make_the_wall(self, ranges, center_deg, width_deg):
        half_width = width_deg // 2
        for offset in range(-half_width, half_width + 1):
            idx = (center_deg + offset) % self.NUM_POINTS
            ranges[idx] = 0.4

    def pattern_front_wall(self, scan):
        self.make_the_wall(scan["ranges"], center_deg=0, width_deg=40)

    def pattern_left_wall(self, scan):
        self.make_the_wall(scan["ranges"], center_deg=90, width_deg=30)

    def pattern_right_wall(self, scan):
        self.make_the_wall(scan["ranges"], center_deg=270, width_deg=30)

    def generate_single_scan(self):
        pattern_name = random.choice(self.AVAILABLE_PATTERNS)
        scan = self.create_empty_scan()

        if pattern_name == "front_wall":
            self.pattern_front_wall(scan)
        elif pattern_name == "left_wall":
            self.pattern_left_wall(scan)
        elif pattern_name == "right_wall":
            self.pattern_right_wall(scan)
        return scan, pattern_name

# ㅡㅡㅡㅡ 데이터 퍼블리시 ㅡㅡㅡㅡ
class MockLidarPub(Node) :
    def __init__(self) :
        super().__init__('mock_lidar_pub')
        self.generator = MockScanGenerator()

        self.publisher = self.create_publisher(LaserScan, '/mock_scan', 10)
        self.timer = self.create_timer(2.0, self.timer_callback)

    def timer_callback(self) :
        scan_dict, pattern_name = self.generator.generate_single_scan()

        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_scan'

        msg.angle_min = float(scan_dict["angle_min"])
        msg.angle_max = float(scan_dict["angle_max"])
        msg.angle_increment = float(scan_dict["angle_increment"])
        msg.range_min = float(scan_dict["range_min"])
        msg.range_max = float(scan_dict["range_max"])

        # 360으로 초기화
        msg.ranges = [float(r) for r in scan_dict["ranges"]]
        msg.intensities = [float(i) for i in scan_dict["intensities"]]

        self.publisher.publish(msg)

def main(args=None) :
    rclpy.init(args=args)
    node = MockLidarPub()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__' :
    main()