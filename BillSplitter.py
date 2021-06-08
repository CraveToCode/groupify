from telegram import Update
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
import logging

PARTICIPANTS, IMAGE, ITEMS = range(3)


def billSplitter(update, context) -> int:
    user = update.message.from_user
    context.bot.send_message(chat_id=update.effective_chat.id, text=
               "Hi! Welcome to the Bill Splitter! Please title the bill. " \
               "\n" \
               "You can /cancel at any time to abort this process.")
    return PARTICIPANTS


def selectParticipants(update, context) -> int:
    user = update.message.from_user
    context.bot.send_message(chat_id=update.effective_chat.id, text=
            "Cool! Please select the participants involved in the bill" \
            "\n" \
            "Again, you can /cancel at any time to abort this process.")
    return IMAGE


def uploadImage(update, context) -> int:
    user = update.message.from_user
    context.bot.send_message(chat_id=update.effective_chat.id, text=
            "Please upload an image of the receipt" \
            "\n" \
            "Again, you can /cancel at any time to abort this process.")
    return ITEMS


def inputItems(update, context) -> int:
    user = update.message.from_user
    context.bot.send_message(chat_id=update.effective_chat.id, text=
    "Thank you! Now please input the items on the receipt" \
    "\n" \
    "Again, you can /cancel at any time to abort this process.")
    return ConversationHandler.END


def cancel(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Bill Splitter has successfully terminated.")


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


conv_handler_split = ConversationHandler(
    entry_points=[CommandHandler('split', billSplitter)],
    states={
        PARTICIPANTS: [MessageHandler(Filters.text & ~Filters.command, selectParticipants)],
        IMAGE: [MessageHandler(Filters.text & ~Filters.command, uploadImage)],
        ITEMS: [MessageHandler(Filters.text & ~Filters.command, inputItems)]},
    fallbacks=[CommandHandler('cancel', cancel)],
)