use pigeon;
db.users.createIndex({ phone_number: 1 }, { unique: true });