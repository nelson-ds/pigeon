from datetime import datetime


class UserDto:
    def __init__(self, phone_number, name=None, cities_ca=None, time_last_sms=datetime.now(),
                 sms_counter=0, deletion_date=datetime(2099, 12, 31, 23, 59, 59), _id=None):
        self.phone_number = phone_number
        self.name = name
        self.cities_ca = cities_ca
        self.time_last_sms = time_last_sms
        self.sms_counter = sms_counter
        self.deletion_date = deletion_date
        self._id = _id

    def __str__(self):
        return str(vars(self))
