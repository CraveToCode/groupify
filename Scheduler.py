from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
import logging

TITLE, DURATION, TIMEFRAME = range(3)


def meetup(update, context) -> int:
    user = update.message.from_user
    context.bot.send_message(chat_id=update.effective_chat.id, text=
               "Hi! Welcome to the Meetup Scheduler! Please input the name of your event. " \
               "\n" \
               "You can /cancel at any time to abort this process.")
    return TITLE


def title(update, context) -> int:
    user = update.message.from_user
    context.bot.send_message(chat_id=update.effective_chat.id, text=
            "Cool! How long will the event approximately last for? Please input a number to represent estimated "
            "duration in hours." \
            "\n" \
            "Again, you can /cancel at any time to abort this process.")
    return DURATION


def duration(update, context) -> int:
    user = update.message.from_user
    context.bot.send_message(chat_id=update.effective_chat.id, text=
            "In how many days will the event start? Please input a number to represent estimated duration in days." \
            "\n" \
            "Again, you can /cancel at any time to abort this process.")
    return TIMEFRAME


def timeframe(update, context) -> int:
    return 4


def cancel(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Meetup Scheduler has successfully terminated.")


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


conv_handler = ConversationHandler(entry_points=[CommandHandler('meetup', meetup)],
                                   states={
                                       TITLE: [MessageHandler(Filters.text & ~Filters.command, title)],
                                       DURATION: [MessageHandler(Filters.text & ~Filters.command, duration)],
                                       TIMEFRAME: [MessageHandler(Filters.text & ~Filters.command, timeframe)]},
                                   fallbacks=[CommandHandler('cancel', cancel)],
                                   )
