import telegram
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackContext
import logging
import Database
from math import sqrt

TITLE, DURATION, TIMEFRAME, PARTICIPANTS, NO_PARTICIPANTS = range(5)
logger = logging.getLogger(__name__)


def meetup(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Hi! Welcome to the Meetup Scheduler! Please input the name of your event. "
        "\n"
        "You can /cancel at any time to abort this process.")
    # context.bot.send_message(chat_id=update.effective_chat.id, text=
    #            "Hi! Welcome to the Meetup Scheduler! Please input the name of your event. " \
    #            "\n" \
    #            "You can /cancel at any time to abort this process.")
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
    # context.bot.send_message(chat_id=update.effective_chat.id, text=
    #         "Cool! How long will the event approximately last for? Please input a number to represent estimated "
    #         "duration in hours." \
    #         "\n" \
    #         "Again, you can /cancel at any time to abort this process.")
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
    # context.bot.send_message(chat_id=update.effective_chat.id, text=
    #         "In how many days will the event start? Please input a number to represent estimated duration in days." \
    #         "\n" \
    #         "Again, you can /cancel at any time to abort this process.")

    return TIMEFRAME


def timeframe(update: Update, context: CallbackContext) -> int:
    # user = update.message.from_user
    user_input = update.message.text
    context.user_data["meetup_timeframe"] = user_input

    # Database insertion of new meetup
    collection_meetups = Database.db.meetups
    title_temp: str = context.user_data.get("meetup_title")
    duration_temp: int = context.user_data.get("meetup_duration")
    timeframe_temp: str = context.user_data.get("meetup_timeframe")

    new_meetup_data = {
        'chat_id': update.effective_chat.id,
        'meetup_title': title_temp,
        'duration': int(duration_temp),
        'timeframe': timeframe_temp,
        'part_timetable_dict': None,
        'creator': update.effective_user.id,
        'state': False,
        'output time': None
    }
    collection_meetups.insert_one(new_meetup_data)

    # Store list of finalized participants
    participants_final = []
    context.user_data["participants_final"] = participants_final

    # Retrieve possible participants
    chat_id = update.effective_chat.id
    collection_users = Database.db.users
    mongo_participant_list = collection_users.find({'chat_id': chat_id})
    participant_list = []
    for participant in mongo_participant_list:
        participant_list.append(participant["user_tele_id"])
    context.user_data["participant_list"] = participant_list

    # Participant Keyboard
    num_of_participants = len(participant_list)
    n = sqrt(num_of_participants)
    reply_keyboard = [participant_list[i:i + n] for i in range(0, len(participant_list), n)]

    logger.info("Estimated time till event: %s", user_input)
    update.message.reply_text(
        "Please select the participants involved in this event.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, selective=True)
    )

    return PARTICIPANTS


def participants(update: Update, context: CallbackContext) -> int:
    # user = update.message.from_user
    chat_id = update.effective_chat.id
    user_input = update.message.text

    # Add participant entered previously
    participant_list = context.user_data.get("participant_list")
    participants_final = context.user_data.get("participants_final")
    participants_final.append(int(user_input))
    context.user_data["participants_final"] = participants_final

    # Participant Keyboard
    num_of_participants = len(participant_list)
    n = sqrt(num_of_participants)
    reply_keyboard = [participant_list[i:i + n] for i in range(0, len(participant_list), n)]

    logger.info("Participant list: %s", participant_list)
    update.message.reply_text(
        "Would you like to add anyone else? If not, please do /done",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, selective=True)
    )

    return PARTICIPANTS


def no_participants(update: Update, context: CallbackContext) -> int:
    # user = update.message.from_user
    print(context.user_data.get("participants_final"))
    logger.info("All participants have been added.")
    update.message.reply_text(
        "Awesome! All participants please input your available timeslots.")

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
        PARTICIPANTS: [MessageHandler(Filters.text & ~Filters.command, participants),
                       CommandHandler('done', no_participants)]
    },
    fallbacks=[CommandHandler('cancel', cancel), CommandHandler('unknown', unknown)]
)


