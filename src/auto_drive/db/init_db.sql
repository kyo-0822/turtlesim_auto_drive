create Database if not exists auto_drive_db;
use auto_drive_db;

create table if not exists lidardata (
    id int auto_increment primary key,
    `ranges` JSON not null,
    `when` datetime default current_timestamp,
    action varchar(20) not null
);

CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED WITH mysql_native_password BY '1234';
ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '1234';

GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
