import rclpy
import numpy as np
import json

from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from datetime import datetime
from auto_drive.connect_mysql import connect_mysql


class  MotionController(Node) :
    def __init__(self) :
        super().__init__('motion_controller')
        self.conn = None
        self.cursor = None
        self.setup_db()

        self.subscription = self.create_subscription(LaserScan, '/mock_scan', self.scan_callback, 10)
        self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        self.current_linear_v = 0.0
        self.current_angular_v = 0.0
        self.target_linear = 0.0
        self.target_angular = 0.0

        self.smooth_factor = 0.1
        self.timer = self.create_timer(0.1, self.control_loop)

    def setup_db(self) :
        self.conn = connect_mysql()
        if self.conn:
            self.cursor = self.conn.cursor()
            self.get_logger().info('DB 연결 성공')
        else :
            self.get_logger().info('DB 연결 실패')

    def save_db(self, ranges, action) :
        if self.conn is None or not self.conn.open :
            self.get_logger().info('DB 연결 끊김')
            self.setup_db()

            if self.conn is None :
                return

        try :
            sql = "insert into lidardata (`ranges`, `when`, action) values (%s, %s, %s)"
            json_ranges = json.dumps(list(ranges))
            self.cursor.execute(sql, (json_ranges, datetime.now(), action))
            self.conn.commit()
        except Exception as e :
            self.get_logger().warn(f'DB 저장 실패 : {e}')


    def scan_filter (self, ranges, start, end) :
        max_idx = len(ranges)
        if max_idx == 0 : return 3.5

        s = max(0, min(start, max_idx))
        e = max(0, min(end, max_idx))

        data_slice = ranges[s:e]
        valid_data = [i for i in data_slice if 0.12 < i < 3.5]

        return sum(valid_data) / len(valid_data) if valid_data else 3.5
    

    def control_loop(self) :
        self.current_linear_v = (self.current_linear_v * (1 - self.smooth_factor)) + (self.target_linear * self.smooth_factor)
        self.current_angular_v = (self.current_angular_v * (1 - self.smooth_factor)) + (self.target_angular * self.smooth_factor)

        twist_msg = Twist()
        twist_msg.linear.x = self.current_linear_v
        twist_msg.angular.z = self.current_angular_v
        self.publisher.publish(twist_msg)


    def scan_callback(self, msg) :
        front_left = self.scan_filter(msg.ranges, 345, 360)
        front_right = self.scan_filter(msg.ranges, 0, 15)
        front_dist = (front_left + front_right) / 2

        left_dist = self.scan_filter(msg.ranges, 15 , 90)
        right_dist = self.scan_filter(msg.ranges, 270, 345)

        force_left = 0.0 if left_dist > 2.5 else (1.0 / left_dist)
        force_right = 0.0 if right_dist > 2.5 else (1.0 / right_dist)
        angle_force = force_right - force_left

        action = 'STRAIGHT'

        if front_dist < 2.0 :
            self.target_linear = max(0.2, front_dist*0.5)

            if abs(angle_force) < 0.1 :
                if left_dist >= right_dist :
                    angle_force = 1.5
                    action = 'TURN_LEFT'
                else :
                    angle_force = -1.5
                    action = 'TURN_RIGHT'
            else :
                angle_force *= 2.0
                action = 'AVOIDING'
        else:
            self.target_linear = 1.0

        self.target_angular = max(-2.0, min(2.0, angle_force))
        self.save_db(msg.ranges, action)


def main(args=None) :
    rclpy.init(args=args)
    node = MotionController()

    try :
        rclpy.spin(node)
    except KeyboardInterrupt :
        pass
    finally :
        stop_msg = Twist()
        node.publisher.publish(stop_msg)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__' :
    main()