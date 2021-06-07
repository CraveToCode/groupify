# Main file to initialize bot from

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
import logging
import os
from Scheduler import conv_handler_meetup
from Organiser import conv_handler_organiser
from BillSplitter import conv_handler_split

# API Token
updater = Updater(token=os.environ['API_KEY'], use_context=True)

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


# Help Command
help_msg = "GroupifyBot supports 3 features: Meetup-Scheduler, Bill Splitter, Event Organiser." \
           "\n \n" \
           "Type /meetup to start a new meetup event. This will output the best time for all your friends to meetup," \
           "along with the best location." \
           "\n \n" \
           "Type /split to start a new bill to be split. This will output the exact amount each person will have to " \
           "pay you." \
           "\n \n" \
           "Type /organise to start a new event organiser. The event organiser will help you plan your day and " \
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
updater.start_polling()
updater.idle()
