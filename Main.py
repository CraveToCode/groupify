# Main file to initialize bot from

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import flask
from Flask import mongobp
import telegram
import logging
import os
import Database
from Scheduler import conv_handler_meetup
from Organiser import conv_handler_organiser
from BillSplitter import conv_handler_split

# API Token
TOKEN = os.environ['API_KEY']
PORT = int(os.environ.get('PORT', '8443'))

updater = Updater(token=TOKEN, use_context=True)

dispatcher = updater.dispatcher

# Logging Module
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Database
collection_users = Database.db.users
collection_details = Database.db.user_details


# Start Command
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=
    f"Hi {update.effective_user.first_name}! I'm GroupifyBot! How can I help you?"
    "\n"
    "You may type /help for more information.")


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


# Join Command
def join(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user_username = update.message.from_user.username

    # Add user to users database
    new_user = {
        'user_tele_id': user_id,
        'chat_id': chat_id
    }
    collection_users.replace_one({'user_tele_id': user_id, 'chat_id': chat_id}, new_user, upsert=True)

    # Add user to user_details database  # TODO (need to update channel_count properly)
    existing_num_of_entries = collection_details.count_documents({'user_tele_id': user_id})
    if existing_num_of_entries == 0:
        new_detail = {
            'user_tele_id': user_id,
            'username': user_username,
            'channel_count': 1
        }
        collection_details.insert_one(new_detail)
    else:
        collection_details.update({'user_tele_id': user_id}, {'$inc': {'channel_count': 1}})

    update.message.reply_text(
        "Great! Events created by users will have you listed as a potential participant from now on.")


join_handler = CommandHandler('join', join)
dispatcher.add_handler(join_handler)


# Leave Command
def leave(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    collection_users.find_one_and_delete({'user_tele_id': user_id, 'chat_id': chat_id})
    # TODO need to implement deletion from collection_details

    update.message.reply_text(
        "You have been removed from being chosen as a potential participant in future events that are created"
        "in this channel.")


leave_handler = CommandHandler('leave', leave)
dispatcher.add_handler(leave_handler)


# Help Command
help_msg = "GroupifyBot supports 3 features: Meetup Scheduler, Bill Splitter, Event Organiser\." \
           "\n \n" \
           "*Important*: Please type */join* if you wish to be considered as a potential participant of the events " \
           "created through this bot\. You have the option of doing */leave* afterwards to stop being" \
           "considered as a participant\." \
           "\n \n" \
           "Type */meetup* to start a new meetup event\. This will output the best time for all your friends to " \
           "meetup, along with the best location\." \
           "\n \n" \
           "Type */split* to start a new bill to be split\. This will output the exact amount each person will have " \
           "to pay you\." \
           "\n \n" \
           "Type */organise* to start a new event organiser\. The event organiser will help you plan your day and " \
           "display the activities for the day chronologically\. It even allows participants to propose activities " \
           "that others can then bid on\."


def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_msg, parse_mode=telegram.ParseMode.MARKDOWN_V2)


help_handler = CommandHandler('help', help)
dispatcher.add_handler(help_handler)


# Meetup Scheduler
dispatcher.add_handler(conv_handler_meetup)

# Bill Splitter
dispatcher.add_handler(conv_handler_split)

# Event Organiser
dispatcher.add_handler(conv_handler_organiser)


# Unknown Commands
def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)


# Start/Stop Bot
'''updater.start_webhook(listen="0.0.0.0",
                      port=PORT,
                      url_path=TOKEN,
                      webhook_url="https://groupify-orbital.herokuapp.com/" + TOKEN)'''
#updater.idle()

# Start Flask app
app = flask.Flask(__name__)
app.config["DEBUG"] = True

#@app.route('/', methods=['GET'])
#def home():
 #   return '''<h1>Distant Reading Archive</h1>
#<p>A prototype API for distant reading of science fiction novels.</p>'''

@app.route('/<groupid>/<eventid>/<userid>/', methods=['GET', 'POST', 'PUT'])
def getData(groupid, eventid, userid):
    # returns event name, participant list, timetable for that user
    return "<h1>test</h1>"

#app.register_blueprint(mongobp)

app.run(host="https://groupify-orbital.herokuapp.com/", port=PORT)

