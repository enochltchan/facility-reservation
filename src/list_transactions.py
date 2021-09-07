import requests, json

LOCALHOST = "http://127.0.0.1:8000"

# Helper function for printing error messages
def print_error(response):
    try:
        print("==> Request failed: " + response.json()["detail"])
    except Exception:
        print("==> Unknown error: Response missing detail.")

# List all transactions in the system
def list_transactions():
    # Request information from user
    start_date_string = input("Start date and time (MM-DD-YYYY): ")
    end_date_string = input("End date and time (MM-DD-YYYY): ")

    # Make get request to localhost URL, and print the response
    parameters = {"start_date_string": start_date_string, "end_date_string": end_date_string}
    try:
        response = requests.get(f"{LOCALHOST}/transactions", params=parameters)
        if response.json().get('detail') is not None:
            print_error(response)
        else:
            print(f"\nTransactions from {start_date_string} to {end_date_string}:")
            for id, txn in response.json().items():
                print(f"  (ID: {id}) {txn}")
    except Exception:
        print_error(response)

# Main function
# Script for course staff, separate from application
if __name__ == '__main__':
    list_transactions()
