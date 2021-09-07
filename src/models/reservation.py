class Reservation:
    def __init__(self, serial_num, resource, customer, date_time, cost):
        self.serial_num = serial_num
        self.resource = resource
        self.customer = customer
        self.reserver = reserver
        # Start date & time for 30-minute reservation (customer can only reserve one 30-minute block at a time)
        self.date_time = date_time
        self.cost = cost