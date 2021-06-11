from pymongo import MongoClient
import os

MONGO_CONNECTION_URL = os.environ['MONGODBCONNECTION']
client = MongoClient(MONGO_CONNECTION_URL)
# db = client.test

db = client.scheduler

