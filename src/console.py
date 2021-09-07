import os
import requests, json, tabulate, csv, random, getpass

LOCALHOST = "http://127.0.0.1:8000"
REMOTE_HOST = "http://linux1.cs.uchicago.edu:51221"

HOST = REMOTE_HOST

# Helper function for printing error messages
def print_error(response):
    try:
        if type(response.json()["detail"]) is list:
            print("==> Request failed: " + str(response.json().get("detail")[0].get("msg")))
        elif type(response.json()["detail"]) is dict:
            print("==> Request failed: " + str(response.json().get("detail")["message"]))
        else:
            print("==> Request failed: " + str(response.json().get("detail")))
    except Exception as e:
        print("==> Unknown error: Response missing detail.")

# Helper function for printing dictionaries
def print_dictionary(dict):
    for key, value in dict.items():
        print(f"==> {key}: {value}")
    print("")

# Helper function for summarizing/visualizing newly entered/created data
def summarize_entered_data(data, data_type="data"):
    # Summarize information for user
    print(f"\n{data_type.capitalize()} information collected. This is your {data_type}: ")
    print_dictionary(data)
    # Give user option to change mind on creating profile
    user_wants_to_continue = input(f"Do you wish to create this {data_type} (yes/no)? ").strip()
    return user_wants_to_continue == "yes"

# Helper for creating a dataset of reservations suitable for tabulate
# - reservations: dictonary of dictionaries (json response obj)
def add_ids_to_data(reservations):
    dataset = []
    for res_id, reservation in reservations.items():
        id_dict = {"ID": res_id}
        id_dict.update(reservation)
        dataset.append(id_dict)
    return dataset

# Helper for creating a dataset of past reservations/txn date-range inputs
# that is suitable for tabulate. Returns list of dictionaries.
# - old_inputs: list of dictionaries.
def transform_data_to_tablulate(old_inputs):
    upper_limit = 5 if len(old_inputs) > 5 else len(old_inputs)
    latest_inputs = old_inputs[0:upper_limit]
    transformed_data = []
    for i in range(len(latest_inputs)):
        input = latest_inputs[i]
        data_point = {"No.": str(i+1), "start date": input["start_date_string"], "end date": input["end_date_string"]}
        transformed_data.append(data_point)
    return transformed_data

# Helper for printing out lists (of dictionaries) in table format
# Helps with listing things like reservations, transactions etc.
def print_list_as_table(dataset, fmt='fancy_grid'):
    if len(dataset) == 0:
        print("No data to display.")
        return
    header = dataset[0].keys()
    rows = [x.values() for x in dataset]
    print(tabulate.tabulate(rows, header, tablefmt=fmt))

# Helper for creating a csv file from the dataset
def create_csv(dataset):
    # If dataset is empty, do not offer user csv option
    if len(dataset) == 0:
        return
    while True:
        make_csv = input("Would you like to export this data to a .csv file? (yes/no) ")
        if make_csv.strip() == "yes":
            # Enter file name
            csv_file_name = input("Enter name of new file (remember the .csv extenstion): ").strip()
            # Check if any mistakes in file name
            if len(csv_file_name.split(".")) != 2:
                print("==> Error: File name improprely formatted. Please try again.\n")
                continue
            else:
                root, ext = csv_file_name.split(".")
                # Loop back if missing .csv extension
                if ext != "csv":
                    print("==> Error: File name missing .csv extension. Please try again.\n")
                    continue

            # Offer options in case file name already exists
            if os.path.exists(f"csv_files/{csv_file_name}"):
                print(f"\n==> A file with the name '{csv_file_name}' already exists in 'csv_files'.")
                overwrite_option = input("Would you like to (a) enter a new name, (b) not export, or (c) overwrite the file?: ")
                if overwrite_option == "a":
                    print("")
                    continue
                elif overwrite_option == "b":
                    return

            # Writing to the .csv file
            keys = dataset[0].keys()
            with open(f"csv_files/{csv_file_name}", 'w', newline='')  as output_file:
                try:
                    dict_writer = csv.DictWriter(output_file, keys)
                    dict_writer.writeheader()
                    dict_writer.writerows(dataset)
                    print(f"==> Success: Data written to csv_files/{csv_file_name}.\n")
                except:
                    print("==> Error: Unable to write to csv file.\n")
            return
        elif make_csv.strip() == "no":
            return
        else:
            print("Please answer with either 'yes' or 'no' !\n")


## The Console class
class Console():
    def __init__(self):
        self.all_commands = ["reserve", "cancel", "list_reservations", "list_users",
                            "list_transactions", "list_holds", "customer_reservations",
                            "customer_transactions", "get_reservation", "edit_reservation",
                            "add_funds", "get_balance", "get_profile", "edit_profile",
                            "allow_client_logins", "disallow_client_logins", "allow_add_funds",
                            "disallow_add_funds", "view_dashboard",
                            "create_client", "activate_client", "deactivate_client",
                            "logout", "exit / q", "commands"]
        self.client_commands = ["reserve", "cancel", "customer_reservations",
                                "customer_transactions", "edit_reservation",
                                "add_funds", "get_profile", "edit_profile", "get_balance",
                                "logout", "exit / q", "commands"]
        self.username = ""
        self.role = ""
        # Lists of dictionaries of old date-range options.
        self.reservation_inputs = []
        self.transaction_inputs = []
        # List of resources
        self.resources = ["workshop", "mini microvac", "irradiator",
                          "polymer extruder", "high velocity crusher",
                          "1.21 gigawatt lightning harvester"]

    ### *** HELPER FUNCTIONS *** ###
    # Helper function to reset user
    def reset_user(self):
        self.username = ""
        self.role = ""
        self.reservation_inputs = []
        self.transaction_inputs = []

    # Helper function for checking user permissions
    # Currently simply a check if the user is a facility manager
    def user_has_permissions(self):
        return self.role == "facility manager"

    # Helper function for checking whether user is a facility manager
    def user_is_facility_manager(self):
        return self.role == "facility manager"

    # Helper function for checking whether user is a client
    def user_is_client(self):
        return self.role == "client"

    # Helper function for a resource is unavailable (so that the customer may be offered a hold in another facility)
    def resource_is_unavailable(self, detail):
        #return detail == "Resource unavailable" or detail == "Customer limit exceeded" or detail == "Time outside working hours"
        if type(detail) is dict:
            return detail.get("hold_request_possible")
        else:
            return False

    # Helper function for checking if the resource is unique or not
    def resource_is_unique(self, resource):
        return resource == "1.21 gigawatt lightning harvester" or resource == "high velocity crusher"

    # Helper function for checking whether user is a facility manager
    def get_customer_username(self):
        if self.user_is_facility_manager():
            customer = input("Username: ")
        else:
            customer = self.username
        return customer

    # Helper function for informing the user of default reservation values
    def get_default_reservation(self, serial_num):
        try:
            response = requests.get(f"{HOST}/reservations/serial_num/{serial_num}")
            if response.json().get('detail') is None:
                print("==> ** Current Reservation Values ** ")
                print_list_as_table([ dict(response.json()) ])
                print("==> Press enter to default to current values.")
                return response.json().get('resource'), response.json().get('date')
            else:
                print_error(response)
        except Exception as e:
            print_error(response)
        return None, None

    # Helper function for displaying old date range inputs for reservation/transaction
    def display_old_date_inputs(self, input_type, old_inputs):
        print(f"==> Past {input_type} inputs: ")
        tabulate_data = transform_data_to_tablulate(old_inputs)
        print_list_as_table(tabulate_data)
        if len(tabulate_data) == 1:
            print(f"==> To select a listed parameter, enter 1 for the corresponding item")
        elif len(tabulate_data) > 1:
            print(f"==> To select a listed parameter, enter 1-{len(tabulate_data)} for the corresponding item")
        return tabulate_data

    # Helper to get date range input from user
    def request_dates_from_user(self, tabulate_data):
        past_options = [str(x) for x in range(1, len(tabulate_data)+1)]
        start_date_string = input("Start date and time (MM-DD-YYYY): ")
        end_date_string = input("End date and time (MM-DD-YYYY): ")
        # Check if user information is valid old inputs (or new input)
        # Booleans that indicate if user used old date or not
        old_start, old_end = False, False
        if start_date_string.strip() in past_options:
            old_start = True
            idx = int(start_date_string.strip())-1
            start_date_string = tabulate_data[idx]["start date"]
        if end_date_string.strip() in past_options:
            old_end = True
            idx = int(end_date_string.strip())-1
            end_date_string = tabulate_data[idx]["end date"]
        return start_date_string, end_date_string, old_start, old_end

    # Helper function for placing holds in other facilities
    def request_remote_hold(self, payload):
        end_time = input("End time (HH:mm): ").strip()
        resource = payload["resource"]
        request = resource + "1" if not self.resource_is_unique(resource) else resource
        #print(request)
        start_date_proper, start_time = payload["date_time_string"].split(" ")
        mm, dd, yyyy = start_date_proper.split("-")
        start_date_improper = f"{yyyy}-{mm}-{dd}"
        host_payload = {
            "username": "team1",
            "password": "password1",
            "client_name": payload["customer"],
            "request": request,
            "start_date": start_date_improper,
            "start_time": start_time,
            "end_time": end_time
        }
        #print(host_payload)
        team_ids = list(range(2,6))
        random.shuffle(team_ids)
        for N in team_ids:
            print(f"Attempting to contact facility #{N}:")
            try:
                response = requests.post(f"http://linux{N}.cs.uchicago.edu:5122{N}/hold", json=host_payload)
                if response.json().get("success") == True and response.json().get("message") is not None:
                    print(f"==> Facility #{N}: " + response.json().get("message") + "\n")
                    return
                elif response.json().get("success") == False and response.json().get("message") is not None:
                    print(f"==> Facility #{N}: " + response.json().get("message") + "\n")
                    continue
                else:
                    print(f"==> Facility #{N}: Error - could not make request\n")

            except Exception as e:
                print(f"==> Error with Facility #{N}. Could not make request: {str(e)}\n")

        print("==> No available facilities to place hold.")


    # Helper function for offering facility managers to make holds in other facilities
    def offer_remote_facility(self, response, payload):
        # Only facility managers may perform this action
        if self.user_is_facility_manager() and response.json().get("detail") is not None:
            detail = response.json().get("detail")
            #print(detail)
            if self.resource_is_unavailable(detail):
                while True:
                    make_remote_request = input("Would you like to place a reservation at a remote location? (yes/no): ")
                    if make_remote_request.strip() == "yes":
                        self.request_remote_hold(payload)
                        return
                    elif make_remote_request.strip() == "no":
                        return
                    else:
                        print("Please answer with either 'yes' or 'no'!")

    # Helper function for getting requested resource string from user
    def request_resource_from_user(self, default_option_exists=False):
        # Display facility resources
        print("Facility resources: ")
        print_list_as_table([{"No." : i+1, "resource": resource} for i, resource in enumerate(self.resources)], 'grid')
        print("==> To select a listed parameter, enter 1-6 for the corresponding item\n")

        # Request information from user
        list_options = [str(x) for x in range(1, len(self.resources)+1)]
        while True:
            resource_list_option = input("Resource #: ")
            if default_option_exists and resource_list_option.strip() == "":
                return ""
            elif resource_list_option.strip() not in list_options:
                print("Option not listed, please try again (remember to enter 1-6)\n")
                continue
            else:
                resource = self.resources[int(resource_list_option)-1]
                return resource

    ### *** END OF HELPER FUNCTIONS *** ###


    ### *** USER/CLIENT FUNCTIONS *** ###
    # Function for reserving a resource
    def reserve(self):
        # Get user information
        resource = self.request_resource_from_user()
        customer = self.get_customer_username()
        reserver = self.username
        date_time_string = input("Date and time (MM-DD-YYYY HH:mm): ")

        # Summarize information for user
        user_wants_to_continue = summarize_entered_data({"Resource": resource, "Customer": customer, "Date/Time": date_time_string}, "reservation")
        # Give user option to change mind on creating profile
        if not user_wants_to_continue:
            print("==> Exiting. Reservation not created.")
            return

        # Make post request to localhost URL, and print the response
        payload = {"resource": resource, "customer": customer, "reserver": reserver, "date_time_string": date_time_string}
        try:
            response = requests.post(f"{HOST}/reservations", json=payload)
            print("==> " + response.json().get("message"))
        except Exception:
            print_error(response)
            self.offer_remote_facility(response, payload)


    # Function for cancelling a reservation
    def cancel(self):
        # Request information from user
        serial_num = input("Serial number (uuid): ")
        customer = self.get_customer_username()
        # Make delete request to localhost URL, and print the response
        parameters = {"customer": customer, "serial_num": serial_num}
        try:
            response = requests.delete(f"{HOST}/reservations", params=parameters)
            print("==> " + response.json().get("message"))
        except Exception:
            print_error(response)


    # Function for listing all reservations within a given timeframe
    # *** Facility manager restricted ***
    def list_reservations(self):
        # Check user's permissions
        if not self.user_has_permissions():
            print("==> Error: This account does not have permission to perform this action.")
            return

        # Display old inputs from which to choose
        tabulate_data = self.display_old_date_inputs("reservation", self.reservation_inputs)
        # Request information from user
        start_date_string, end_date_string, old_start, old_end = self.request_dates_from_user(tabulate_data)
        # Make get request to localhost URL, and print the response
        parameters = {"start_date_string": start_date_string, "end_date_string": end_date_string}
        try:
            response = requests.get(f"{HOST}/reservations", params=parameters)
            if response.json().get('detail') is not None:
                print_error(response)
            else:
                if not (old_start and old_end):
                    self.reservation_inputs.insert(0, parameters)
                # Print output
                print(f"\nReservations from {start_date_string} to {end_date_string}:")
                dataset = add_ids_to_data(dict(response.json()))
                print_list_as_table(dataset)
                # Offer to create .csv file from dataset
                create_csv(dataset)
        except Exception:
            print_error(response)


    # Function for listing all transactions within a given timeframe
    # *** Facility manager restricted ***
    def list_transactions(self):
        # Check user's permissions
        if not self.user_has_permissions():
            print("==> Error: This account does not have permission to perform this action.")
            return

        # Display old inputs from which to choose
        tabulate_data = self.display_old_date_inputs("transaction", self.transaction_inputs)
        # Request information from user
        start_date_string, end_date_string, old_start, old_end = self.request_dates_from_user(tabulate_data)
        # Make get request to localhost URL, and print the response
        parameters = {"start_date_string": start_date_string, "end_date_string": end_date_string}
        try:
            response = requests.get(f"{HOST}/transactions", params=parameters)
            if response.json().get('detail') is not None:
                print_error(response)
            else:
                if not (old_start and old_end):
                    self.transaction_inputs.insert(0, parameters)
                print(f"\nTransactions from {start_date_string} to {end_date_string}:")
                dataset = add_ids_to_data(dict(response.json()))
                print_list_as_table(dataset)
                # Offer to create .csv file from dataset
                create_csv(dataset)
        except Exception:
            print_error(response)


    # Helper function for listing all users.
    # *** Facility manager restricted ***
    def list_users(self):
        if not self.user_has_permissions():
            print("==> Error: This account does not have permission to perform this action.")
            return
        # Make get request to localhost URL, and print the response
        try:
            response = requests.get(f"{HOST}/users")
            print(f"\nAll users:")
            dataset = add_ids_to_data(dict(response.json()))
            print_list_as_table(dataset)
            # Offer to export data to .csv file
            create_csv(dataset)
        except Exception:
            print_error(response)


    # Helper function for listing all holds.
    # *** Facility manager restricted ***
    def list_holds(self):
        if not self.user_has_permissions():
            print("==> Error: This account does not have permission to perform this action.")
            return
        # Make get request to localhost URL, and print the response
        try:
            response = requests.get(f"{HOST}/hold")
            print(f"\nAll holds:")
            dataset = add_ids_to_data(dict(response.json()))
            print_list_as_table(dataset)
            # Offer to export data to .csv file
            create_csv(dataset)
        except Exception:
            print_error(response)


    # Function for listing all reservations for a given customer within a given timeframe
    def customer_reservations(self):
        # Request information from user
        customer = self.get_customer_username()
        # Display old inputs from which to choose
        tabulate_data = self.display_old_date_inputs("reservation", self.reservation_inputs)
        # Request information from user
        start_date_string, end_date_string, old_start, old_end = self.request_dates_from_user(tabulate_data)

        # Make get request to localhost URL, and print the response
        parameters = {"customer": customer, "start_date_string": start_date_string, "end_date_string": end_date_string}
        try:
            response = requests.get(f"{HOST}/reservations/{customer}", params=parameters)
            if response.json().get('detail') is not None:
                print_error(response)
            else:
                if not (old_start and old_end):
                    self.reservation_inputs.insert(0, parameters)
                print(f"\nReservations for {customer} from {start_date_string} to {end_date_string}:")
                dataset = add_ids_to_data(dict(response.json()))
                print_list_as_table(dataset)
                # Offer to create .csv file from dataset
                create_csv(dataset)
        except Exception:
            print_error(response)


    # Function for listing all transactions for a given customer within a given timeframe
    def customer_transactions(self):
        # Request information from user
        customer = self.get_customer_username()
        # Display old inputs from which to choose
        tabulate_data = self.display_old_date_inputs("transaction", self.transaction_inputs)
        # Request information from user
        start_date_string, end_date_string, old_start, old_end = self.request_dates_from_user(tabulate_data)
        # Make get request to localhost URL, and print the response
        parameters = {"customer": customer, "start_date_string": start_date_string, "end_date_string": end_date_string}
        try:
            response = requests.get(f"{HOST}/transactions/{customer}", params=parameters)
            if response.json().get('detail') is not None:
                print_error(response)
            else:
                if not (old_start and old_end):
                    self.transaction_inputs.insert(0, parameters)
                print(f"\nTransactions for {customer} from {start_date_string} to {end_date_string}:")
                dataset = add_ids_to_data(dict(response.json()))
                print_list_as_table(dataset)
                # Offer to create .csv file from dataset
                create_csv(dataset)
        except Exception as e:
            print_error(response)


    # Function for getting a reservation with a specific ID
    # *** Facility manager restricted ***
    def get_reservation(self):
        # Check user's permissions
        if not self.user_has_permissions():
            print("==> Error: This account does not have permission to perform this action.")
            return
        # Request information from user
        serial_num = input("Serial number (uuid): ")
        try:
            response = requests.get(f"{HOST}/reservations/serial_num/{serial_num}")
            if response.json().get('detail') is not None:
                print_error(response)
            else:
                print("==> Reservation: ")
                print_list_as_table([ dict(response.json()) ])
        except Exception as e:
            print_error(response)


    # Function for creating a client
    # *** Facility manager restricted ***
    def create_client(self):
        # Check user's permissions
        if not self.user_has_permissions():
            print("==> Error: This account does not have permission to perform this action.")
            return
        # Get information from user
        username = input("Enter username: ")
        password = input("Enter password: ")
        full_name = input("Full name: ")
        payload = {"id": username, "password": password, "name": full_name, "role": "client"}
        try:
            response = requests.post(f"{HOST}/users", json=payload)
            if response.json().get("detail") is None:
                print("==> " + str(response.json().get("message")))
            else:
                print("==> Error: " + str(response.json().get("detail")))
        except Exception:
            print_error(response)


    # Function for deactivating a client
    # *** Facility manager restricted ***
    def client_activation(self, activation):
        # Check user's permissions
        if not self.user_has_permissions():
            print("==> Error: This account does not have permission to perform this action.")
            return
        customer = self.get_customer_username()
        data = {"activation": activation}
        try:
            response = requests.put(f"{HOST}/users/{customer}/activation", data=json.dumps(data))
            if response.json().get("detail") is None:
                print("==> " + str(response.json().get("message")))
            else:
                print("==> Error: " + str(response.json().get("detail")))
        except Exception:
            print_error(response)


    # Function for allowing/disallowing client logins
    # *** Facility manager restricted ***
    def allow_client_logins(self, allow):
        # Check user's permissions
        if not self.user_has_permissions():
            print("==> Error: This account does not have permission to perform this action.")
            return
        setting = "client_logins_allowed"
        payload = {"value": allow}
        try:
            response = requests.post(f"{HOST}/settings/{setting}", json=payload)
            if response.json().get("detail") is None:
                print("==> " + str(response.json().get("message")))
            else:
                print("==> Error: " + str(response.json().get("detail")))
        except Exception:
            print_error(response)


    # Function for checking if client logins are allowed
    # *** Facility manager restricted ***
    # -- Permissions check not done because clients need this function to see if
    #    their login permissions have been removed --
    def client_logins_allowed(self):
        # Check user's permissions
        setting = "client_logins_allowed"
        try:
            response = requests.get(f"{HOST}/settings/{setting}")
            if response.json().get("detail") is None:
                return response.json().get("value")
            else:
                print("==> Error: " + str(response.json().get("detail")))
        except Exception:
            print_error(response)
        return None


    # Function for allowing/disallowing clients to add funds
    # *** Facility manager restricted ***
    def allow_add_funds(self, allow):
        # Check user's permissions
        if not self.user_has_permissions():
            print("==> Error: This account does not have permission to perform this action.")
            return
        setting = "client_adding_funds_allowed"
        payload = {"value": allow}
        try:
            response = requests.post(f"{HOST}/settings/{setting}", json=payload)
            if response.json().get("detail") is None:
                print("==> " + str(response.json().get("message")))
            else:
                print("==> Error: " + str(response.json().get("detail")))
        except Exception:
            print_error(response)


    # Function for checking if adding funds is allowed for clients
    # *** Facility manager restricted ***
    # -- Permissions check not done because clients need this function to see if
    #    their login permissions have been removed --
    def add_funds_allowed(self):
        # Check user's permissions
        setting = "client_adding_funds_allowed"
        try:
            response = requests.get(f"{HOST}/settings/{setting}")
            if response.json().get("detail") is None:
                return response.json().get("value")
            else:
                print("==> Error: " + str(response.json().get("detail")))
        except Exception:
            print_error(response)
        return None


    # Function for viewing the facility manager dashboard
    # *** Facility manager restricted ***
    def view_dashboard(self):
        print("\n*** Facility Manager Dashboard ***")
        if HOST == REMOTE_HOST:
            print("==> Console is connected to remote host.")
        else:
            print("==> Console is connected to local host.")
        if self.client_logins_allowed():
            print("==> Client logins are currently allowed.")
        else:
            print("==> Client logins are currently not allowed.")
        if self.add_funds_allowed():
            print("==> Clients adding funds is currently allowed.")
        else:
            print("==> Clients adding funds is currently not allowed.")
        print("\n")

    # Function for editing a reservation
    def edit_reservation(self):
        serial_num = input("Serial number (uuid): ")
        customer = self.get_customer_username()
        reserver = self.username
        # Get existing reservation
        default_resource, default_dtstr = self.get_default_reservation(serial_num)
        if default_resource is None or default_dtstr is None:
            print("==> Error in getting reservation. Reservation with given ID may not exist.")
            return
        resource = self.request_resource_from_user(True)
        date_time_string = input("Date and time (MM-DD-YYYY HH:mm): ")

        # Default to old reservation if user presses enter
        resource = default_resource if resource.strip() == "" else resource
        date_time_string = default_dtstr if date_time_string.strip() == "" else date_time_string
        data = {"serial_num": serial_num, "resource": resource, "customer": customer, "reserver": reserver, "date_time_string": date_time_string}
        # Send the request
        try:
            response = requests.put(f"{HOST}/reservations", data=json.dumps(data))
            print("==> " + response.json().get("message"))
        except Exception:
            print_error(response)


    # Function for adding funds to account
    def add_funds(self):
        if self.user_is_client() and not self.add_funds_allowed():
            print("*** Clients currently not allowed to add funds. ***")
            return
        customer = self.get_customer_username()
        amount = input("Amount to add: ")
        data = {"amount": amount}
        try:
            response = requests.put(f"{HOST}/users/{customer}/account_balance", data=json.dumps(data))
            print("==> " + response.json().get("message"))
        except Exception as e:
            print_error(response)


    # Function for editing user profile
    def get_profile(self):
        customer = self.get_customer_username()
        try:
            response = requests.get(f"{HOST}/users/{customer}")
            if response.json().get("detail") is None:
                print("==> Profile: ")
                print_list_as_table([ dict(response.json()) ])
            else:
                print_error(response)
        except Exception:
            print_error(response)


    # Function for editing user profile
    def edit_profile(self):
        customer = self.get_customer_username()
        name = input("Enter new full name: ")
        data = {"name": name}
        try:
            response = requests.put(f"{HOST}/users/{customer}/name", data=json.dumps(data))
            print("==> " + response.json().get("message"))
        except Exception:
            print_error(response)


    # Function for getting user account balance
    def get_balance(self):
        customer = self.get_customer_username()
        try:
            response = requests.get(f"{HOST}/users/{customer}")
            print("==> " + "Your account balance is currently $" + str(response.json().get("account balance")))
        except Exception:
            print_error(response)


    # Helper function for listing all supported commands
    def list_commands(self):
        commands = self.all_commands if self.user_is_facility_manager() else self.client_commands
        print("\nSupported commands:")
        for i in range(1, len(commands)+1):
            print(f"  ({i}) {commands[i-1]}")
        print("")


    # Helper function for verifying an existing user
    def verify_existing_user(self):
        username = input("Enter username: ")
        #password = input("Enter password: ")
        password = getpass.getpass(prompt="Enter password: ")
        payload = {"id": username, "password": password}
        try:
            response = requests.post(f"{HOST}/validity", json=payload)
            user_exists = response.json()["validity"]
            if user_exists:
                # Get user role if exists
                rsp = requests.get(f"{HOST}/users/{username}")
                print("==> User verification successful")
                self.username = username
                self.role = rsp.json()["role"]
                return True
            else:
                print("==> Error: Invalid username.")
                return False
        except Exception as e:
            print("==> Unknown error - User verification could not complete: " + str(e))
            return False

    # Helper function for creating new user
    def create_user(self):
        # Get user information
        username = input("Create user: ")
        while True:
            password = getpass.getpass(prompt="Create password: ")
            retype_password = getpass.getpass(prompt="Re-enter password: ")
            if password != retype_password:
                print("Passwords do not match. Try again.")
                continue
            else:
                print("Passwords match. Please complete your profile.")
                break
        full_name = input("Full name: ")
        role = input("Role (client / facility manager): ")

        # Summarize information for user
        user_wants_to_continue = summarize_entered_data({"Username": username, "Name": full_name, "Role": role}, "profile")

        # Give user option to change mind on creating profile
        if not user_wants_to_continue:
            print("Exiting user creation. Profile not created.")
            return False
        create_successful = True

        # Make post request to localhost URL, and print the response
        payload = {"id": username, "password": password, "name": full_name, "role": role}
        try:
            response = requests.post(f"{HOST}/users", json=payload)
            print("==> " + response.json().get("message"))
            self.username = username
            self.role = role
        except:
            create_successful = False
            print_error(response)

        return create_successful

    # Helper function for verifying whether the user is new or not
    def user_login(self):
        while True:
            print("** Please log in **")
            is_new_user = input("Are you a new user (yes/no)? ")
            if is_new_user.strip() == "yes":
                create_successful = self.create_user()
                if create_successful:
                    return
                else:
                    continue
            elif is_new_user.strip() == "no":
                user_exists = self.verify_existing_user()
                if user_exists:
                    return
                else:
                    continue
            elif is_new_user.strip() == "exit" or is_new_user.strip() == "q":
                print("Exiting the program.")
                exit()
            else:
                print("Please answer with either 'yes' or 'no'!")
                continue


    # Function to run the console
    def run(self):
        print("###=== Welcome to the MPCS Inc. Reservation System! ===###")
        print("Our facility is located in Chicago, USA (CST/CDT). Business hours are:")
        print("Mon-Fri 09:00-18:00")
        print("Sat 10:00-16:00")
        # Verify the user's identity. If the user is new, create a username.
        self.user_login()
        # Run command line for console
        while True:
            # Check if user is a client and if client logins are allowed
            if self.user_is_client() and not self.client_logins_allowed():
                print("*** Client logins have been disabled. Logging out now. ***")
                self.reset_user()
                self.user_login()
                continue
            # Get user command
            command = input(f"(Cmd: {self.username} - {self.role}) ")
            command = command.strip()
            # Check if user is a client and if client logins are allowed
            if self.user_is_client() and not self.client_logins_allowed():
                print("*** Client logins have been disabled. Logging out now. ***")
                self.reset_user()
                self.user_login()
                continue
            # Parse command
            if command == "reserve":
                self.reserve()
            elif command == "cancel":
                self.cancel()
            elif command == "list_reservations":
                self.list_reservations()
            elif command == "list_transactions":
                self.list_transactions()
            elif command == "customer_reservations":
                self.customer_reservations()
            elif command == "customer_transactions":
                self.customer_transactions()
            elif command == "add_funds":
                self.add_funds()
            elif command == "edit_reservation":
                self.edit_reservation()
            ## ** Facility manager restricted ** ##
            elif command == "list_users":
                self.list_users()
            elif command == "list_holds":
                self.list_holds()
            elif command == "get_reservation":
                self.get_reservation()
            elif command == "create_client":
                self.create_client()
            elif command == "activate_client":
                self.client_activation(True)
            elif command == "deactivate_client":
                self.client_activation(False)
            elif command == "view_dashboard":
                self.view_dashboard()
            elif command == "allow_client_logins":
                self.allow_client_logins(True)
            elif command == "disallow_client_logins":
                self.allow_client_logins(False)
            elif command == "allow_add_funds":
                self.allow_add_funds(True)
            elif command == "disallow_add_funds":
                self.allow_add_funds(False)
            ## ** End of FM restricted ** ##
            elif command == "get_profile":
                self.get_profile()
            elif command == "edit_profile":
                self.edit_profile()
            elif command == "get_balance":
                self.get_balance()
            elif command == "logout":
                self.reset_user()
                self.user_login()
            elif command == "commands":
                self.list_commands()
            elif command == "exit" or command == "q":
                print("Exit the program")
                return
            else:
                print("Command not defined. Type 'commands' to see full list of supported commands.")

# Main function
if __name__ == '__main__':
    console = Console()
    console.run()
