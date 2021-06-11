from pymongo import MongoClient
import os

TOKEN = os.environ['MONGODBCONNECTION']
client = MongoClient(TOKEN)
# db = client.test

db = client.scheduler

