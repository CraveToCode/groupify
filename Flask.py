import flask
import Database
from flask import request, jsonify

# Database
collection_users = Database.db.users
collection_details = Database.db.user_details
collection_meetups = Database.db.meetups

mongobp = flask.Blueprint('mongobp', __name__)


@mongobp.route('/<groupid>/<eventid>/<userid>/', methods=['GET', 'POST', 'PUT'])
def getData(groupid, eventid, userid):
    # returns event name, participant list, timetable for that user
    #return f"{groupid}, {eventid}, {userid}"
    test = collection_meetups.find({"chat_id": groupid})
    test2 = jsonify(test)
    print(test)
    print(test2)
    return test2




