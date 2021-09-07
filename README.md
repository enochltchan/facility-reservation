# Facility Reservation System

## Concole Documentation
* Run the console by command "`python3 console.py`"

* You need to run the main.py by command "`uvicorn main:app --reload`" while running the console

* Then try command from following:

  * **reserve** (to make a reservation)

  * **cancel** (to cancel a reservation)

  * **list_reservations** (to generate a report of the reservations for any given date range)

  * **list_transactions** (to list the financial transactions for any given date range)

  * **customer_reservations** (to list the reservations for a given customer for a given date range)

  * **customer_transactions** (to list the transactions for a given customer for a given date range)

  * **exit** (to quits the program)

  * **q** (to quits the program)

  * **commands** (to lists all possible commands)

* Then, the program may prompt you for each argument that is needed to make the eventual request

  A sample input looks like: 

  `(Cmd) reserve`

  `Resource (e.g. workshop/mini microvac etc.): workshop`

  `Customer: Brian`

  `Date and time (MM-DD-YYYY HH:mm): 05-09-2021 14:30`

  

## API Documentation

* Run the main.py by command "`uvicorn main:app --reload`" 

| **Endpoint**             | **Request type** | **Function**                       | **Information needed**                                       | **Information returned**                                     |
| ------------------------ | ---------------- | ---------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| /reservations            | POST             | Make new reservation               | {     “resource”: string    “customer”: string    “date_time_string”:  string (format “MM-DD-YYYY HH:mm”)  }  (important to use double quotes, not single quotes!) | String with reservation confirmation in format  { “message” : string } |
| /reservations            | GET              | List all reservations              | Query (URL) parameters:  start_date_string=string (format “MM-DD-YYYY”, optional, default  01-01-2021)  end_date_string=string(format “MM-DD-YYYY”, optional, default  01-01-2022) | List of reservations in format  {  “serial_num”: {     “date”: string (format  “MM-DD-YYYY HH:mm”)    “resource”: string    “customer”: string    }  …  } |
| /reservations            | DELETE           | Cancel reservation                 | Query (URL) parameter:  serial_num=string                    | String with cancellation confirmation in format  { “message” : string } |
| /reservations/{customer} | GET              | List all reservations for customer | Path parameter:  customer: string  Query (URL) parameters:  start_date_string=string (format “MM-DD-YYYY”, optional, default  01-01-2021)  end_date_string=string(format “MM-DD-YYYY”, optional, default  01-01-2022) | List of reservations in format  {  “serial_num”: {     “date”: string (format  “MM-DD-YYYY HH:mm”)    “resource”: string    }  …  } |
| /transactions            | GET              | List all transactions              | Query (URL) parameters:  start_date_string=string (format “MM-DD-YYYY”, optional, default  01-01-2021)  end_date_string=string(format “MM-DD-YYYY”, optional, default  01-01-2022) | List of transactions in format  {  “id”: {     “date”: string (format  “MM-DD-YYYY HH:mm”)    “customer”: string    “amount”: string    }  …  } |
| /transactions/{customer} | GET              | List all transactions for customer | Path parameter:  customer: string  Query (URL) parameters:  start_date_string=string (format “MM-DD-YYYY”, optional, default  01-01-2021)  end_date_string=string(format “MM-DD-YYYY”, optional, default  01-01-2022) | List of transactions in format  {  “id”: {     “date”: string (format  “MM-DD-YYYY HH:mm”)    “amount”: string    }  …  } |

* Reservations and transactions are stored in a SQLite database in the server directory for persistence.
* “resource” can be one of “workshop”, “mini microvac”, “irradiator”, “polymer extruder”, “high velocity crusher”, “1.21 gigawatt lightning harvester”

