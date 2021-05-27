# Initialize Bot
import Key
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging

updater = Updater(token=Key.API_KEY, use_context=True)

dispatcher = updater.dispatcher

# Logging Module
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Start Command
start_msg = "Hi! I'm GroupifyBot! How can I help you?"


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=start_msg)


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


# Unknown Commands
def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)


# Start/Stop Bot
updater.start_polling()
updater.idle()
