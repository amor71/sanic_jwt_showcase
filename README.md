## JWT Showcasing


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
 
 * Authentication is based on JWT, with _refresh_token_ using best practices defined in https://jwt.io/.
 * User roles are implemented as JWT _scopes_.
 * Implementation assumes running REDIS as in-memory storage for refresh_tokens.
 * JWT out-of-scope: refresh_token rotation, access_token blacklisting, logout, access_token refresh on scope changes.
 * If weather conditions can not be pulled for location and date of run, the jog is not recorded. 
 * Out-of-scope: back-office for setting user roles (set on DB level). However, for unit testing purposes an end-point for setting (=upgrading) user role was implemented.
 * Jogging API are user-specific, and results can not be pulled or *managed* by user-managers or admins.
 * Filtering API required for jogging results only. 
 * Logging were not implemented, however Excpetions are descriptive and explenatory.
 
### Design & Tools

* Sanic (https://sanic.readthedocs.io/en/latest/) has been chosen as a web-server and framework.
* Sanic_jwt (https://sanic-jwt.readthedocs.io/en/v1.3.2/) has been chosen for JWT implementation. **Disclaimer:** I'm a contributor in that project.
* SQLite3 (https://www.sqlite.org/index.html) has been chosen as a database, REDIS (https://redis.io/) was chosen as in-memory storage for refrsh_tokens.
* Two DB tables were implemented, _"users"_ table for storing users, _"jogging_results"_ for stroing jogging results. 
* Relevant indexes were added.
* Below is description of the Schema:

    #### users table

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
  hash_passwords holds the **bcrypted** password. Each user has a create date, and if modified, the last modification date is stored during update, as well as the identify of the updating user.
  Each user has it's own JWT scope which is stored in the DB. expire_date holds the expiration time of a user - instead of deleting a user. 
  A user may delete (=expire) itself, managers and admins may expire other users. 
  Once a user is expired, it can take no further actions, even if the user was already authenticated and has a valid token.
  
    #### jogging_results table
 
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

* Database operations are done using SQLAlchemy (https://www.sqlalchemy.org/), however w/o ORM. 
* There's a quirk that needs to be done in order to return the "id" post insert. This is done by bypassing SQLAlchemy and working directly w/ SQLite cursor (it's known best-practice, and one of the reasons why I normally prefer PostgreSQL).
* The filter API is based on basic parsing of the query-string and passing it to the DB for further parsing. It's not ideal but it's getting the job done on a such implementation. Basic protection against SQL-Injection has been added.
* Report API is generated based on SQL query which groups by year and week.
* More on the returned JSON format in below section(s).
 
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


### API Usage 
 
 * Endpoints returning list adhere to paging: `?page=1&count=10`. Page numbers are zero based. Default page is 0,  default count is 10. 
#### CURD /users routes

* CURD user operations (register, delete, update, list) are implemented on `/users`. Return codes are based on HTTP best practices. 
* Registration payload must include minimum `username` and `password`. username must be unique. Password must adhere to basic minimum requirements. `name` and `email` are optional, however no validation on email is performed (for sake of simplicity).
* `DELETE` a user, will not delete the record from the DB, but rather expire the user. Expired users are ommited from further searches, and can perform any operation. Calling `me` will return an empty object. However, as stated in the assumptions, access_tokens and refresh_tokens are not revoked or blacklisted.
* listing of users (`GET /users`) is a protected endpoint, it can only be accessed by users with scope "manager" or "admin". Managers may see all users, but they can not see other managers or admins. Admins can see all users.
* Here are example payload(s) for manager and admin:

    `GET http://127.0.0.1:61831/users` (for manager)
    
    ```buildoutcfg
    [{'email': None, 'exists': True, 'hashed_password': '$2b$14$XTUPxCBbbaUfISX6nHlvYeq.9k1lpgkEEqd6JLGuO6vhSFOacko0W', 'modified': False, 'name': None, 'scopes': ['user'], 'user_id': 35, 'username': 'amichay.oren+6742@gmail.com'}, {'email': None, 'exists': True, 'hashed_password': '$2b$14$76Gv0tj66LrdSm94xOMBCulljGJpVkLvbbqY/Ddbp0UaF0/XWV4ia', 'modified': False, 'name': None, 'scopes': ['user'], 'user_id': 36, 'username': 'amichay.oren+7714@gmail.com'}, {'email': 'amichay.oren+4472@gmail.com', 'exists': True, 'hashed_password': '$2b$14$DQ7zZ2LlFXZNk5Z7oWtUoeIjP7nSrBQx5oDmzc1W1F36eWPwI74A6', 'modified': False, 'name': 'Amichay Oren', 'scopes': ['user'], 'user_id': 37, 'username': 'amichay.oren+4472@gmail.com'}, {'email': 'amichay.oren+8501@gmail.com', 'exists': True, 'hashed_password': '$2b$14$EINM/hkI0Nd8MUGcUSisi.l8YwbIwqIdMy8SqLa1BPR25a2FwyZsq', 'modified': False, 'name': None, 'scopes': ['user'], 'user_id': 38, 'username': 'amichay.oren+8501@gmail.com'}, {'email': 'amichay@gmail.com', 'exists': True, 'hashed_password': '$2b$14$WcpPWxVkH0ftymxuXew7ieWYRW9YDZM/btJ6nEVayRZzOlCuADLg2', 'modified': False, 'name': None, 'scopes': ['user'], 'user_id': 39, 'username': '6008'}, {'email': 'somebs@a.com', 'exists': True, 'hashed_password': '$2b$14$nMZ2dlbKvq0yL160NIer/ut2DvDFXPIAJpMpWLlrzQOK1xV8K9hwe', 'modified': False, 'name': 'my new name!', 'scopes': ['user'], 'user_id': 40, 'username': 'amichay.oren+2287'}, {'email': 'somebs@a.com', 'exists': True, 'hashed_password': '$2b$14$E0NII/0o9yJoWJo8htj27OnnoWIyS.YEEffw81w3FuR/l/QwT/BGO', 'modified': False, 'name': 'my new name!', 'scopes': ['user'], 'user_id': 41, 'username': 'amichay.oren+1016'}, {'email': 'somebs@a.com', 'exists': True, 'hashed_password': '$2b$14$/RfnPQ3IWjElQ4gsgSooZescUMppctLj1HtxDplDSDg3ZPepcqE5i', 'modified': False, 'name': 'my new name!', 'scopes': ['user'], 'user_id': 42, 'username': 'amichay.oren+2423'}, {'email': 'amichay.oren+4721@gmail.com', 'exists': True, 'hashed_password': '$2b$14$bCmUUIE4GsnK8kXKjZlpredpM6FkyHlxiUb1s44nyfMs9wmXJ1TrG', 'modified': False, 'name': 'Amichay Oren', 'scopes': ['user'], 'user_id': 43, 'username': 'amichay.oren+4721'}, {'email': 'somebs@a.com', 'exists': True, 'hashed_password': '$2b$14$xrQ80Vtd8XXF35lQNysPhuLBEzAVKZOHySX9YQ/7uJzTOmVKMzHg6', 'modified': False, 'name': 'my new name!', 'scopes': ['user'], 'user_id': 44, 'username': 'amichay.oren+9812'}]
    ```
    `GET http://127.0.0.1:61831/users` (for admin)
    
    ```
    [{'email': 'amichay.oren+3885@gmail.com', 'exists': True, 'hashed_password': '$2b$14$Sqmq9hUqR.1dVxQGY7RTNuPymzrFeJsgT3RxlkIOhOYV0GKbY2x5m', 'modified': False, 'name': 'Amichay Oren', 'scopes': ['user', 'admin'], 'user_id': 1, 'username': 'amichay.oren+3885'}, {'email': 'amichay.oren+8955@gmail.com', 'exists': True, 'hashed_password': '$2b$14$rn2aayP0gjM1/LquiILu9.X/AxNG2c7LKWvn8C3RXnc2YAFosUkF.', 'modified': False, 'name': 'Amichay Oren', 'scopes': ['user', 'admin'], 'user_id': 2, 'username': 'amichay.oren+8955'}]
    ```

* The payload are complete in order to instantiate a "User" object in Models.
* PATCH is implemented for partial upload of user details 
* HTTP 204 is returned upon successful update or delete 
* A user may retrieve it's own user_id and details by called `/me` endpoint (see next section).
* DELETE, PATCH will return HTTP 204 w/o return payload.
* Updating user scope was implemented at this `/users/<userId>/scopes`, for testing purposes obly. Any authenticated user may call this route.
* if a user record is updated, the modification dates, and well as the user_id of the modifier will be recorded. 
* modification user_id are not returned in the list endpoints, in order to note exposed user_ids for managers and admins.


#### CURD /auth : Authentication endpoints

* login is done by POST to `/auth` with payload that includes username & password. The login endpoint returns JWT access-token (which is short-lived) amd refresh-token used for getting a new access-token.
* Example response payload:
    
    `{'access_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjo0OCwiZXhwIjoxNTU5NjQ3MTI1LCJpYXQiOjE1NTk2NDUzMjUsIm5hbWUiOiJBbWljaGF5IE9yZW4iLCJlbWFpbCI6ImFtaWNoYXkub3Jlbis0Mzc4QGdtYWlsLmNvbSIsInNjb3BlcyI6WyJ1c2VyIl19.2arsjawnHlPT0StNxTkyO6kEdDImqgCnFPjVbcRidEs', 'refresh_token': '12a6c653839e03be9cfa56d35eed26931668b174a58bb589'}
    ` 
* `access_token` should be used in the header for all protected calls as followes:

    ```buildoutcfg
     headers = {"Authorization": f"Bearer {access_token}"}
    ```
* GET `/auth/verify` validates the access-token and responds with `{'valid': True}`
* GET `/auth/me` returns the user information attached to the token.
* GET `/auth/refresh` returns a new access-token. Keep in mind that the fresh-token is not expired in this basic implementation.
* An example of The JWT claims include:

    ```buildoutcfg
    {
      "user_id": 48,
      "exp": 1559647125,
      "iat": 1559645325,
      "name": "Amichay Oren",
      "email": "amichay.oren+4378@gmail.com",
      "scopes": [
        "user"
      ]
    }
    ```
    * Be advised that the scope is presented, however scope is validated against what appears in the user_id database, and not what is passed in the scope. This means that if user scopes are changed, while they might not be reflected in the JWT claims (yet) they would still impact the authorization.
* Failure to authorize access to resource will return HTTP 403.

#### CURD /results : Jogging endpoints

 * POST `/resutls` with jogging results payload will return the added `result_id`.
 * Example of payload for POST:
 `{
        "date": "1971-06-20",
        "distance": 2000,
        "time": 405,
        "location": "32.0853 34.7818",
    }`

 * Get/Update/Delete are GET/PATCH/DELETE to `/resutls/<id>` returning HTTP 204 unless validation fails.
 * Running conditions are as elaborate as possible, returning in JSON format:
 
    ```
    {"time": 1452290400, "summary": "Partly cloudy throughout the day.", "icon": "partly-cloudy-day", "sunriseTime": 1452314616, "sunsetTime": 1452351244, "moonPhase": 0.97, "precipIntensity": 0.0004, "precipIntensityMax": 0.006, "precipIntensityMaxTime": 1452297600, "precipProbability": 0.45, "precipType": "rain", "temperatureHigh": 64.81, "temperatureHighTime": 1452340800, "temperatureLow": 47.94, "temperatureLowTime": 1452394800, "apparentTemperatureHigh": 64.81, "apparentTemperatureHighTime": 1452340800, "apparentTemperatureLow": 47.94, "apparentTemperatureLowTime": 1452394800, "dewPoint": 48.25, "humidity": 0.67, "pressure": 1018.29, "windSpeed": 6.45, "windGust": 14.99, "windGustTime": 1452337200, "windBearing": 279, "cloudCover": 0.51, "uvIndex": 3, "uvIndexTime": 1452330000, "visibility": 6.22, "temperatureMin": 53.17, "temperatureMinTime": 1452373200, "temperatureMax": 64.81, "temperatureMaxTime": 1452340800, "apparentTemperatureMin": 53.17, "apparentTemperatureMinTime": 1452373200, "apparentTemperatureMax": 64.81, "apparentTemperatureMaxTime": 1452340800}
    ```
 
 * Weekly reports are generated by GET to `/results/reports/weekly`. Report is based on are based on annual week number.
 The report returns JSON w/ year followed by week-number with a tuple including speed and total distance.
 Example:
 
     ```buildoutcfg
    {'2015': [{'1': [4.828042328, 8100]}, {'2': [4.828042328, 8100]}], '2016': [{'1': [4.8780487805, 2000]}, {'52': [4.0, 2000]}], '2018': [{'1': [3.0, 3000]}], '2019': [{'1': [2.5, 2500]}, {'5': [5.0, 100]}, {'9': [5.5, 110]}, {'11': [5.5, 110]}, {'20': [4.4, 110]}]}
    ```
 
 * Searching results at `/results` implement filters as specified (examples are in the unittests).
  

### Testing

* 54 Unit tests have been implemented covering majority of application flows. 
* Unittest are using `pytest` (https://docs.pytest.org/en/latest/) with fixtures for Sanic. 
* Unittests covers both positive and negative flows.
* Unittest print intermediary resutls, and those can be seen if running w/ `-s` for review of payloads & responses.


