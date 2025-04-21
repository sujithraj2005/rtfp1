from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["login_db"]
users_collection = db["users"]

# Insert a test user
users_collection.insert_one({
    "username": "admin",
    "password": "admin123"
})

print("✅ User inserted!")
