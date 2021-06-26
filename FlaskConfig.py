import json

import flask
import Database
from flask import request, jsonify, make_response
from bson.json_util import dumps
from bson.objectid import ObjectId

import Scheduler
from Scheduler import check_common_timeslot

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

@mongobp.route('/<groupid>/<eventid>/<userid>/', methods=['PUT', "OPTIONS"])
def updateData(groupid, eventid, userid):
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response
    else:
        req = json.loads(request.data)
        print(req)
        chat_id = int(groupid)
        meetup_id = ObjectId(eventid)
        collection_meetups.update_one({"chat_id": chat_id, "_id": meetup_id},
                                      { "$set": { f"part_timetable_dict.{userid}": req}})

        # Check if all users have input their available timeslots
        data_cursor = collection_meetups.find_one({'chat_id': chat_id, "_id": meetup_id})
        part_id_left_to_fill = data_cursor['part_id_left_to_fill']
        if len(part_id_left_to_fill) == 0:
            Scheduler.check_common_timeslot(chat_id, meetup_id, data_cursor)
        else:
            part_id_left_to_fill.remove(int(userid))
            collection_meetups.update_one({'chat_id': chat_id, '_id': meetup_id},
                                          {'$set': {'part_id_left_to_fill': part_id_left_to_fill}})
            if len(part_id_left_to_fill) == 0:
                Scheduler.check_common_timeslot(chat_id, meetup_id, data_cursor)

        response = make_response(jsonify({"message": "Timeslots updated"}), 200)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response






