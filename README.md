## "Jogging Results"
###### v0.1 Jun 2019 by Amichay Oren

### Requirements Summary

**RESTful API that tracks jogging times of users**

* API Users must be able to create an account and log in.
* All API calls must be authenticated.
* Implement at least three roles with different permission levels: a regular user would only be able to CRUD on their owned records, a user manager would be able to CRUD only users, and an admin would be able to CRUD all records and users.
* Each time entry when entered has a date, distance, time, and location.
* Based on the provided date and location, API should connect to a weather API provider and get the weather conditions for the run, and store that with each run.
* The API must create a report on average speed & distance per week.
* The API must be able to return data in the JSON format.
* The API should provide filter capabilities for all endpoints that return a list of elements, as well should be able to support pagination.
* The API filtering should allow using parenthesis for defining operations precedence and use any combination of the available fields. The supported operations should at least include or, and, eq (equals), ne (not equals), gt (greater than), lt (lower than).
* Example -> (date eq '2016-05-01') AND ((distance gt 20) OR (distance lt 10)).

### Assumptions
 * Out-of-scope: back-office for setting user roles (set on DB level). For unit testing purposes an end-point for setting user role was implemented.
 * Jogging specific API are user-specific, and results can not be pulled or *managed* by user-managers or admins.
 * Filtering API required for jogging results only. 
 * Authentication is based on JWT, with _refresh_token_ using best practices defined in https://jwt.io/.
 * User roles are implemented as JWT _scopes_.
 * Implementation assumes running REDIS as in-memory storage for refresh_tokens.
 * JWT out-of-scope: refresh_token rotation, access_token blacklisting, logout, access_token refresh on scope changes.
 * If weather conditions can not be pulled for location and date of run, the jog is not recorded. 
 
### Design

* Sanic (https://sanic.readthedocs.io/en/latest/) has been chosen as a web-server and framework.
* Sanic_jwt (https://sanic-jwt.readthedocs.io/en/v1.3.2/) has been chosen for JWT implementation. **Disclaimer:** I'm a contributor in that project.
* SQLite3 (https://www.sqlite.org/index.html) has been chosen as a database, REDIS (https://redis.io/) was chosen as in-memory storage for refrsh_tokens.
* Two DB tables were implemented, _users_ tables for storing users, _jogging_results_ for stroing jogging results. Relevant indexes were added.

##### users table

  - user_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT 
  - username TEXT NOT NULL,
  - email TEXT,
  - name TEXT,
  - scopes TEXT NOT NULL,
  - hashed_password TEXT NOT NULL,
  - create_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  - expire_date TIMESTAMP,
  - modify_user_id INT REFERENCES users(modify_user_id),
  - modified_at TIMESTAMP
  
 user_id is the primary key (autoincrement is not ideal, but for the sake of this implementation its fine). 
  username (mandatory) , email (optional) & name (optional) field are can we added during registration, and can be edited later on. 
  hash_passwords holds the **bcrypted**. Each user has a create date, and if modified, the last modification date is stored during update, as well as the identify of the updating user.
  Each user has it's own JWT scope which is stored in the DB. expire_date holds the expiration time of a user - instead of deleting a user. 
  A user may delete (=expire) itself, managers and admins may expire other users. 
  Once a user is expired, it can take no further actions, even if the user was already authenticated and has a valid token.
  
 ##### jogging_results table
 
  - result_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  - user_id INT NOT NULL REFERENCES users(user_id),
  - running_distance INT NOT NULL,
  - date TEXT NOT NULL,
  - time INTEGER NOT NULL,
  - location TEXT NOT NULL,
  - condition TEXT NOT NULL,
  - week_number INTEGER NOT NULL,
  - year INTEGER NOT NULL,
  - created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

Each jogging results has a result_id, attached to a user_id (which is forigen key to the users table).
running_distance holds the jogging distance, date is when the job took place (not timestamp).
time holds the job time and location is the lat & long for jog location. 
condition holds json with the conditions at the time of the jog, 
and week_number and year are calculated during insert (or update) for reporting purposes.

### Weather API

In order to pull past and future weather conditions, Dark Sky API (https://darksky.net/dev) has been selected. 
The service returns elaborates weather conditions, in JSON format, globally either as forecast for future, or based on past history.

### Project Structure & Setup


```
- Connectors/ 
   (interfacing 3rd party APIs)
- Models/ 
   ("models": objects, functions which connect to database, 
    function as data abstraction layer)
- Routes/
   ("views": implementation of API validation, 
     RESTful & json responses)
- Tests/
   (tests repository)
- main.py
   (main application, route setting)
- config.py
   (hold path for database)
- requirements.txt
   (Pythonic requierments)
- jogging_dataset.csv
   (dataset for jogging tests, loaded by unit tests)
- db_setup.sql 
   (schema file for SQLite3 database)
```

Install requirements by:
 
`pip install -r requirements.txt`

Prerequisites:
* edit `config.py` and point to local database
* run `sqlite3`, and execute the SQL commands in `db_setup.sql`
* install `redis` and run redis server: `redis-server`

To run the project:

`python main.py`

Running tests:

`pytest` or `pytest -s`


### Implementation Notes
 
 * Weekly reports are based on annual week number. The report returns JSON w/ year followed by 
 * running conditions are as elaborate as possible, returning in JSON format. 

### Testing

### ToDos
