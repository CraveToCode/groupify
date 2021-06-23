import json

import flask
import Database
from flask import request, jsonify
from bson.json_util import dumps
from bson.objectid import ObjectId

# Database
collection_users = Database.db.users
collection_details = Database.db.user_details
collection_meetups = Database.db.meetups

mongobp = flask.Blueprint('mongobp', __name__)


@mongobp.route('/<groupid>/<eventid>/<userid>/', methods=['GET', 'POST', 'PUT'])
def getData(groupid, eventid, userid):
    # returns event name, participant list, timetable for that user
    #return f"{groupid}, {eventid}, {userid}"
    cursor = collection_meetups.find_one({"chat_id": int(groupid), "_id": ObjectId(eventid)})
    print(cursor)
    response = jsonify(json.loads(dumps(cursor)))
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response





