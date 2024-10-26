DROP TABLE IF EXISTS users;

CREATE TABLE users
(
    user_id TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    profile_picture blob
);
ALTER TABLE users DROP COLUMN profile_picture;

CREATE TABLE journals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_text TEXT NOT NULL,
    image BLOB
);
ALTER TABLE journals ADD COLUMN user_id INTEGER;

create table PLAN(
    premium TEXT,
    user_id TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    )

drop table if exists plan

SELECT *
from journals

insert into PLAN (premium)
values 
('yes')