import pymysql

def connect_mysql() :
        try :
            conn = pymysql.connect(
                host='172.22.80.1',
                user='root',
                password='1234',
                db='auto_drive_db',
                charset='utf8'
            )
            return conn
        
        except Exception as e:
            print(f'DB 연결 실패 {e}')
            conn = None