import roslibpy
import time
import random
import math

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


def main(args=None) :
    # 웹 소켓 연결
    ros = roslibpy.Ros(host='localhost', port=9090)
    ros.run()

    publisher = roslibpy.Topic(ros, '/mock_scan', 'sensor_msgs/LaserScan')
    generator = MockScanGenerator()

    try :
        while ros.is_connected:
            scan_dict, pattern_name = generator.generate_single_scan()

            msg = {
                'header': {
                    'frame_id' : 'base_scan'
                },
                'angle_min' : float(scan_dict["angle_min"]),
                'angle_max' : float(scan_dict["angle_max"]),
                'angle_increment' : float(scan_dict["angle_increment"]),
                'range_min' : float(scan_dict["range_min"]),
                'range_max' : float(scan_dict["range_max"]),
                'ranges' : [float(r) for r in scan_dict["ranges"]],
                'intensities' : [float(i) for i in scan_dict["intensities"]],
            }

            # 토픽 발행
            publisher.publish(roslibpy.Message(msg))
            time.sleep(2.0)
            
    except KeyboardInterrupt :
        pass
    finally :
        publisher.unadvertise()
        ros.terminate()

if __name__ == '__main__' :
    main()