class Resource:
    def __init__(self, name, id, cost):
        self.name = name
        self.id = id
        self.cost = cost
        self.reservations = {}
