# Main file to initialize bot from

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import flask
from FlaskConfig import mongobp
from flask_cors import CORS
import telegram
import logging
import os
import Database
from Scheduler import conv_handler_meetup
from Organiser import conv_handler_organiser
from BillSplitter import conv_handler_split
from HelperFunctions import flatten

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


# Algorithm for calculation
def check_common_timeslot(chat_id, meetup_id, data_cursor):
    part_timetable_dict = data_cursor['part_timetable_dict']
    all_timetable_list = list(part_timetable_dict.values())     # = [[[], [], []], ...]
    all_timetable_flat = []                                     # = [[1,2,3,4], [1,2,3,4], [1,2,3,4]]
    for timetable in all_timetable_list:
        all_timetable_flat.append(flatten(timetable))
    base_timetable = all_timetable_flat.pop()

    # Check common timeslots
    curr_timeslot = 0
    for timeslot in base_timetable:                 # timeslots are true/false values
        if timeslot:                                # if the current timeslot is True
            for timetable in all_timetable_flat:    # timetable = [1,2,3,4]
                if not timetable[curr_timeslot]:
                    base_timetable[curr_timeslot] = False
                    curr_timeslot += 1
                    break
        else:
            continue

    # Find appropriate time periods and store their indices
    event_timeframe_days = data_cursor['timeframe']
    event_timeframe_hours = event_timeframe_days * 24 - 1
    min_duration = data_cursor['duration']
    curr_duration = 0
    start_index = 0
    time_period_indices = []
    for index, timeslot in enumerate(base_timetable, start=0):
        if timeslot:
            if curr_duration == 0:
                start_index = index
            curr_duration += 1
            if index < event_timeframe_hours:
                if curr_duration >= min_duration and ~base_timetable[index + 1]:
                    time_period_indices.append([start_index, index + 1])
            else:
                if curr_duration >= min_duration:
                    time_period_indices.append([start_index, index + 1])
        else:
            curr_duration = 0

    # Map indices to correct time periods in date format
    start_date = data_cursor['date']
    start_date_zero = datetime.datetime(year=start_date.year, month=start_date.month, day=start_date.day)
    final_time_periods = []
    for period in time_period_indices:
        start_hour = start_date_zero + datetime.timedelta(hours=period[0])
        end_hour = start_date_zero + datetime.timedelta(hours=period[1])
        final_time_periods.append([start_hour, end_hour])

    # Format time periods to make them readable
    curr_timeslot_num = 1
    final_timeslot_str = ""
    for period in final_time_periods:
        start_str = '{0:%I:%M%p} on {0:%d}/{0:%m}/{0:%y}'.format(period[0])
        end_str = '{0:%I:%M%p} on {0:%d}/{0:%m}/{0:%y}'.format(period[1])
        next_slot_str = f"\n{curr_timeslot_num}) {start_str} -> {end_str}"
        final_timeslot_str = final_timeslot_str + next_slot_str

    bot = telegram.Bot(token=TOKEN)
    bot.send_message(chat_id=chat_id, text=
        f"These are your available timeslots sorted in chronological order."
        f"\n"
        f"Timeslots:"
        f"{final_timeslot_str}")
    print(final_timeslot_str)
    return base_timetable



# Bill Splitter
dispatcher.add_handler(conv_handler_split)

# Event Organiser
dispatcher.add_handler(conv_handler_organiser)


# Unknown Commands
def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)



# Start Flask app
app = flask.Flask(__name__)
#app.config["DEBUG"] = True
app.register_blueprint(mongobp)
CORS(app)

# Start/Stop Bot
if __name__ == "__main__":
    updater.start_polling()
    updater.idle()

