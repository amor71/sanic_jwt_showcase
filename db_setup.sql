CREATE TABLE IF NOT EXISTS users(
  user_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL,
  email TEXT,
  name TEXT,
  scopes TEXT NOT NULL,
  hashed_password TEXT NOT NULL,
  create_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expire_date TIMESTAMP,
  modify_user_id INT REFERENCES users(modify_user_id),
  modified_at TIMESTAMP

);
CREATE INDEX IF NOT EXISTS users_idx ON users (username, expire_date);

CREATE TABLE IF NOT EXISTS jogging_results(
  result_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  user_id INT NOT NULL REFERENCES users(user_id),
  running_distance INT NOT NULL,
  date TEXT NOT NULL,
  time INTEGER NOT NULL,
  location TEXT NOT NULL,
  condition TEXT NOT NULL,
  week_number INTEGER NOT NULL,
  year INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expire_at TIMESTAMP,
  modify_user_id INT REFERENCES users(modify_user_id),
  modified_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS jogging_results_idx ON jogging_results (week_number, year);


