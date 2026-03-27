import pymysql
import json
import numpy as np
import pandas as pd

def processing_data() :
    config = {
        'host' : '172.22.80.1',
        'user' : 'root',
        'password' : '1234',
        'db' : 'auto_drive_db',
        'charset' : 'utf8mb4',
    }

    try :
        conn = pymysql.connect(**config)
        cursor = conn.cursor()

        sql = "select `ranges`, action from lidardata"
        cursor.execute(sql)
        rows = cursor.fetchall()

        if not rows : return None

        all_features = []
        for row in rows :
            lidar_list = json.loads(row[0])

            if len(lidar_list) != 360 :
                continue

            action = row[1]
            combined = lidar_list + [action]
            all_features.append(combined)
        
        dataset = np.array(all_features, dtype=object)
        file_name = 'robot_training_data.npy'
        np.save(file_name, data)

        return dataset
    
    except Exception as e :
        print(e)
        return None
    finally :
        if 'conn' in locals() :
            conn.close()

if __name__ == '__main__' :
    processing_data()