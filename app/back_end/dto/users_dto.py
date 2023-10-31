class UsersDto:
    def __init__(self, name, phone_number, _id=None):
        self.name = name
        self.phone_number = phone_number
        self._id = _id

    def __str__(self):
        return str(vars(self))
