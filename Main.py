# Main file to initialize bot from

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
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
    # new_user = f"""
    # INSERT INTO users VALUES
    # (DEFAULT, \"{update.effective_user.id}\")
    # ON DUPLICATE KEY UPDATE user_tele_id = \"{update.effective_user.id}\";
    # """
    # connection = Database.create_db_connection("us-cdbr-east-04.cleardb.com", "bea2e6c2784c72", "a0c7ca66",
    #                                            "heroku_2b5704fd7eefb53")
    # Database.execute_query(connection, new_user)

    context.bot.send_message(chat_id=update.effective_chat.id, text=
    "Great! Events created by users will have you listed as a potential participant from now on.")


join_handler = CommandHandler('join', join)
dispatcher.add_handler(join_handler)

# Help Command
help_msg = "GroupifyBot supports 3 features: Meetup-Scheduler, Bill Splitter, Event Organiser." \
           "\n \n" \
           "*Important*: Please type */join* if you wish to be considered as a potential participant of the events " \
           "created through this bot." \
           "\n \n" \
           "Type */meetup* to start a new meetup event. This will output the best time for all your friends to meetup," \
           "along with the best location." \
           "\n \n" \
           "Type */split* to start a new bill to be split. This will output the exact amount each person will have to " \
           "pay you." \
           "\n \n" \
           "Type */organise* to start a new event organiser. The event organiser will help you plan your day and " \
           "display the activities for the day chronologically. It even allows participants to propose activities" \
           "that others can then bid on."


def help(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_msg)


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
updater.start_webhook(listen="0.0.0.0",
                      port=PORT,
                      url_path=TOKEN,
                      webhook_url="https://groupify-orbital.herokuapp.com/" + TOKEN)
updater.idle()
