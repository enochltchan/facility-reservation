# TA-05 - Work Together ... Wrap it Up ... Applause

This assignment allows the previously created reservation system to interact with its counterparts in other facilities in order to request reservation "holds" and respond to such requests.

## Console Documentation

### How to run it

* Go to `./src` directory and run "`pip3 install -r requirements.txt`" for all packages also run "`pip3 install tabulate`".
* Run the console by command "`python3 console.py`"
* You need to run the main.py by command "`uvicorn main:app --reload`" at the same time while running the console

### Features

#### **Sign up / Login:**

* The console asks the client whether (s)he is a new user or not [yes/no]. And then ask for the user name and password.

  * For new user,  the console asks the client to create a username and password.It also ask for user full name. Finally, the console ask new user to enter his/her role, choosing from "client" or "facility manager".

    Sample input looks like:

    ```
    ** Please log in **
    Are you a new user (yes/no)? yes
    Create user: mike
    Create password: mikepassword
    Full name: michael
    Role (client / facility manager): client
    ==> User added successfully
    ```

  * For old user, the console asks the client for their username and password. It accepts/rejects the user login request depending on whether the username and password matches with data in the database.

    Sample input looks like:

    ```
    ** Please log in **
    Are you a new user (yes/no)? no
    Enter username: mike
    Enter password: mikepassword
    ==> User verification successful
    ```

  * Facility Managers have access to all functionalities, whereas clients only have access to functionalities that relate to their own data.
  
  * Note that passwords are now invisible when typed for better security.

#### **Functionalities for Clients:**

* When you see `(Cmd: {username - client})`, you may try following commands as a client:

  * **(1) reserve** (to make a reservation)

    * It is now more user friendly. It only involves selecting an item from a list of resource. 

      * Also, the program will also summarize the information about the reservation, and asks the user to check with the request if everything is correct. 
      * A sample usage looks like:
      
      ```
      (Cmd: mike - client) reserve
      Facility resources: 
      +-------+-----------------------------------+
      |   No. | resource                          |
      +=======+===================================+
      |     1 | workshop                          |
      +-------+-----------------------------------+
      |     2 | mini microvac                     |
      +-------+-----------------------------------+
      |     3 | irradiator                        |
      +-------+-----------------------------------+
      |     4 | polymer extruder                  |
      +-------+-----------------------------------+
      |     5 | high velocity crusher             |
      +-------+-----------------------------------+
      |     6 | 1.21 gigawatt lightning harvester |
      +-------+-----------------------------------+
      ==> To select a listed parameter, enter 1-6 for the corresponding item
      
      Resource #: 1
      Date and time (MM-DD-YYYY HH:mm): 06-03-2021 13:30
      
      Reservation information collected. This is your reservation: 
      ==> Resource: workshop
      ==> Customer: mike
      ==> Date/Time: 06-03-2021 13:30
      
      Do you wish to create this reservation (yes/no)? yes
      ==> Reservation successful with serial number: 818658a4-d3c8-4aeb-8163-223197c0ae95, Total cost: $742.5, Current account balance: $9257.5
      ```

  * **(2) cancel** (to cancel a reservation)

  * **(3) customer_reservations** (to list the reservations for this client within any entered date range)

  * **(4) customer_transactions** (to list the transactions for this client within any entered date range)

  * **(5) edit_reservation** (to change a specific reservation by entering its serial number)

    * The console will first print out the details of the reservation

    * The user can then either enter in new values, or simply press enter to default to existing values.

    * Sample usage looks like:
  
      ```
      (Cmd: mike - client) edit_reservation
      Serial number (uuid): 818658a4-d3c8-4aeb-8163-223197c0ae95
      ==> ** Current Reservation Values **
      +------------------+------------+
      | date             | resource   |
      +==================+============+
      | 05-31-2021 14:30 | workshop   |
      +------------------+------------+
      Press enter to default to current values.
      Resource (e.g. workshop/mini microvac etc.): mini microvac
      Date and time (MM-DD-YYYY HH:mm): 05-31-2021 13:00        
      ==> Modification successful, Total cost: $1628.75
      ```
  
  * **(6) add_funds** (to add money to this client's account balance)
  
  * **(7) get_profile** ( to view this client's information, including name, account balance, activation status, role  )
  
  * **(8) edit_profile** (to change new full name)
  
  * **(9) get_balance** (to view this client's account balance, e.g: Your account balance is currently $50.0)
  
  * **(10) logout** (to return to login page)

  * **(11) exit / q** (to quits the program)
  
  * **(12) commands** (to lists all possible commands)

#### **Functionalities for Facility Manager:**

* When you see `(Cmd: {username - facility manager})`, you may try following commands as a facility manager. In addition to those functionalities that clients have,  facility managers have 12 more functionalities.

  * **(1) reserve** (to make a reservation for any clients)

    * Same as the explanation in Client functionalities part, we made improvements about selecting an item from list, summarizing the information, and asking the user to check.

    * For facility manager, he/she has functionality to make a hold in a remote facility. 

      * When a reserve request failed for reasons of "`Time outside working hours`", "`Customer limit exceeded`", "`The resource is unavailable`", facility manager can choose to make a hold to place this reservation in a remote facility. 
      * Our program tries to make a hold in every facility until it succeeds in one of them, or they all fail. 
      * Sample output looks like:
      
        ```
        ==> Request failed: Time outside working hours
        Would you like to place a reservation at a remote location? (yes/no): yes
        End time (HH:mm): 20:00
        Attempting to contact facility #2:
        ==> Facility #2. Your hold could not be placed.
        
        Attempting to contact facility #5:
        ==> Error with Facility #5. Could not make request: HTTPConnectionPool(host='linux5.cs.uchicago.edu', port=51225): Max retries exceeded with url: /hold (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x10451bf70>: Failed to establish a new connection: [Errno 61] Connection refused'))
        
        Attempting to contact facility #4:
        ==> Facility #4. Facility not open at these hours.
        
        Attempting to contact facility #3:
        ==> Facility #3: Your hold was placed.
        ```
      
      * For tester's convinience, tester can also try this "making hold" functionality in a separate console file  "`remote_console.py`". It supports making holds on our SSH facility and listing all holds as well.
      
        Tester can request a hold by entering "hold". Sample usage looks like:
      
        ```
        (Cmd: faculty - remote facility manager) hold
        Resource (e.g. workshop/mini microvac etc.): workshop
        Username: brian
        Start date (YYYY-MM-DD): 2021-06-04
        Start time (HH:mm): 10:00
        End time (HH:mm): 11:00
        ==> Hold added successfully with serial numbers for 30-minute blocks: ['d9fb0e47-98d2-48b8-90c3-485f64885664', '94b5c5a8-95f4-48d3-8cf4-8e2710245b60']
        ```

  * **(2) cancel** (to cancel a reservation for any clients)

  * **(3) list_reservations** (to generate a report of all reservations within any entered date range)

  * **(4) list_users** (to list all registered users in the system)

  * **(5) list_transactions** (to list all financial transactions within any entered date range)

  * **(6) list_holds** (to list all holds on our facility) [NEW!!]

  * **(7) customer_reservations** (to generate a report of all reservations for a specific client)

  * **(8) customer_transactions** (to list all financial transactions for a specific client)
  
  * **(9) get_reservation** (to view detail information of a specific reservation by entering its serial number )
  
  * **(10) edit_reservation** (to change detail information of a specific reservation by entering its serial number )
  
  * **(11) add_funds** (to add money to any entered client's account balance)
  
  * **(12) get_balance** (to view any client's account balance, e.g: Mike's account balance is currently $50.0)
  
  * **(13) get_profile** (to view any client's information, including name, account balance, activation status, role )
  
  * **(14) edit_profile** (to change any client's profile information)
  
  * **(15) allow_client_logins** (to authorize a client to log into the system)
  
  * **(16) disallow_client_logins** (to disable a client to login at all)
    
    * If a client is currently logged in, when the FM disallows logins, the client will be logged out when (s)he finishes the current request or makes a new request (whichever comes first).
    * Also, the person launching the server in main.py has a choice to set the default for allowing clients to log-in or not with an environment variable: `export CLIENT_LOGINS_ALLOWED="false"/"true"` If unset, the default is "true".
    
  * **(17) allow_add_funds** (to authorize a client to add funds to his/her account balance)

  * **(18) disallow_add_funds** (to disable a client to add funds to his/her account balance at all)

  * **(19) view_dashboard** (to view the status of "allow_add_funds" and "allow_client_logins")

    * Sample output looks like:

      ```
      Facility Manager Dashboard
      ==> Client logins are currently allowed.
      ==> Clients adding funds is currently allowed.
      ```
  
  * **(20) create_client** (to create an account for a client)
  
  * **(21) activate_client**
  
  * **(22) deactivate_client**
  
  * **(23) logout** (to return to login page)
  
  * **(24) exit / q** (to quits the program)
  
  * **(25) commands** (to lists all possible commands)

#### **Extra functionalities for listing functions:**

* **Export output to a csv file**

  * This is only available for those functionalities that print out lists/summaries, including "list_reservations", "list_transactions", "list_users", "list_holds", "customer_reservations", "customer_transactions"

  * The console gives the user the option to export the results to a .csv file of the user's choice

  * Sample input within any functionalities that print out lists/summaries:

    ```
    ......(data)
    Would you like to export this data to a .csv file? (yes/no) yes
    Enter name of new file (remember the .csv extenstion): mydata.csv
    ==> Success: Data written to csv_files/mydata.csv.
    ```

* **History input**

  * This is only available for those functionalities that print out lists/summaries, including "list_reservations", "list_transactions", "list_users", "list_holds", "customer_reservations", "customer_transactions"

  * The console saves previous history inputs and displays them

  * If the user wants to use an history input, then he/she should only enter the index (No.) of the old input (i.e. 1,2 ...). Otherwise, the user can just type in a regular input as usual.

  * Sample demonstration for usage look like:

    ```
    ==> Past reservation inputs:
    +-------+--------------+------------+
    |  No. | start date  | end date  |
    +=======+==============+============+
    |   1 | 05-20-2021  | 05-25-2021 |
    +=======+==============+============+
    |   2 | 05-01-2021  | 05-30-2021 |
    +-------+--------------+------------+
    ==> To select a listed parameter, enter 1-2 for the corresponding item
    Start date and time (MM-DD-YYYY): 1
    ```


* **Unit tests:** You may view and run all unit tests in "`/src/test_main.py`"





## API Documentation

* Run the main.py by command "`uvicorn main:app --reload`"

| **Endpoint**                              | **Request type** | **Function**                                       | **Information needed**                                       | **Information returned**                                     |
| ----------------------------------------- | ---------------- | -------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| /reservations                             | POST             | Make new reservation                               | {     “resource”: string,    “customer”: string,    “date_time_string”:  string (format “MM-DD-YYYY HH:mm”)  }  (important to use double quotes, not single quotes!) | String with reservation confirmation in format  { “message” : string } |
| /reservations                             | PUT              | Edit existing reservation                          | {     “serial_num”: string,    “resource”: string,    “customer”: string,    “date_time_string”:  string (format “MM-DD-YYYY HH:mm”)  } | String with modification confirmation in format { “message” :  string } |
| /reservations                             | GET              | List all reservations                              | Query (URL) parameters:  start_date_string=string (format “MM-DD-YYYY”, optional, default  01-01-2021)  end_date_string=string(format “MM-DD-YYYY”, optional, default  01-01-2022) | List of reservations in format  {  “serial_num”: {     “date”: string (format  “MM-DD-YYYY HH:mm”)    “resource”: string,    “customer”: string    }  …  } |
| /reservations/  serial_num/  {serial_num} | GET              | Get reservation with serial number                 | Path parameter:  serial_num: string                          | Reservation in format  {  “date”: string (format “MM-DD-YYYY HH:mm”),  “resource”: string  } |
| /reservations                             | DELETE           | Cancel reservation                                 | Query (URL) parameters:  customer=string  serial_num=string  | String with cancellation confirmation in format  { “message” : string } |
| /reservations/  {customer}                | GET              | List all reservations for customer                 | Path parameter:  customer: string  Query (URL) parameters:  start_date_string=string (format “MM-DD-YYYY”, optional, default  01-01-2021)  end_date_string=string(format “MM-DD-YYYY”, optional, default  01-01-2022) | List of reservations in format  {  “serial_num”: {     “date”: string (format  “MM-DD-YYYY HH:mm”),    “resource”: string    }  …  } |
| /transactions                             | GET              | List all transactions                              | Query (URL) parameters:  start_date_string=string (format “MM-DD-YYYY”, optional, default 01-01-2021)  end_date_string=string(format “MM-DD-YYYY”, optional, default  01-01-2022) | List of transactions in format  {  “id”: {     “date”: string (format  “MM-DD-YYYY HH:mm”),    “customer”: string,    “amount”: string    }  …  } |
| /transactions/  {customer}                | GET              | List all transactions for customer                 | Path parameter:  customer: string  Query (URL) parameters:  start_date_string=string (format “MM-DD-YYYY”, optional, default  01-01-2021)  end_date_string=string(format “MM-DD-YYYY”, optional, default  01-01-2022) | List of transactions in format  {  “id”: {     “date”: string (format  “MM-DD-YYYY HH:mm”),    “amount”: string    }  …  } |
| /users                                    | POST             | Add new user                                       | {    “id”: string,    “password”: string,    “name”: string,    “role”: string  } | String with confirmation in format  { “message” : string }   |
| /users                                    | GET              | List all users                                     | -                                                            | List of users in format   {   “id”: {     “name”: string,    “account balance”:   float,    “activation status”:  string,    “role”: string    }  …  } |
| /users/{id}                               | GET              | Get user details                                   | Path parameter:  id: string                                  | User details in format  {  “name”: string,  “account balance”: float,  “activation status”: bool,  “role”: string  } |
| /users/{id}                               | DELETE           | Delete user                                        | Path parameter:  id: string                                  | String with confirmation in format  { “message” : string }   |
| /users/{id}/name                          | PUT              | Update user’s name                                 | Path parameter:  id: string  { “name”: string }              | String with confirmation in format  { “message” : string }   |
| /users/{id}/  account_balance             | PUT              | Add to user’s account balance                      | Path parameter:  id: string  { “amount”: float }             | String with confirmation in format  { “message” : string }   |
| /users/{id}/  activation                  | PUT              | Change user’s activation status                    | Path parameter:  id: string  { “activation”: bool }          | String with confirmation in format  { “message” : string }   |
| /validity                                 | POST             | Check if user ID and password combination is valid | {    “id”: string,    “password”: string  }                  | Validity of user ID in format { “validity”: bool }           |
| /settings/{setting}                       | GET              | Get current value of setting                       | Path parameter:  setting: string                             | Current value of setting in format { “value”: bool }         |
| /settings/{setting}                       | POST             | Set value of setting                               | Path parameter:  setting: string  { “value”: bool }          | String with confirmation in format  { “message” : string }   |
| /hold                                     | POST             | Make new hold                                      | {    “username”: string,    “password”: string,    “client_name”: string,    “request”: string  (resource including number, eg. “mini microvac2”),    “start_date”: string  (format “YYYY-MM-DD”),    “start_time”: string  (format “HH:mm”),    “end_time”: string  (format “HH:mm”)  } | String with confirmation in format  {    “success”: bool,    “message”: string,    “facility_name”: string  } |
| /hold                                     | GET              | List all holds                                     | -                                                            | List of holds in format   {  “serial_num”: {     “date”: string (format  “MM-DD-YYYY HH:mm”)    “resource”: string,    “customer”: string,    “reserver”: string    }  …  } |

* Reservations and transactions are stored in a SQLite database in the server directory for persistence. A separate test database is provided for running tests without affecting production data, which can be accessed by setting the environment variable DB_NAME to “test” before running the app.

* “resource” can be one of “workshop”, “mini microvac”, “irradiator”, “polymer extruder”, “high velocity crusher”, “1.21 gigawatt lightning harvester”

* “role” can currently be either “facility manager” or “client”

* “setting” can currently be either “client_logins_allowed” or “client_adding_funds_allowed”. Client logins can also be disallowed prior to running the app by setting the environment variable CLIENT_LOGINS_ALLOWED to “false”.

  

*Note:*  

* The “customer” string for non-user-specific endpoints is the same as the user ID for user-specific endpoints.

* Our facility is located in Chicago, USA (CST/CDT). Business hours are:

  Mon-Fri 09:00-18:00 ;

  Sat 10:00-16:00

* Login credentials for remote facility managers:

| Username | Password   |
| -------- | ---------- |
| peter    | pwdpeter   |
| spencer  | pwdspencer |
| team2    | password2  |
| team3    | password3  |
| team4    | password4  |
| team5    | password5  |

## Testing Documentation

### How to run it

* Create an environment variable called "DB_NAME" and set its value to "test"

* Run the command "pytest" from the command line when navigating to the code directory - run "pytest -vv" for verbose output

* Tests prefixed with "test_api" test API endpoints, those with "test_db" test database functions, and those with "test_e2e" are end-to-end integration tests

 