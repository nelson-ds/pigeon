class UserDto:
    def __init__(self, phone_number, name=None, cities_ca=None, _id=None):
        self._id = _id
        self.phone_number = phone_number
        self.name = name
        self.cities_ca = cities_ca

    def __str__(self):
        return str(vars(self))
