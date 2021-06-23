import pymongo
import telegram
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackContext, \
    CallbackQueryHandler
import logging
import Database
from math import sqrt, ceil
from HelperFunctions import overwrite


# Database
collection_users = Database.db.users
collection_details = Database.db.user_details
collection_meetups = Database.db.meetups

# States
TITLE, DURATION, TIMEFRAME, PARTICIPANTS, NO_PARTICIPANTS = range(5)

# Callback Data
DONE = 0

# Logging
logger = logging.getLogger(__name__)


# Program
def meetup(update: Update, context: CallbackContext) -> int:
    # Clear any user_data from other events in this chat
    context.user_data.clear()

    update.message.reply_text(
        "Hi! Welcome to the Meetup Scheduler! Please input the name of your event. "
        "\n"
        "You can /cancel at any time to abort this process.")
    return TITLE


def title(update: Update, context: CallbackContext) -> int:
    # user = update.message.from_user
    user_input = update.message.text
    context.user_data["meetup_title"] = user_input
    logger.info("Name of event: %s", user_input)
    reply_keyboard = [['1', '2', '3', '4', '5', '6'], ['7', '8', '9', '10', '11', '12'], ['13', '14', '15', '16',
                       '17', '18'], ['19', '20', '21', '22', '23', '24']]
    update.message.reply_text(
        "Cool! How long will the event approximately last for in hours? Please select an option in the keyboard below."
        "\n"
        "Again, you can /cancel at any time to abort this process.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True, selective=True),
    )
    return DURATION


def duration(update: Update, context: CallbackContext) -> int:
    # user = update.message.from_user
    user_input = update.message.text
    context.user_data["meetup_duration"] = user_input
    logger.info("Estimated event duration: %s hours", user_input)
    reply_keyboard = [['Today', 'Tomorrow', 'Within the next 3 days'], ['Within a week', 'Within 2 weeks'],
                      ['Within 3 weeks', 'Within a month']]
    update.message.reply_text(
        "Approximately when will the event be? Please select the estimated timeframe within which the event will "
        "occur."
        "\n"
        "Again, you can /cancel at any time to abort this process.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True, selective=True),
    )
    return TIMEFRAME


def timeframe(update: Update, context: CallbackContext) -> int:
    # user = update.message.from_user
    user_input = update.message.text

    # To store in database estimated timeframe in days
    map_to_number_of_days = {'Today': 1, 'Tomorrow': 2, 'Within the next 3 days': 3, 'Within a week': 7,
                             'Within 2 weeks': 14, 'Within 3 weeks': 21, 'Within a month': 28}
    context.user_data["meetup_timeframe"] = map_to_number_of_days[user_input]

    # Store list of finalized participants
    participants_final = []
    context.user_data["participants_final"] = participants_final

    # Retrieve possible participants and sort list alphabetically
    chat_id = update.effective_chat.id
    mongo_participant_pool = collection_users.find({'chat_id': chat_id})     # list of data cursors from mongodb
    participant_pool = []                                                    # list of potential usernames
    context.user_data["part_list"] = participant_pool                        # store list of username for database
    for participant in mongo_participant_pool:
        user_id = participant['user_tele_id']
        username = collection_details.find_one({'user_tele_id': user_id})['username']
        participant_pool.append(username)
    participant_pool.sort()

    # Participant Keyboard
    num_of_participants = len(participant_pool)
    n: int = ceil(sqrt(num_of_participants))
    participant_pool_keyboard = list(map(lambda x: InlineKeyboardButton(x,  callback_data=f"button:{x}"),
                                         participant_pool))
    reply_keyboard = [participant_pool_keyboard[i:i + n] for i in range(0, num_of_participants, n)]
    reply_keyboard.append([InlineKeyboardButton("DONE", callback_data=str(DONE))])
    context.user_data["participant_keyboard"] = reply_keyboard

    logger.info("Estimated time till event: %s", user_input)

    # Add cross emojis to participant_pool and store it
    participant_pool = list(map(lambda x: x + " \U0000274c", participant_pool))
    context.user_data["participant_pool_emoji"] = participant_pool

    participant_pool_listed = '\n'.join(participant_pool)  # stringify name list
    update.message.reply_text(
        f"Please select the participants involved in this event."
        f"\nYou can tap the same person again to remove them."
        f"\nSelect DONE if you are done selecting participants."
        f"\nAgain, you can /cancel at any time to abort this process."
        f"\n \n"
        f"Participant List: "
        f"\n{participant_pool_listed}",
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )

    return PARTICIPANTS


def participants(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    user_input = query.data.split(':')[1]

    # Participant Keyboard
    reply_keyboard = context.user_data.get("participant_keyboard")

    # Add participant entered previously
    participant_pool = context.user_data.get("participant_pool_emoji")
    participants_final = context.user_data.get("participants_final")
    value_unlisted = user_input + " \U0000274c"                                # user input with cross
    value_listed = user_input + " \U00002714"                                  # user input with check
    if user_input not in participants_final:
        participants_final.append(user_input)                                                   # add user to final list
        participant_pool = overwrite(participant_pool, value_unlisted, value_listed)            # add check emoji
        context.user_data["participant_pool_emoji"] = participant_pool                          # save new name list
        participant_pool_listed = '\n'.join(participant_pool)                                   # stringify name list
        query.edit_message_text(
            text=f"{user_input} has been added."
                 f"\nWould you like to add/remove anyone else? If not, please select DONE."
                 f"\n \n"
                 f"Participant list:"
                 f"\n{participant_pool_listed}",
            reply_markup=InlineKeyboardMarkup(reply_keyboard)
        )
    else:
        participants_final.remove(user_input)                                                     # remove user
        participant_pool = overwrite(participant_pool, value_listed, value_unlisted)              # add cross emoji
        context.user_data["participant_pool_emoji"] = participant_pool                            # save new name list
        participant_pool_listed = '\n'.join(participant_pool)                                     # stringify name list
        query.edit_message_text(
            text=f"{user_input} has been removed."
                 f"\nWould you like to add/remove anyone else? If not, please select DONE."
                 f"\n \n"
                 f"Participant list:"
                 f"\n{participant_pool_listed}",
            reply_markup=InlineKeyboardMarkup(reply_keyboard)
        )

    context.user_data["participants_final"] = participants_final
    logger.info("Participant list: %s", participants_final)

    return PARTICIPANTS


def no_participants(update: Update, context: CallbackContext) -> int:
    # user = update.message.from_user
    query = update.callback_query
    query.answer()
    participants_final = context.user_data.get("participants_final")
    logger.info("All participants have been added. Final list: %s", participants_final)
    query.edit_message_text(text="Awesome! All participants please input your available timeslots.")

    # Database insertion of new meetup (to be brought to last state)
    title_temp: str = context.user_data.get("meetup_title")
    duration_temp: int = context.user_data.get("meetup_duration")
    timeframe_temp: str = context.user_data.get("meetup_timeframe")
    part_list = context.user_data.get("part_list")

    new_meetup_data = {
        'chat_id': update.effective_chat.id,
        'meetup_title': title_temp,
        'duration': int(duration_temp),
        'timeframe': timeframe_temp,
        'part_list': part_list,
        'part_timetable_dict': None,
        'creator': update.effective_user.id,
        'state': False,
        'output time': None,
        'date': update.message.date
    }
    collection_meetups.insert_one(new_meetup_data)

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Meetup Scheduler has successfully terminated.")
    return ConversationHandler.END


def unknown(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Sorry, I did not understand that command.")


conv_handler_meetup = ConversationHandler(
    entry_points=[CommandHandler('meetup', meetup)],
    states={
        TITLE: [MessageHandler(Filters.text & ~Filters.command, title)],
        DURATION: [MessageHandler(Filters.text & ~Filters.command, duration)],
        TIMEFRAME: [MessageHandler(Filters.text & ~Filters.command, timeframe)],
        PARTICIPANTS: [CallbackQueryHandler(participants, pattern="^button"),
                       CallbackQueryHandler(no_participants, pattern='^' + str(DONE) + '$')
                       ]
    },
    fallbacks=[CommandHandler('cancel', cancel), CommandHandler('unknown', unknown)]
)


