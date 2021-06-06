from telegram import Update
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackContext
import logging

PARTICIPANTS = range(1)
logger = logging.getLogger(__name__)


def organise(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Hi! Welcome to the Event Organiser! Please input a name for your event list. "
        "\n"
        "You can /cancel at any time to abort this process.")
    # context.bot.send_message(chat_id=update.effective_chat.id, text=
    #            "Hi! Welcome to the Meetup Scheduler! Please input the name of your event. " \
    #            "\n" \
    #            "You can /cancel at any time to abort this process.")
    return PARTICIPANTS


def participants(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Great! Now you can select the participants that will be involved in your event. "
        "\n"
        "You can /cancel at any time to abort this process.")
    # context.bot.send_message(chat_id=update.effective_chat.id, text=
    #         "Cool! How long will the event approximately last for? Please input a number to represent estimated "
    #         "duration in hours." \
    #         "\n" \
    #         "Again, you can /cancel at any time to abort this process.")
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Meetup Scheduler has successfully terminated.")
    return ConversationHandler.END


def unknown(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Sorry, I did not understand that command.")


conv_handler_organiser = ConversationHandler(
    entry_points=[CommandHandler('organise', organise)],
    states={
        PARTICIPANTS: [MessageHandler(Filters.text & ~Filters.command, participants)],
    },
    fallbacks=[CommandHandler('cancel', cancel), CommandHandler('unknown', unknown)]
)

