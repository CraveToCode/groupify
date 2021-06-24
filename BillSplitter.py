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
collection_bills = Database.db.bills

# States
TITLE, PARTICIPANTS, IMAGE, ITEMS, UPLOAD, AUTO_READ, MANUAL_INPUT, MANUAL_INPUT_LOOP, USER_MATCHING,\
    USER_MATCHING_LOOP= range(10)

# Callback Data
DONE_PARTICIPANTS, YES_IMAGE, NO_IMAGE, YES_READ, NO_READ, GOOD_OUTPUT, SELF_INPUT, DONE_ITEMS, \
    BEGIN_MATCHING, DONE_PAYERS = range(10)

# Logging
logger = logging.getLogger(__name__)


# Program
def bill_splitter(update, context) -> int:
    # Clear any user_data from other events in this chat
    context.user_data.clear()

    update.message.reply_text(
        "Hi! Welcome to the Bill Splitter! Please title the bill. "
        "\n \n"
        "You can /cancel at any time to abort this process.")

    return TITLE


def title(update, context) -> int:
    user_input = update.message.text
    context.user_data["bill_title"] = user_input

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
    participant_pool_keyboard = list(map(lambda x: InlineKeyboardButton(x,  callback_data=f"participant:{x}"),
                                         participant_pool))
    reply_keyboard = [participant_pool_keyboard[i:i + n] for i in range(0, num_of_participants, n)]
    reply_keyboard.append([InlineKeyboardButton("DONE", callback_data=str(DONE_PARTICIPANTS))])
    context.user_data["participant_keyboard"] = reply_keyboard

    # Add cross emojis to participant_pool and store it
    participant_pool = list(map(lambda x: x + " \U0000274c", participant_pool))
    context.user_data["participant_pool"] = participant_pool

    participant_pool_listed = '\n'.join(participant_pool)  # stringify name list

    update.message.reply_text(
        f"Cool! Please select the participants involved in this bill."
        f"\nYou can tap the same person again to remove them."
        f"\nSelect DONE if you are done selecting participants."
        f"\nAgain, you can /cancel at any time to abort this process."
        f"\n \n"
        f"Participant List: "
        f"\n{participant_pool_listed}",
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )

    # Log
    logger.info("Name of bill: %s", user_input)

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
    value_unlisted = user_input + " \U0000274c"                                # user input with cross
    value_listed = user_input + " \U00002714"                                  # user input with check
    if user_input not in participants_final:
        participants_final.append(user_input)                                                   # add user to final list
        participant_pool = overwrite(participant_pool, value_unlisted, value_listed)            # add check emoji
        context.user_data["participant_pool"] = participant_pool                                # save new name list
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
        context.user_data["participant_pool"] = participant_pool                                  # save new name list
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

    reply_keyboard = [[InlineKeyboardButton("Yes", callback_data=str(YES_IMAGE)),
                      InlineKeyboardButton("No", callback_data=str(NO_IMAGE))]]

    context.bot.send_message(chat_id=update.effective_chat.id, text=
        "Awesome\! Participants responsible for ~owing you money~ the bill have been added\."
        "\nWould you like to upload an image of the receipt for the others to see?",
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
        parse_mode=telegram.ParseMode.MARKDOWN_V2
    )

    return IMAGE


def upload_image(update, context) -> int:
    query = update.callback_query
    query.answer()
    logger.info("User has chosen to upload an image.")

    query.edit_message_text(text="Go ahead and upload an image of the receipt!")

    return UPLOAD


def auto_read_selection(update, context) -> int:
    user_input = update.message.text
    # TODO need to store this image ^
    query = update.callback_query
    query.answer()
    logger.info("User has uploaded an image.")

    reply_keyboard = [[InlineKeyboardButton("Yes", callback_data=str(YES_READ)),
                      InlineKeyboardButton("No", callback_data=str(NO_READ))]]

    query.edit_message_text(text="Your image has been successfully recorded. Would you like to use our optical"
                                 "character recognition to auto-read the items in your receipt and expedite this"
                                 "process?",
                            reply_markup=InlineKeyboardMarkup(reply_keyboard))

    return AUTO_READ


def auto_read(update, context) -> int:
    query = update.callback_query
    query.answer()

    # TODO Implement autoread feature

    logger.info("User has chosen to auto read the receipt.")

    reply_keyboard = [[InlineKeyboardButton("Manual Input", callback_data=str(GOOD_OUTPUT)),
                      InlineKeyboardButton("Good to go", callback_data=str(SELF_INPUT))]]

    # TODO need to display auto generated results in reply_text below
    context.bot.send_message(chat_id=update.effective_chat.id, text=
        "This is the auto-generated bill split according to who owes what. "
        "\nIf this is inaccurate, you may opt to input the items manually instead.",
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )
    return MANUAL_INPUT


# TODO temporary placeholder for good_output path of optical recognition feature
def temp(update, context) -> int:
    query = update.callback_query
    query.answer()
    logger.info("User has accepted the provided output result.")

    return ConversationHandler.END


def input_items_start(update, context) -> int:
    query = update.callback_query
    query.answer()
    logger.info("User has chosen to input items manually.")
    context.user_data["item_number"] = 2
    context.user_data["item_dict"] = {}
    context.user_data["item_list"] = ""

    message_details = context.bot.send_message(chat_id=update.effective_chat.id, text=
        "Welcome to manual entry\! Please input the *name* of your first item, followed by the *value* and *quantity* "
        "of it\."
        "\nFor instance, if you want to input '2x Apple' for '$5\.49' each, you should type '*apple 5\.49 2*', "
        "without the quotations\."
        "\nYou can review this message each time you add an item\."
        "\n"
        "\n"
        "Note: Duplicate names are disallowed."
        "\nAgain, you can /cancel at any time to abort this process\.",
        parse_mode=telegram.ParseMode.MARKDOWN_V2
    )

    context.user_data["reference_message_id"] = message_details['message_id']
    return MANUAL_INPUT_LOOP


def input_items_loop(update, context) -> int:
    user_input_split = update.message.text.split()
    item_name = user_input_split[0]
    item_value = float(user_input_split[1])
    item_quantity = int(user_input_split[2])
    item_cost = item_value * item_quantity
    item_number = context.user_data.get("item_number")
    context.user_data["item_number"] = item_number + 1      # item number of the next user input

    # Retrieve dictionary of items and store new item
    item_dict = context.user_data.get("item_dict")
    item_dict[item_name] = [item_cost]
    context.user_data["item_dict"] = item_dict              # Store updated item_dict

    # Retrieve item_list string and add new item
    item_list = context.user_data.get("item_list")
    item_list = item_list + f"\n{item_number - 1}) {item_name}: ${item_value}   (Qty: x{item_quantity})"
    context.user_data["item_list"] = item_list

    reference_message_id = context.user_data.get("reference_message_id")
    reply_keyboard = [[InlineKeyboardButton("DONE", callback_data=str(DONE_ITEMS))]]
    item_value = str(item_value)
    context.bot.edit_message_text(text=
                                  f"{item_quantity}x {item_name} for ${item_value} each has been added." 
                                  f"Please input the name and value of the next item (no. {item_number}). "
                                  f"Otherwise, press DONE."
                                  f"\n \n"
                                  f"---Current Item List--- "
                                  f"{item_list}",
                                  chat_id=update.effective_chat.id,
                                  message_id=reference_message_id,
                                  reply_markup=InlineKeyboardMarkup(reply_keyboard)
                                  )

    logger.info(f"Current Item List: {item_list}")

    return MANUAL_INPUT_LOOP


def match_users_prompt(update, context):
    query = update.callback_query
    query.answer()

    item_dict = context.user_data.get("item_dict")
    item_dict_keylist = list(item_dict.keys())
    item_dict_keylist.append(None)
    context.user_data["item_dict_keylist"] = item_dict_keylist

    # Payer Keyboard Creation
    participants_final = context.user_data.get("participants_final")
    payer_pool = participants_final.copy()
    num_of_payers = len(payer_pool)
    n: int = ceil(sqrt(num_of_payers))
    payer_pool_keyboard = list(map(lambda x: InlineKeyboardButton(x, callback_data=f"payer:{x}"),
                                   payer_pool))
    reply_keyboard = [payer_pool_keyboard[i:i + n] for i in range(0, num_of_payers, n)]
    reply_keyboard.append([InlineKeyboardButton("DONE", callback_data=str(DONE_PAYERS))])
    context.user_data["payer_keyboard"] = reply_keyboard

    # Add cross emojis to payer_pool and store it
    payer_pool = list(map(lambda x: x + " \U0000274c", payer_pool))
    context.user_data["payer_pool"] = payer_pool
    context.user_data["payer_pool_clean_list"] = '\n'.join(payer_pool)         # stringify name list

    # Temporary field to allow program to realise what item it is at during the next state
    started = False
    context.user_data["started"] = started

    # Reply keyboard for current state
    reply_keyboard = [[InlineKeyboardButton("BEGIN", callback_data=str(BEGIN_MATCHING))]]

    context.bot.send_message(chat_id=update.effective_chat.id, text=
        "Wonderful! You will now be prompted to indicate which users are responsible for each item "
        "in the bill. Press BEGIN to start the process.",
        reply_markup=InlineKeyboardMarkup(reply_keyboard))

    logger.info(f"User has finished inputting items.")

    return USER_MATCHING


def match_users_start(update, context):
    query = update.callback_query
    query.answer()

    # Store list of finalized participants if this is not the first iteration
    started = context.user_data.get("started")
    if started:
        item = context.user_data.get("item")
        item_dict = context.user_data.get("item_dict")
        payers_final = context.user_data.get("payers_final")
        item_dict[item].append(payers_final)
        context.user_data["item_dict"] = item_dict
    else:
        started = True
        context.user_data["started"] = started

    # Pop first item from keylist and check if it exists
    item_dict_keylist = context.user_data.get("item_dict_keylist")
    item = item_dict_keylist.pop(0)

    if item is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text=
        "All items have been accounted for. Payers will be notified individually!")

        return ConversationHandler.END

    else:
        # Store new item and updated item_dict_keylist
        context.user_data["item"] = item
        context.user_data["item_dict_keylist"] = item_dict_keylist

        # Reset list of finalized participants
        payers_final = []
        context.user_data["payers_final"] = payers_final

        # Payer Keyboard
        reply_keyboard = context.user_data.get("payer_keyboard")

        # Reset payer pool
        payer_pool = context.user_data.get("payer_pool")
        context.user_data["payer_pool_edittable"] = payer_pool.copy()
        payer_pool_listed = context.user_data.get("payer_pool_clean_list")
        query.edit_message_text(
            text=f"Please select the payers for *{item}*\."
                 f"\nYou can select DONE if you are done selecting payers\."
                 f"\nAgain, you can /cancel at any time to abort this process\."
                 f"\n \n"
                 f"Payer list:"
                 f"\n{payer_pool_listed}",
            reply_markup=InlineKeyboardMarkup(reply_keyboard),
            parse_mode=telegram.ParseMode.MARKDOWN_V2
        )
        return USER_MATCHING_LOOP


def match_users_loop(update, context):
    query = update.callback_query
    query.answer()
    user_input = query.data.split(':')[1]

    # Retrieve current item
    item = context.user_data.get("item")

    # Retrieve Participant Keyboard
    reply_keyboard = context.user_data.get("payer_keyboard")

    # Add payer entered previously
    payer_pool_edittable = context.user_data.get("payer_pool_edittable")
    payers_final = context.user_data.get("payers_final")
    value_unlisted = user_input + " \U0000274c"                                # user input with cross
    value_listed = user_input + " \U00002714"                                  # user input with check
    if user_input not in payers_final:
        payers_final.append(user_input)                                                         # add user to final list
        payer_pool_edittable = overwrite(payer_pool_edittable, value_unlisted, value_listed)    # add check emoji
        context.user_data["payer_pool_edittable"] = payer_pool_edittable                        # save new name list
        payer_pool_listed = '\n'.join(payer_pool_edittable)                                     # stringify name list
        query.edit_message_text(
            text=f"{user_input} has been added as payer for {item}."
                 f"\nWould you like to add/remove anyone else? If not, please select DONE."
                 f"\n \n"
                 f"Payer list:"
                 f"\n{payer_pool_listed}",
            reply_markup=InlineKeyboardMarkup(reply_keyboard)
        )
    else:
        payers_final.remove(user_input)                                                         # remove user
        payer_pool_edittable = overwrite(payer_pool_edittable, value_listed, value_unlisted)    # add cross emoji
        context.user_data["payer_pool_edittable"] = payer_pool_edittable                        # save new name list
        payer_pool_listed = '\n'.join(payer_pool_edittable)                                     # stringify name list
        query.edit_message_text(
            text=f"{user_input} has been removed from being a payer for {item}."
                 f"\nWould you like to add/remove anyone else? If not, please select DONE."
                 f"\n \n"
                 f"Payer list:"
                 f"\n{payer_pool_listed}",
            reply_markup=InlineKeyboardMarkup(reply_keyboard)
        )

    context.user_data["payers_final"] = payers_final
    logger.info("Payer list: %s", payers_final)

    return USER_MATCHING_LOOP


def cancel(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Bill Splitter has successfully terminated.")
    return ConversationHandler.END


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


conv_handler_split = ConversationHandler(
    entry_points=[CommandHandler('split', bill_splitter)],
    states={
        TITLE: [MessageHandler(Filters.text & ~Filters.command, title)],
        PARTICIPANTS: [CallbackQueryHandler(participants, pattern="^participant"),
                       CallbackQueryHandler(no_participants, pattern='^' + str(DONE_PARTICIPANTS) + '$')
                       ],
        IMAGE: [CallbackQueryHandler(upload_image, pattern='^' + str(YES_IMAGE) + '$'),
                CallbackQueryHandler(input_items_start, pattern='^' + str(NO_IMAGE) + '$')
                ],
        UPLOAD: [MessageHandler(Filters.photo & ~Filters.command, auto_read_selection)],
        AUTO_READ: [CallbackQueryHandler(auto_read, pattern='^' + str(YES_READ) + '$'),
                    CallbackQueryHandler(input_items_start, pattern='^' + str(NO_READ) + '$')
                ],
        MANUAL_INPUT: [CallbackQueryHandler(temp, pattern='^' + str(GOOD_OUTPUT) + '$'),
                       CallbackQueryHandler(input_items_start, pattern='^' + str(SELF_INPUT) + '$')
                ],
        MANUAL_INPUT_LOOP: [MessageHandler(Filters.text & ~Filters.command, input_items_loop),
                            CallbackQueryHandler(match_users_prompt, pattern='^' + str(DONE_ITEMS) + '$')],
        USER_MATCHING: [CallbackQueryHandler(match_users_start, pattern='^' + str(BEGIN_MATCHING) + '$')],
        USER_MATCHING_LOOP: [CallbackQueryHandler(match_users_loop, pattern="^payer"),
                             CallbackQueryHandler(match_users_start, pattern='^' + str(DONE_PAYERS) + '$')]
    },
    fallbacks=[CommandHandler('cancel', cancel), CommandHandler('unknown', unknown)]
)