import roslibpy
import time
import numpy as np
import json
import threading
from datetime import datetime
from auto_drive.connect_mysql import connect_mysql


class  MotionController :
    def __init__(self, ros) :
        self.ros = ros
        self.conn = None
        self.cursor = None
        self.setup_db()

        # turtlesim으로 msg 전달
        self.publisher = roslibpy.Topic(self.ros, '/turtle1/cmd_vel', 'geometry_msgs/Twist')

        # 모의 센서 데이터 구독
        self.subscription = roslibpy.Topic(self.ros, '/mock_scan', 'sensor_msgs/LaserScan')
        self.subscription.subscribe(self.scan_callback)
        
        self.current_linear_v = 0.0
        self.current_angular_v = 0.0
        self.target_linear = 0.0
        self.target_angular = 0.0
        self.smooth_factor = 0.1

        self.running = True
        self.timer_thread = threading.Thread(target=self.control_loop)
        self.timer_thread.start()

    def setup_db(self) : # db 연결
        self.conn = connect_mysql()
        if self.conn:
            self.cursor = self.conn.cursor()
            print('DB 연결 성공')
        else :
            print('DB 연결 실패')

    def save_db(self, ranges, action) : # db에 데이터 저장
        if self.conn is None or not self.conn.open :
            print('DB 연결 끊김')
            self.setup_db()

            if self.conn is None :
                return

        try :
            sql = "insert into lidardata (`ranges`, `when`, action) values (%s, %s, %s)"
            json_ranges = json.dumps(list(ranges))
            self.cursor.execute(sql, (json_ranges, datetime.now(), action))
            self.conn.commit()

        except Exception as e :
            print(f'DB 저장 실패 : {e}')


    def scan_filter (self, ranges, start, end) : # 센서 노이즈 데이터 전처리 
        max_idx = len(ranges)

        if max_idx == 0 :
            return 3.5

        s = max(0, min(start, max_idx))
        e = max(0, min(end, max_idx))

        data_slice = ranges[s:e]
        valid_data = [i for i in data_slice if 0.12 < i < 3.5]

        return sum(valid_data) / len(valid_data) if valid_data else 3.5
    

    def control_loop(self) :
        while self.running and self.ros.is_connected :
            self.current_linear_v = (self.current_linear_v * (1 - self.smooth_factor)) + (self.target_linear * self.smooth_factor)
            self.current_angular_v = (self.current_angular_v * (1 - self.smooth_factor)) + (self.target_angular * self.smooth_factor)

            twist_msg = {
                'linear' : {'x': self.current_linear_v, 'y': 0.0, 'z': 0.0},
                'angular' : {'x': 0.0, 'y': 0.0, 'z': self.current_angular_v}
            }
            self.publisher.publish(roslibpy.Message(twist_msg))
            time.sleep(0.1)


    def scan_callback(self, msg) :
        ranges = msg.get('ranges', [])

        if not ranges or len(ranges) != 360 :
            return
        
        front_left = self.scan_filter(ranges, 345, 360)
        front_right = self.scan_filter(ranges, 0, 15)
        front_dist = (front_left + front_right) / 2

        left_dist = self.scan_filter(ranges, 15 , 90)
        right_dist = self.scan_filter(ranges, 270, 345)

        # 빈 공간 찾기
        force_left = 0.0 if left_dist > 2.5 else (1.0 / left_dist)
        force_right = 0.0 if right_dist > 2.5 else (1.0 / right_dist)

        # 해당 방향 가중치
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
        self.save_db(ranges, action)
    
    
    def shutdown(self) :
        self.running = False
        self.timer_thread.join()

        stop_msg = {
            'linear' : {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'angular' : {'x': 0.0, 'y': 0.0, 'z': 0.0}
        }
        self.publisher.publish(roslibpy.Message(stop_msg))
        self.subscription.unsubscribe()
        self.publisher.unadvertise()


def main(args=None) :
    ros = roslibpy.Ros(host='localhost', port=9090)
    ros.run()

    controller = MotionController(ros)

    try :
        while ros.is_connected :
            time.sleep(1)
    except KeyboardInterrupt :
        pass
    finally :
        controller.shutdown()
        ros.terminate()

if __name__ == '__main__' :
    main()