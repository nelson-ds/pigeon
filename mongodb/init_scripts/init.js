db.users.createIndex({ phone_number: 1 }, { unique: true });
db.users.createIndex({ deletion_date: 1}, {expireAfterSeconds: 0})