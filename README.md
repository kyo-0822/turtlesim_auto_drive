## 프로젝트 개요
> 가상의 LiDAR 센서 데이터를 수집하여 시뮬레이션으로 확인, AI 학습을 위한 데이터셋(.npy)으로 변환하는 파이프라인

## Teck Stack
- **Language :** python 3.10
- **Framework :** ROS2 (humble), roslibpy (websocket)
- **Database :** MySQL
- **Library :** NumPy, PyMySQL

## 주요 기능
1. **Lidar Data Simulation :** 'mock_lidar_pub.py' - 360도 전 방향 거리 데이터를 토픽으로 발행
2. **Real_time control & Storage :** 'motion_controller.py' - 토픽을 구독해서 turtlesim 제어, 센서 값과 상태를 DB에 실시간 INSERT
3. **Data Preprocessing :** 'data_processing.py' - DB에 저장된 데이터를 딥러닝 학습용 NumPy 배열('.npy')로 변환

## 실행 방법

### 1. 환경 설정
```bash
pip install roslibpy pymysql numpy
#ROS2 Bridge 서버 실행 필수
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

### 2. 데이터 수집
``` bash
# 가상 LiDAR 데이터 토픽으로 발행
python3 -m auto_drive.mock_lidar_pub

# 컨트롤러 및 DB 저장 실행
python3 -m auto_drive.motion_controller
```

### 3. 학습 데이터 생성
``` bash
python3 data_processing.py
```

