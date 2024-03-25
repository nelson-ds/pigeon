class UsersDto:
    def __init__(self, name, phone_number, _id=None):
        self._id = _id
        self.phone_number = phone_number
        self.name = name

    def __str__(self):
        return str(vars(self))
