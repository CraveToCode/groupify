import json

import flask
import Database
from flask import request, jsonify, make_response
from bson.json_util import dumps
from bson.objectid import ObjectId

# Database
collection_users = Database.db.users
collection_details = Database.db.user_details
collection_meetups = Database.db.meetups

mongobp = flask.Blueprint('mongobp', __name__)


@mongobp.route('/<groupid>/<eventid>/<userid>/', methods=['GET'])
def getData(groupid, eventid, userid):
    cursor = collection_meetups.find_one({"chat_id": int(groupid), "_id": ObjectId(eventid)})
    print(cursor)
    response = jsonify(json.loads(dumps(cursor)))
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@mongobp.route('/<groupid>/<eventid>/<userid>/', methods=['PUT'])
def updateData(groupid, eventid, userid):
    req = request.data
    collection_meetups.update_one({"chat_id": int(groupid), "_id": ObjectId(eventid)},
                                  { "$set": { f"part_timetable_dict.{userid}": req}})
    res = make_response(jsonify({"message": "Timeslots updated"}), 200)
    return res





