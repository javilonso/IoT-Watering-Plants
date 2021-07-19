import logging
import time
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
from time import sleep
import wiringpi
import picamera

TOKEN = 'YOUR_TOKEN'        # Get your token from  @botfather
CHAT_ID = 'YOUR_CHAT_ID'    # Restrict access to your bot
WATERING_TIME = 60          # Seconds to activate water pump

# ************ Telegram Enable logging ************
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

temporary_data: Dict[int, dict] = {}

# ************ Telegram Restrictions ************
LIST_OF_ADMINS = [int(CHAT_ID)] # List of user_id of authorized users

def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            print("Unauthorized access denied for {}.".format(user_id))
            return
        return func(update, context, *args, **kwargs)
    return wrapped


# ************ Telegram Commands Functions ************
# You can edit these commands to modify the actions

# /watering command action
@restricted
def watering(update, context):
    print(temporary_data.get(update.effective_chat.id, None))

    
    wiringpi.digitalWrite(7, 1) # Power On Water Pump
    sleep(5)                    # Wait 5 seconds until water is coming out before taking a photo 

    with picamera.PiCamera() as camera:
      camera.resolution = (768, 1024)
      camera.rotation = 270
      camera.start_preview()
      sleep(1)
      camera.capture('photo.jpg')
      file = open('photo.jpg', 'rb')
      context.bot.sendPhoto(chat_id=CHAT_ID, photo=file, caption="Here is your watering picture")

    sleep(WATERING_TIME - 5)    # After 55 seconds the Water Pump stops
    wiringpi.digitalWrite(7, 0) # Power Off Water Pump

    # Estimate water level with Ultrasonic Sensor
    aux_dist = []
    for i in range(0,10):
        dist = distance()
        aux_dist.append(dist)
        sleep(1)
        
    dist = sum(aux_dist)/len(aux_dist)
    litros_restantes = 16-(25*35*dist/1000)
    dist_text = "Water level: " + ("%.2f" % dist) + " cm\nLiters left: " + ("%.2f" % litros_restantes) + " L"
    context.bot.sendMessage(chat_id=CHAT_ID, text= dist_text)

# /status command action
@restricted
def status(update, context):
    context.bot.sendMessage(chat_id=CHAT_ID, text='I am online')
   
# /capacity command action
@restricted
def capacity(update, context):
    context.bot.sendMessage(chat_id=CHAT_ID, text= "Wait 10 seconds for the estimation")
    aux_dist = []
    for i in range(0,10):
        dist = distance()
        aux_dist.append(dist)
        sleep(1)
        
    dist = sum(aux_dist)/len(aux_dist)
    litros_restantes = 16-(23*33*dist/1000)
    dist_text = "Water level: " + ("%.2f" % dist) + " cm\nLiters left: " + ("%.2f" % litros_restantes) + " L"
    context.bot.sendMessage(chat_id=CHAT_ID, text= dist_text)

# Get ultrasonic sensor reads
def distance():
    GPIO_TRIGGER = 16
    GPIO_ECHO = 18
    # set Trigger to HIGH
    wiringpi.digitalWrite(GPIO_TRIGGER,1)
 
    # set Trigger after 0.01ms to LOW
    sleep(0.00001)
    wiringpi.digitalWrite(GPIO_TRIGGER,0)

 
    StartTime = time.time()
    StopTime = time.time()
 
    # save StartTime
    while wiringpi.digitalRead(GPIO_ECHO) == 0:
        StartTime = time.time()
 
    # save time of arrival
    while wiringpi.digitalRead(GPIO_ECHO) == 1:
        StopTime = time.time()
 
    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2
    return distance
 

# ########################### Main #########################################
def main():

    sleep(1)
    wiringpi.wiringPiSetupPhys()
    
    # Mosfet
    wiringpi.pinMode(7, 1)	   
    wiringpi.digitalWrite(7,0)

    #Ultrasonic sensor
    GPIO_TRIGGER = 16   
    GPIO_ECHO = 18     
    wiringpi.pinMode(GPIO_TRIGGER, 1)
    wiringpi.pinMode(GPIO_ECHO, 0)

    global API_URL
    API_URL = 'https://api.telegram.org/bot' + TOKEN +'/'

    # Create the Updater and Bot and pass it your bot's token.
    updater = Updater(TOKEN)
    global bot
    bot = Bot(token=TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Telegram commands with their actions
    dispatcher.add_handler(CommandHandler("watering", watering))
    dispatcher.add_handler(CommandHandler('status', status))
    dispatcher.add_handler(CommandHandler('capacity', capacity))

    # ############################ Handlers #########################################
    updater.dispatcher.add_handler(
        CallbackQueryHandler(main_area_selection, pattern="main")
    )
    
    requests.post('https://api.telegram.org/bot' + TOKEN + '/sendMessage', {'chat_id': CHAT_ID, 'text': '[Bot available]'})

    # Start the Bot/Listen for user input/messages
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
