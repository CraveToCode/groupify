from pymongo import MongoClient
import os

MONGO_CONNECTION_URL = os.environ['MONGODBCONNECTION']
client = MongoClient(MONGO_CONNECTION_URL)

# For testing connection
# db = client.test

db = client.scheduler

