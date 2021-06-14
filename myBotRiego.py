#!/usr/bin/env python
# pylint: disable=C0116

import logging
from typing import Dict
import requests
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
)
from functools import wraps
import wiringpi
from time import sleep
import picamera


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

temporary_data: Dict[int, dict] = {}

# ############################ RESTRICTIONS  ############################
LIST_OF_ADMINS = [243684919] # List of user_id of authorized users

def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            print("Unauthorized access denied for {}.".format(user_id))
            return
        return func(update, context, *args, **kwargs)
    return wrapped

# ########################### Selection #########################################

def main_area_selection(update, _: CallbackContext) -> None:
    global temporary_data
    temporary_data[update.effective_chat.id] = {}

    query = update.callback_query
    query.answer()
    update.effective_message.delete()

    if "main" in query.data:
        number = query.data.split("_")[-1]
        #print(query.data)

        if number == "1":
           with picamera.PiCamera() as camera:
             camera.resolution = (1024, 768)
             camera.start_preview()
             sleep(1)
             camera.capture('photo.jpg')
             file = open('photo.jpg', 'rb')
             
             query.message.reply_photo(photo=file, caption="Has elegido la opción SI, te mando foto después del riego")

        elif number == "2":
          query.message.reply_text(f"Has elegido la opción NO")


# ########################### Functions #########################################

@restricted
def start(update, context):
    """Send a message when the command /start is issued."""
    print(temporary_data.get(update.effective_chat.id, None))

    with picamera.PiCamera() as camera:
      camera.resolution = (1024, 768)
      camera.start_preview()
      sleep(1)
      camera.capture('photo.jpg')
      file = open('photo.jpg', 'rb')
      context.bot.sendPhoto(chat_id=CHAT_ID, photo=file, caption="Antes del riego")

    # Activar bomba de agua
    wiringpi.digitalWrite(7, 1) #power putton
    sleep(2)
    wiringpi.digitalWrite(7, 0) #release power button

    update.message.reply_text(
        "¿Quieres foto?",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("SI", callback_data="main_1"),
                ],
                [
                    InlineKeyboardButton("NO", callback_data="main_2"),
                ],
            ]
        ),
    )

@restricted
def help(update, context):
    context.bot.sendMessage(chat_id=CHAT_ID, text='Estoy online!')
   

@restricted
def send_img(update, context):
    with picamera.PiCamera() as camera:
      camera.resolution = (1024, 768)
      camera.start_preview()
      sleep(1)
      camera.capture('photo.jpg')
      file = open('photo.jpg', 'rb')
      context.bot.sendPhoto(chat_id=CHAT_ID, photo=file)


# ########################### Main #########################################
def main():

    sleep(1)
    wiringpi.wiringPiSetupPhys()
    wiringpi.pinMode(7, 1)	#reset pin in rele output mode
    wiringpi.digitalWrite(7,0)

    global TOKEN
    global CHAT_ID
    global API_URL
    TOKEN = '1895975525:AAEvpxwmJEJo_GfdrLgrPDv2opTDpvsJrgU'
    CHAT_ID = '243684919'
    API_URL = 'https://api.telegram.org/bot' + TOKEN +'/'


    # Create the Updater and Bot and pass it your bot's token.
    updater = Updater(TOKEN)
    global bot
    bot = Bot(token=TOKEN)
    

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("riego", start))
    dispatcher.add_handler(CommandHandler('foto', send_img))
    dispatcher.add_handler(CommandHandler('help', help))

    # ############################ Handlers #########################################
    updater.dispatcher.add_handler(
        CallbackQueryHandler(main_area_selection, pattern="main")
    )


    # Start the Bot/Listen for user input/messages
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
