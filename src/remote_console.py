import requests, json, tabulate, csv, random

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
def print_list_as_table(dataset):
    if len(dataset) == 0:
        print("No data to display.")
        return
    header = dataset[0].keys()
    rows = [x.values() for x in dataset]
    print(tabulate.tabulate(rows, header, tablefmt='grid'))


## The Console class
class Console():
    def __init__(self):
        self.all_commands = ["hold", "list_holds", "list_users", "exit / q", "commands"]
        self.username = ""
        self.role = ""

    # Helper function for checking if the resource is unique or not
    def resource_is_unique(self, resource):
        return resource == "1.21 gigawatt lightning harvester" or resource == "high velocity crusher"

    ### *** USER/CLIENT FUNCTIONS *** ###
    # Function for reserving a resource
    def hold(self):
        # Request information from user
        resource = input("Resource (e.g. workshop/mini microvac etc.): ")
        customer = input("Username: ")
        reserver = self.username
        start_date = input("Start date (YYYY-MM-DD): ")
        start_time = input("Start time (HH:mm): ").strip()
        end_time = input("End time (HH:mm): ").strip()

        request = resource + "1" if not self.resource_is_unique(resource) else resource
        # Make post request to SSH host URL, and print the response
        hold_payload = {
            "username": "peter",
            "password": "pwdpeter",
            "client_name": customer,
            "request": request,
            "start_date": start_date,
            "start_time": start_time,
            "end_time": end_time
        }
        # Make request
        try:
            response = requests.post(f"{HOST}/hold", json=hold_payload)
            print("==> " + response.json().get("message"))
        except Exception:
            print_error(response)


    # Helper function for listing all holds.
    # *** Facility manager restricted ***
    def list_holds(self):
        # Make get request to localhost URL, and print the response
        try:
            response = requests.get(f"{HOST}/hold")
            print(f"\nAll holds:")
            dataset = add_ids_to_data(dict(response.json()))
            print_list_as_table(dataset)
        except Exception:
            print_error(response)

    # Helper function for listing all users.
    # *** Facility manager restricted ***
    def list_users(self):
        # Make get request to localhost URL, and print the response
        try:
            response = requests.get(f"{HOST}/users")
            print(f"\nAll users:")
            dataset = add_ids_to_data(dict(response.json()))
            print_list_as_table(dataset)
        except Exception:
            print_error(response)


    # Helper function for listing all supported commands
    def list_commands(self):
        commands = self.all_commands
        print("\nSupported commands:")
        for i in range(1, len(commands)+1):
            print(f"  ({i}) {commands[i-1]}")
        print("")


    # Function to run the console
    def run(self):
        print("###=== Welcome to the MPCS Inc. Reservation System! ===###")
        print("Our facility is located in Chicago, USA (CST/CDT). Business hours are:")
        print("Mon-Fri 09:00-18:00")
        print("Sat 10:00-16:00")
        # Verify the user's identity. If the user is new, create a username.
        #self.user_login()
        self.role = "facility manager"
        self.username = "faculty"
        # Run command line for console
        while True:
            # Get user command
            command = input(f"(Cmd: {self.username} - remote {self.role}) ")
            command = command.strip()
            # Parse command
            if command == "hold":
                self.hold()
            elif command == "list_holds":
                self.list_holds()
            elif command == "list_users":
                self.list_users()
            elif command == "commands":
                self.list_commands()
            elif command == "exit" or command == "q":
                return
            else:
                print("Command not defined. Type 'commands' to see full list of supported commands.")

# Main function
if __name__ == '__main__':
    console = Console()
    console.run()
