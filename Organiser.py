import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackContext, \
    CallbackQueryHandler, PollAnswerHandler
import logging
import Database
from math import sqrt, ceil
from HelperFunctions import overwrite
from re import compile
import datetime

# Database
collection_users = Database.db.users
collection_details = Database.db.user_details
collection_organisers = Database.db.organisers
collection_organiser_polls = Database.db.organiser_polls

# States
ORGANISER_TITLE, DATE, PARTICIPANTS, EVENT_TITLE, START_HOUR, START_MINUTE, END_HOUR, \
    END_MINUTE = range(8)

# Callback Data
DONE = 0

# Regex
DD_MM_YYYY = compile(r"(?:(?:31(\/|-|\.)(?:0?[13578]|1[02]))\1|(?:(?:29|30)(\/|-|\.)(?:0?[13-9]|1[0-2])\2))"
                     r"(?:(?:1[6-9]|[2-9]\d)?\d{2})$|^(?:29(\/|-|\.)0?2\3(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|"
                     r"[13579][26])|(?:(?:16|[2468][048]|[3579][26])00))))$|^(?:0?[1-9]|"
                     r"1\d|2[0-8])(\/|-|\.)(?:(?:0?[1-9])|(?:1[0-2]))\4(?:(?:1[6-9]|[2-9]\d)?\d{2})").pattern

# Logging
logger = logging.getLogger(__name__)


# Program
def organise(update, context) -> int:
    update.message.reply_text(
        "Hi! Welcome to the Event Organiser! Please input a name for your organiser. "
        "\n"
        "You can /cancel at any time to abort this process.")
    return ORGANISER_TITLE


def organiser_title(update, context) -> int:
    user_input = update.message.text
    matches = collection_organisers.find_one({"organiser_title": user_input, "chat_id": update.effective_chat.id})
    if matches is None:
        context.user_data["organiser_title"] = user_input              # store title for database
        context.user_data["date"] = update.message.date             # store date for database

        update.message.reply_text(
            "Please input the date for your events in your organiser, in the format DD/MM/YYYY."
        )

        logger.info("Name of organiser: %s", user_input)

        return DATE

    else:
        update.message.reply_text(
            "There already exists an organiser with that name in this channel. Please enter another name."
        )

        return ORGANISER_TITLE


def date(update, context) -> int:
    user_input = update.message.text
    context.user_data["organiser_date"] = user_input              # store organiser_date for database

    # Log
    logger.info("Date of event: %s", user_input)

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

    # Add cross emojis to participant_pool and store it
    participant_pool = list(map(lambda x: x + " \U0001F534", participant_pool))
    context.user_data["participant_pool"] = participant_pool

    participant_pool_listed = '\n'.join(participant_pool)  # stringify name list
    context.bot.send_message(chat_id=update.effective_chat.id, text=
        f"Great! Please select the participants involved in this event."
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


def no_participants(update, context) -> int:
    query = update.callback_query
    query.answer()
    participants_final = context.user_data.get("participants_final")
    logger.info("All participants have been added. Final list: %s", participants_final)

    # Database insertion of new event
    title_temp = context.user_data.get("organiser_title")
    organiser_date_temp = context.user_data.get("organiser_date")
    date_temp = context.user_data.get("date")               # datetime.datetime object

    new_organiser_data = {
        'chat_id': update.effective_chat.id,
        'organiser_title': title_temp,
        'organiser_date': organiser_date_temp,
        'part_list': participants_final,
        'events': [],
        'creator': update.effective_user.id,
        'date': date_temp
    }

    collection_organisers.insert_one(new_organiser_data)

    context.bot.send_message(chat_id=update.effective_chat.id, text=
        f"All participants recorded!"
        f"\nFrom now on, you or any of the recorded participants can do <b>/add {title_temp}</b> in this channel to "
        f"propose an event to be added to this organiser."
        f"\n \n"
        f"You can also do <b>/retrieve {title_temp}</b> in this channel to retrieve the organised event list for "
        f"this particular event organiser",
        parse_mode=telegram.ParseMode.HTML
    )

    return ConversationHandler.END


def cancel(update, context):
    update.message.reply_text("Event Organiser has successfully terminated.")
    return ConversationHandler.END


def unknown(update, context):
    update.message.reply_text("Sorry, I did not understand that command.")


conv_handler_organiser = ConversationHandler(
    entry_points=[CommandHandler('organise', organise)],
    states={
        ORGANISER_TITLE: [MessageHandler(Filters.regex(pattern='^' + '([a-zA-Z0-9\-()])+' + '$') & ~Filters.command,
                                         organiser_title)],
        DATE: [MessageHandler(Filters.regex(pattern='^' + DD_MM_YYYY + '$') & ~Filters.command, date)],
        PARTICIPANTS: [CallbackQueryHandler(participants, pattern="^button"),
                       CallbackQueryHandler(no_participants, pattern='^' + str(DONE) + '$')
                       ]
    },
    fallbacks=[CommandHandler('cancel', cancel), CommandHandler('unknown', unknown)]
)


def add(update, context) -> int:
    if len(context.args) == 0:
        update.message.reply_text(
            "Please indicate the title of the event organiser, in the form <b>/add organiser_name</b>."
            "\n"
            "\ne.g. /add holiday",
            parse_mode=telegram.ParseMode.HTML
        )
        return ConversationHandler.END
    else:
        org_title = str(context.args[0])
        data_cursor = collection_organisers.find_one({"organiser_title": org_title, "chat_id": update.effective_chat.id})
        if data_cursor is None:
            update.message.reply_text(
                "There is no event organiser with that particular title. Please enter a valid title."
            )
            return ConversationHandler.END
        else:
            if update.effective_user.username in data_cursor['part_list']:
                context.user_data["data_cursor"] = data_cursor
                update.message.reply_text(
                    f"Enter the name of your event to be added to the organiser titled <b>{org_title}</b>.",
                    parse_mode=telegram.ParseMode.HTML
                )
                return EVENT_TITLE
            else:
                update.message.reply_text(
                    f"You are not a participant of the events in the organiser titled <b>{org_title}</b>.",
                    parse_mode=telegram.ParseMode.HTML
                )
                return ConversationHandler.END


def event_title(update, context) -> int:
    user_input = update.message.text
    context.user_data["event_title"] = user_input

    # Keyboard for hour selection
    hours_list = [list(range(0, 6)), list(range(6, 12)), list(range(12, 18)), list(range(18, 24))]
    reply_keyboard = []
    for hour_period in hours_list:
        reply_keyboard.append(list(map(lambda x: InlineKeyboardButton(str(x),  callback_data=f"shour:{x}"),
                                       hour_period)))

    context.bot.send_message(chat_id=update.effective_chat.id, text=
        "You will now be prompted to enter the start and end time for the event."
        "Please enter the start hour!",
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )
    return START_HOUR


def start_hour(update, context) -> int:
    query = update.callback_query
    query.answer()
    user_input = query.data.split(':')[1]
    context.user_data["s_hour"] = int(user_input)

    # Keyboard for minutes selection
    minutes_list = [list(range(0, 6)), list(range(6, 12)), list(range(12, 18)), list(range(18, 24)),
                    list(range(24, 30)), list(range(30, 36)), list(range(36, 42)), list(range(42, 48)),
                    list(range(48, 54)), list(range(54, 60))]
    reply_keyboard = []
    for minute_period in minutes_list:
        reply_keyboard.append(list(map(lambda x: InlineKeyboardButton(str(x),  callback_data=f"smin:{x}"),
                                       minute_period)))

    query.edit_message_text(
        text="Please enter the start minute!",
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )

    return START_MINUTE


def start_minute(update, context) -> int:
    query = update.callback_query
    query.answer()
    user_input = query.data.split(':')[1]
    context.user_data["s_min"] = int(user_input)

    # Keyboard for minutes selection
    hours_list = [list(range(0, 6)), list(range(6, 12)), list(range(12, 18)), list(range(18, 24))]
    reply_keyboard = []
    for hour_period in hours_list:
        reply_keyboard.append(list(map(lambda x: InlineKeyboardButton(str(x),  callback_data=f"ehour:{x}"),
                                       hour_period)))
    query.edit_message_text(
        text="Please enter the end hour!",
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )

    return END_HOUR


def end_hour(update, context) -> int:
    query = update.callback_query
    query.answer()
    user_input = query.data.split(':')[1]
    context.user_data["e_hour"] = int(user_input)

    # Keyboard for minutes selection
    minutes_list = [list(range(0, 6)), list(range(6, 12)), list(range(12, 18)), list(range(18, 24)),
                    list(range(24, 30)), list(range(30, 36)), list(range(36, 42)), list(range(42, 48)),
                    list(range(48, 54)), list(range(54, 60))]
    reply_keyboard = []
    for minute_period in minutes_list:
        reply_keyboard.append(list(map(lambda x: InlineKeyboardButton(str(x), callback_data=f"emin:{x}"),
                                       minute_period)))

    query.edit_message_text(
        text="Please enter the end minute!",
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )

    return END_MINUTE


def end_minute(update, context) -> int:
    query = update.callback_query
    query.answer()
    user_input = query.data.split(':')[1]
    s_hour = context.user_data.get("s_hour")
    s_min = context.user_data.get("s_min")
    e_hour = context.user_data.get("e_hour")
    e_min = int(user_input)
    ev_title = context.user_data.get("event_title")
    data_cursor = context.user_data.get("data_cursor")
    org_title = data_cursor['organiser_title']

    # Format time
    organiser_date = data_cursor['organiser_date']
    split_date = organiser_date.split("/")
    int_date = list(map(lambda x: int(x), split_date))
    start_datetime = datetime.datetime(year=int_date[2], month=int_date[1], day=int_date[0],
                                       hour=int(s_hour), minute=int(s_min))
    end_datetime = datetime.datetime(year=int_date[2], month=int_date[1], day=int_date[0],
                                     hour=int(e_hour), minute=int(e_min))
    start_time_formatted = '{0:%I:%M%p}'.format(start_datetime)
    end_time_formatted = '{0:%I:%M%p}'.format(end_datetime)

    # Format participants
    part_list = data_cursor['part_list']
    space = ", "
    part_string = space.join(part_list)

    poll_msg = context.bot.send_poll(chat_id=update.effective_chat.id,
                                 question=
                                 f"Indicated participants, please vote if you would like to take part in "
                                 f"this activity, under the organiser {org_title}."
                                 f"\n"
                                 f"\nActivity: {ev_title}"
                                 f"\n    Date: {organiser_date}"
                                 f"\n    Time: {start_time_formatted} to {end_time_formatted}"
                                 f"\n\nParticipants: {part_string}",
                                 options=["Yes", "No"],
                                 allows_multiple_answers=False,
                                 is_anonymous=False)

    # Create new ongoing poll for database insertion
    chat_id = update.effective_chat.id
    new_poll_entry = {"poll_id": poll_msg.poll.id,
                      "chat_id": chat_id,
                      "organiser_title": org_title,
                      "message_id": poll_msg.message_id,
                      "answer_count": 0,
                      "expected_answers": len(part_list),
                      "s_hour": s_hour,
                      "s_min": s_min,
                      "e_hour": e_hour,
                      "e_min": e_min,
                      "event_title": ev_title
                      }

    collection_organiser_polls.insert_one(new_poll_entry)

    return ConversationHandler.END


conv_handler_add_event = ConversationHandler(
    entry_points=[CommandHandler('add', add)],
    states={
        EVENT_TITLE: [MessageHandler(Filters.regex(pattern='^' + '([a-zA-Z0-9\-()])+' + '$') & ~Filters.command,
                                     event_title)],
        START_HOUR: [CallbackQueryHandler(start_hour, pattern = "^shour")],
        START_MINUTE: [CallbackQueryHandler(start_minute, pattern="^smin")],
        END_HOUR: [CallbackQueryHandler(end_hour, pattern="^ehour")],
        END_MINUTE: [CallbackQueryHandler(end_minute, pattern="^emin")]
    },
    fallbacks=[CommandHandler('cancel', cancel), CommandHandler('unknown', unknown)]
)


def poll_result(update, context):
    poll_answer = update.poll_answer
    poll_id = poll_answer.poll_id
    data_cursor = collection_organiser_polls.find_one({"poll_id": poll_id})
    if data_cursor is None:
        return
    else:
        selected_answer = poll_answer.option_ids[0]
        answer_count = data_cursor['answer_count']
        expected_answers = data_cursor['expected_answers']
        chat_id = data_cursor['chat_id']
        message_id = data_cursor['message_id']
        org_title = data_cursor['organiser_title']
        ev_title = data_cursor['event_title']
        if selected_answer == 0:                    # Participant chooses yes
            answer_count += 1
            if answer_count == expected_answers:            # All participants have chosen yes
                new_event = {"event_title": ev_title,
                             "s_hour": data_cursor['s_hour'],
                             "s_min": data_cursor['s_min'],
                             "e_hour": data_cursor['e_hour'],
                             "e_min": data_cursor['e_min']
                             }
                context.bot.stop_poll(chat_id=chat_id, message_id=message_id)
                collection_organiser_polls.delete_one({"poll_id": poll_id, "chat_id": chat_id})
                org_data_cursor = collection_organisers.find_one({'chat_id': chat_id, 'organiser_title': org_title})
                event_list = org_data_cursor['events']
                event_list.append(new_event)
                collection_organisers.update_one({'chat_id': chat_id, 'organiser_title': org_title},
                                                 {'$set': {'events': event_list}})
                context.bot.send_message(chat_id = chat_id, text=
                                         f"All participants have agreed to the event <b>{ev_title}</b> under the "
                                         f"organiser <b>{org_title}</b>. The event has been added to the organiser!",
                                         parse_mode=telegram.ParseMode.HTML)
            else:                                           # Not all participants have voted yet
                collection_organiser_polls.update_one({"poll_id": poll_id, "chat_id": chat_id},
                                                      {'$set': {'answer_count': answer_count}})
        else:                                       # Participant chooses no
            context.bot.stop_poll(chat_id=chat_id, message_id=message_id)
            collection_organiser_polls.delete_one({"poll_id": poll_id})
            context.bot.send_message(chat_id=chat_id, text=
                                     f"Not all participants agreed to the event <b>{ev_title}</b> under the "
                                     f"organiser <b>{org_title}</b>. The event will not be added to the organiser.",
                                     parse_mode=telegram.ParseMode.HTML)
        return


poll_result_handler = PollAnswerHandler(poll_result)


def retrieve(update, context):
    if len(context.args) == 0:
        update.message.reply_text(
            "Please indicate the title of the event organiser, in the form <b>/retrieve organiser_name</b>."
            "\n"
            "\ne.g. /retrieve holiday",
            parse_mode=telegram.ParseMode.HTML
        )
        return
    else:
        chat_id = update.effective_chat.id
        org_title = str(context.args[0])
        data_cursor = collection_organisers.find_one({"organiser_title": org_title, "chat_id": update.effective_chat.id})
        if data_cursor is None:
            update.message.reply_text(
                "There is no event organiser with that particular title. Please enter a valid title."
            )
            return
        else:
            event_list = data_cursor['events']
            if len(event_list) == 0:
                context.bot.send_message(chat_id=chat_id, text=
                    "No events have been added to this event organiser yet.")
                return

            event_list_sorted = sorted(event_list, key=lambda x: (x['s_hour'], x['s_min']))

            # Format events
            organiser_date = data_cursor['organiser_date']
            split_date = organiser_date.split("/")
            int_date = list(map(lambda x: int(x), split_date))
            year = int_date[2]
            month = int_date[1]
            day = int_date[0]
            all_events_string = ""
            count = 1
            for event in event_list_sorted:
                ev_title = event['event_title']
                s_hour = event['s_hour']
                s_min = event['s_min']
                e_hour = event['e_hour']
                e_min = event['e_min']
                start_datetime = datetime.datetime(year=year, month=month, day=day, hour=int(s_hour), minute=int(s_min))
                end_datetime = datetime.datetime(year=year, month=month, day=day, hour=int(e_hour), minute=int(e_min))
                start_time_formatted = '{0:%I:%M%p}'.format(start_datetime)
                end_time_formatted = '{0:%I:%M%p}'.format(end_datetime)
                event_string = f"\n{count}) {ev_title}: {start_time_formatted} to {end_time_formatted}"
                count += 1
                all_events_string = all_events_string + event_string

            context.bot.send_message(chat_id=chat_id, text=
                f"The events under the organiser <b>{org_title}</b> are displayed below, sorted chronologically based "
                f"on start time."
                f"\n"
                f"\n<b>----Events List----</b>"
                f"{all_events_string}",
                parse_mode=telegram.ParseMode.HTML
            )
        return


retrieve_handler = CommandHandler('retrieve', retrieve)
