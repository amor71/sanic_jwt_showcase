CREATE TABLE IF NOT EXISTS roles(
  role_id INT NOT NULL PRIMARY KEY,
  description TEXT NOT NULL
);

insert into roles (role_id, description) values (1, "user");
insert into roles (role_id, description) values (10, "user manager");
insert into roles (role_id, description) values (100, "user manager");

CREATE TABLE IF NOT EXISTS users(
  user_id INT NOT NULL PRIMARY KEY,
  email TEXT NOT NULL,
  roll_id INT DEFAULT 1 REFERENCES roles(role_id),
  hashed_password TEXT NOT NULL,
  create_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expire_date TIMESTAMP
);
CREATE INDEX IF NOT EXISTS users_idx ON users (email, expire_date);

CREATE TABLE IF NOT EXISTS jogging_results(
  result_id INT NOT NULL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(user_id),
  running_distance INT NOT NULL,
  date TEXT NOT NULL,
  time INTEGER NOT NULL,
  location TEXT NOT NULL,
  condition TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expire_at TIMESTAMP,
  modify_user_id INT REFERENCES users(modify_user_id),
  modified_at TIMESTAMP
);


