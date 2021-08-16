import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackContext, \
    CallbackQueryHandler
import logging
import Database
from math import sqrt, ceil
from HelperFunctions import overwrite, flatten
import datetime
import os

# API Token
TOKEN = os.environ['API_KEY']

# Database
collection_users = Database.db.users
collection_details = Database.db.user_details
collection_meetups = Database.db.meetups

# States
TITLE, DURATION, TIMEFRAME, PARTICIPANTS, NO_PARTICIPANTS, POLL_CHOICE = range(6)

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
    user_input = update.message.text
    context.user_data["meetup_title"] = user_input              # store title for database
    context.user_data["date"] = update.message.date             # store date for database
    logger.info("Name of event: %s", user_input)

    hours_list = [str(i) for i in range(1, 25)]
    hours_keyboard = list(map(lambda x: InlineKeyboardButton(x,  callback_data=f"hours:{x}"), hours_list))
    reply_keyboard = [hours_keyboard[i: i + 6] for i in range(0, 24, 6)]

    update.message.reply_text(
        "Cool! How long will the event approximately last for in hours? Please select an option in the keyboard below."
        "\n"
        "Again, you can /cancel at any time to abort this process.",
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )

    return DURATION


def duration(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    user_input = query.data.split(':')[1]
    context.user_data["meetup_duration"] = user_input
    logger.info("Estimated event duration: %s hours", user_input)
    timeframe_list = [['Today', 'Tomorrow', 'Next 3 days'], ['Within a week', 'Within 2 weeks'],
                      ['Within 3 weeks', 'Within a month']]
    reply_keyboard = []
    for row in timeframe_list:
        reply_keyboard.append(list(map(lambda x: InlineKeyboardButton(x,  callback_data=f"time:{x}"), row)))

    context.bot.send_message(chat_id=update.effective_chat.id, text=
        "Approximately when will the event be? Please select the estimated timeframe within which the event will "
        "occur."
        "\n"
        "Again, you can /cancel at any time to abort this process.",
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )
    return TIMEFRAME


def timeframe(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    user_input = query.data.split(':')[1]

    # To store in database estimated timeframe in days
    map_to_number_of_days = {'Today': 1, 'By Tomorrow': 2, 'Next 3 days': 3, 'Within a week': 7,
                             'Within 2 weeks': 14, 'Within 3 weeks': 21, 'Within a month': 28}
    context.user_data["meetup_timeframe"] = map_to_number_of_days[user_input]

    # Store list of finalized participants
    participants_final = []
    context.user_data["participants_final"] = participants_final

    # Retrieve possible participants and sort list alphabetically
    chat_id = update.effective_chat.id
    mongo_participant_pool = collection_users.find({'chat_id': chat_id})     # list of data cursors from mongodb
    participant_pool = []                                                    # list of potential usernames
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
    participant_pool = list(map(lambda x: x + " \U0001F534", participant_pool))
    context.user_data["participant_pool"] = participant_pool

    participant_pool_listed = '\n'.join(participant_pool)  # stringify name list
    context.bot.send_message(chat_id=update.effective_chat.id, text=
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
    participant_pool = context.user_data.get("participant_pool")
    participants_final = context.user_data.get("participants_final")
    value_unlisted = user_input + " \U0001F534"                                # user input with cross
    value_listed = user_input + " \U0001F7E2"                                  # user input with check
    if user_input not in participants_final:
        participants_final.append(user_input)                                                   # add user to final list
        participant_pool = overwrite(participant_pool, value_unlisted, value_listed)            # add check emoji
        context.user_data["participant_pool"] = participant_pool                                # save new name list
        participant_pool_listed = '\n'.join(participant_pool)                                   # stringify name list
        query.edit_message_text(
            text=f"<b>{user_input}</b> has been <b>added</b>."
                 f"\nWould you like to add/remove anyone else? If not, please select DONE."
                 f"\n \n"
                 f"Participant list:"
                 f"\n{participant_pool_listed}",
            reply_markup=InlineKeyboardMarkup(reply_keyboard),
            parse_mode=telegram.ParseMode.HTML
        )
    else:
        participants_final.remove(user_input)                                                     # remove user
        participant_pool = overwrite(participant_pool, value_listed, value_unlisted)              # add cross emoji
        context.user_data["participant_pool"] = participant_pool                                  # save new name list
        participant_pool_listed = '\n'.join(participant_pool)                                     # stringify name list
        query.edit_message_text(
            text=f"<b>{user_input}</b> has been <b>removed</b>."
                 f"\nWould you like to add/remove anyone else? If not, please select DONE."
                 f"\n \n"
                 f"Participant list:"
                 f"\n{participant_pool_listed}",
            reply_markup=InlineKeyboardMarkup(reply_keyboard),
            parse_mode=telegram.ParseMode.HTML
        )

    context.user_data["participants_final"] = participants_final
    logger.info("Participant list: %s", participants_final)

    return PARTICIPANTS


def no_participants(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    participants_final = context.user_data.get("participants_final")
    logger.info("All participants have been added. Final list: %s", participants_final)

    reply_keyboard = [[InlineKeyboardButton('Generate Poll', callback_data="poll: yes"),
                      InlineKeyboardButton('No Poll', callback_data="poll: no")]]

    context.bot.send_message(chat_id=update.effective_chat.id, text=
        "Great!"
        "\nWould you like to receive an auto-generated poll, if multiple timeslots are available, in order to choose"
        " the most favourable timeslot?",
        reply_markup=InlineKeyboardMarkup(reply_keyboard))

    return POLL_CHOICE


def poll_choice(update, context):
    query = update.callback_query
    query.answer()
    user_input = query.data
    poll_temp = None
    if user_input == "poll: yes":
        poll_temp = True
        logger.info("User has opted for a poll.")

    else:
        poll_temp = False
        logger.info("User has opted out of a poll.")

    # Database insertion of new meetup
    chat_id_temp: int = update.effective_chat.id
    title_temp: str = context.user_data.get("meetup_title")
    duration_temp: int = context.user_data.get("meetup_duration")
    timeframe_temp: int = context.user_data.get("meetup_timeframe")
    part_timetable_dict_value = [[False] * 24] * timeframe_temp
    participants_final_temp = context.user_data.get("participants_final")
    part_timetable_dict_temp = {}
    participant_id_list_temp = []
    for participant in participants_final_temp:
        participant_id = collection_details.find_one({'username': participant})['user_tele_id']
        participant_id_list_temp.append(participant_id)               # List of participant ids for sending links in pm
        part_timetable_dict_temp[str(participant_id)] = part_timetable_dict_value.copy()
    date_temp = context.user_data.get("date")   # datetime.datetime object

    new_meetup_data = {
        'chat_id': chat_id_temp,
        'meetup_title': title_temp,
        'duration': int(duration_temp),
        'timeframe': timeframe_temp,
        'part_list': participants_final_temp,
        'part_list_id': participant_id_list_temp,
        'part_id_left_to_fill': participant_id_list_temp.copy(),
        'part_timetable_dict': part_timetable_dict_temp,
        'poll': poll_temp,
        'creator': update.effective_user.id,
        'state': False,
        'output_time': None,
        'poll_output': None,
        'date': date_temp
    }
    data = collection_meetups.insert_one(new_meetup_data)

    # Send link to each participant to allow them to fill in timeslots
    meetup_id = data.inserted_id
    for participant_id in participant_id_list_temp:
        context.bot.send_message(chat_id=participant_id, text=
        f"Hi! Please indicate your available timeslots for the event '{title_temp}' in the link below."
        f"\n"
        f"\nLink: "
        f"\nhttps://groupify-site.vercel.app/{chat_id_temp}/{meetup_id}/{participant_id}/")

    context.bot.send_message(chat_id=update.effective_chat.id, text=
        "Awesome!"
        "\nEach participant will be sent a link immediately. Please indicate your available timeslots "
        "through that link")

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
        TITLE: [MessageHandler(Filters.regex(pattern='^' + '([a-zA-Z0-9\-()])+' + '$') & ~Filters.command, title)],
        DURATION: [CallbackQueryHandler(duration, pattern = "^hours")],
        TIMEFRAME: [CallbackQueryHandler(timeframe, pattern = "^time")],
        PARTICIPANTS: [CallbackQueryHandler(participants, pattern="^button"),
                       CallbackQueryHandler(no_participants, pattern='^' + str(DONE) + '$')
                       ],
        POLL_CHOICE: [CallbackQueryHandler(poll_choice, pattern='^poll')]
    },
    fallbacks=[CommandHandler('cancel', cancel), CommandHandler('unknown', unknown)]
)


def check_common_timeslot(chat_id, meetup_id, data_cursor):
    part_timetable_dict = data_cursor['part_timetable_dict']
    all_timetable_list = list(part_timetable_dict.values())     # = [[[], [], []], ...]
    all_timetable_flat = []                                     # = [[1,2,3,4], [1,2,3,4], [1,2,3,4]]
    for timetable in all_timetable_list:
        all_timetable_flat.append(flatten(timetable))
    base_timetable = all_timetable_flat.pop(0)

    # Check common timeslots
    curr_timeslot = 0
    for timeslot in base_timetable:                 # timeslots are true/false values
        if timeslot:                                # if the current timeslot is True
            for timetable in all_timetable_flat:    # timetable = [1,2,3,4]
                if not timetable[curr_timeslot]:
                    base_timetable[curr_timeslot] = False
                    break
        curr_timeslot += 1

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
                if curr_duration >= min_duration and (not base_timetable[index + 1]):
                    time_period_indices.append([start_index, index + 1])
            else:
                if curr_duration >= min_duration:
                    time_period_indices.append([start_index, index + 1])
        else:
            curr_duration = 0

    # Check if there are any common time periods first
    bot = telegram.Bot(token=TOKEN)
    if len(time_period_indices) == 0:
        bot.send_message(chat_id=chat_id, text=
        "There are no available timeslots.")
    else:
        # Map indices to correct time periods in date format
        start_date = data_cursor['date']
        start_date_local = start_date + datetime.timedelta(hours=8)         # Convert to local timezone
        start_date_zero = datetime.datetime(year=start_date_local.year, month=start_date_local.month,
                                            day=start_date_local.day)
        final_time_periods = []
        for period in time_period_indices:
            start_hour = start_date_zero + datetime.timedelta(hours=period[0])
            end_hour = start_date_zero + datetime.timedelta(hours=period[1])
            final_time_periods.append([start_hour, end_hour])

        # Format time periods to make them readable
        curr_timeslot_num = 1
        final_timeslot_str = ""
        poll_options = []
        for period in final_time_periods:
            start_str = '{0:%I:%M%p} on {0:%d}/{0:%m}/{0:%y}'.format(period[0])
            end_str = '{0:%I:%M%p} on {0:%d}/{0:%m}/{0:%y}'.format(period[1])
            next_slot_str = f"\n{curr_timeslot_num}) {start_str} -> {end_str}"
            poll_options.append(f"{start_str} -> {end_str}")
            final_timeslot_str = final_timeslot_str + next_slot_str
            curr_timeslot_num += 1

        meetup_title = data_cursor['meetup_title']
        bot.send_message(chat_id=chat_id, text=
            f"These are your available timeslots for the meetup '{meetup_title}', sorted in chronological order."
            f"\n"
            f"<b>Timeslots:</b>"
            f"{final_timeslot_str}",
            parse_mode=telegram.ParseMode.HTML)

        # Send poll if there are more than one available timeslots, and if user has opted for a poll
        if data_cursor['poll'] and len(poll_options) > 1:
            bot.send_poll(chat_id=chat_id,
                          question="Which timeslot is most convenient for you?",
                          options=poll_options,
                          allows_multiple_answers=False)

    return base_timetable
