from pymongo import MongoClient
import os

# Replace with your MongoDB connection string
MONGO_URI = "mongodb+srv://aryaa3957:<xoCEka328OUMlOSn>@lettereditorcluster.zaexp.mongodb.net/?retryWrites=true&w=majority&appName=LetterEditorCluster"
client = MongoClient(MONGO_URI)

# Select the database
db = client["LetterEditorProject"]

# Collections
users_collection = db["users"]
letters_collection = db["letters"]

# Sample functions to interact with MongoDB
def add_user(user_data):
    users_collection.insert_one(user_data)

def get_user(email):
    return users_collection.find_one({"email": email})

def add_letter(letter_data):
    letters_collection.insert_one(letter_data)

def get_letters_by_user(user_email):
    return list(letters_collection.find({"user_email": user_email}))
