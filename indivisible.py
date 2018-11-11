# coding: utf-8
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode
from telegram.ext import (Updater, CommandHandler, ConversationHandler, MessageHandler,
                        Filters, RegexHandler)
import logging, json, random, base64

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

amics = []
admin_keyboard = [['Info', 'Codes'],
                 ['Sorting', 'Save']]
delete_keyboard = ReplyKeyboardRemove()
admin_markup = ReplyKeyboardMarkup(admin_keyboard, one_time_keyboard=True)
LOGIN, ADMIN_CHOOSING, SHOW_INFO = range(3)
lang = None

def getLang(selected_lang):
    try:
        with open('indivisible-lang.json', 'r') as fo:
            json_data_file = fo.read()
            languages = json.loads(json_data_file)

        print("Languages loaded correctly")
        return languages[selected_lang]
    except OSError as err:
        logger.error('Error while loading languages: "%s"', err)

def saveData(bot, update):
    try:
        dataToString = json.dumps(amics)
        encoded = base64.b64encode(dataToString)
        fo = open('secretsantasaved','w+')
        fo.write(encoded)
        fo.close()
        update.message.reply_text("Saving done, bye!")
    except OSError as err:
        logger.error('Error while saving the file "%s"', err)

def loadData():
    try:
        fo = open('secretsantasaved','r')
        encodedData = fo.read()

        ## missing padding error
        missing_padding = len(encodedData) % 4
        if missing_padding != 0:
            print "MISSING PADDING"
            encodedData += b'='* (4 - missing_padding)

        stringToData = base64.b64decode(encodedData)
        fo.close()
        global amics
        amics = json.loads(stringToData)
        print("Loaded correctly")
    except OSError as err:
        logger.error('Error while loading the file "%s"', err)

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def mix_people(bot,update):
    totalPeople = [x["id"] for x in amics]
    oldTotalPeople = totalPeople[:]
    notFine = True
    while notFine:
        for amic in amics:
            if len(totalPeople) > 1:
                id = random.choice(totalPeople)
                while id == amic["id"]: id = random.choice(totalPeople)
                amic["towho"] = id
                totalPeople.remove(id)
            else:
                if totalPeople[0] == amic["id"]:
                    totalPeople = oldTotalPeople[:]
                else:
                    amic["towho"] = totalPeople[0]
                    notFine = False
    update.message.reply_text("Mix done!")


def start(bot, update):
    introText = lang["ASK_PWD"]
    update.message.reply_text(introText, reply_markup=delete_keyboard)
    loadData()
    print "START!"
    return LOGIN

def login(bot, update, user_data):
    text = update.message.text
    print "LOGIN! - " + update.message.from_user.first_name.encode("utf-8")
    text = text.lower()
    if text == lang["ADMIN_PWD"]:
        print "ADMIN!! - " + update.message.from_user.first_name.encode("utf-8")
        update.message.reply_text("Welcome Admin!", reply_markup=admin_markup)
        return ADMIN_CHOOSING
    print "NOT ADMIN!"
    for amic in amics:
        if amic['pwd'] == text:
            update.message.reply_text("{0} {1}!".format(lang["HI"], amic["nom"]))
            user_data['idamic'] = amic['id']
            info(bot, update, amic)
            return SHOW_INFO
    update.message.reply_text("IDENTIFY YOURSELF D:!")

def admin_codis(bot, update):
    text = update.message.text
    wanted_info = ""
    for amic in amics:
        wanted_info += "" + amic["nom"] + " - " + amic["pwd"] + "\n"
    update.message.reply_text(wanted_info)

def admin_info(bot, update):
    text = update.message.text
    wanted_info = ""
    for amic in amics:
        #wanted_info += "" + amic["nom"] + " - " + amic["likes"] + " - " + str(amic["towho"])+ "\n"
        wanted_info += "" + amic["nom"] + " - " + amic["likes"] + "\n"
    update.message.reply_text(wanted_info)

def info(bot, update, amic):
    wanted_info = lang["YOUR_DATA"]
    towho = -1
    wanted_info += "{0}: *{1}*\n{2}: *{3}*\n\n".format(lang["NAME"], amic["nom"].encode("utf-8"), lang["YOUR_LIKES"], amic["likes"].encode("utf-8"))
    towho = amic['towho']
    wanted_info += lang["AMIC_DATA"]
    for invisible in amics:
        if invisible['id'] == towho:
            #wanted_info += "{0}: *{1}*\n{2}: *{3}*".format(lang["NAME"], invisible["nom"], lang["AMIC_LIKES"], invisible["likes"].encode("utf-8"))
            wanted_info += lang["NAME"]+": *"+invisible["nom"]+ "*\n"+lang["AMIC_LIKES"]+": *" +invisible["likes"] + "*"

    update.message.reply_text(wanted_info, parse_mode=ParseMode.MARKDOWN)

def change_name(bot, update, args):
    id = int(args[0])
    name = args[1]
    global amics
    changeFriend = amics[id]
    changeFriend["nom"] = name
    print "NAME CHANGED"

def main():
    updater = Updater(TOKEN)
    # Add conversation handler with the states LOGIN, ADMIN_CHOOSING AND SHOW_INFO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            LOGIN: [MessageHandler(Filters.text,
                                   login, pass_user_data=True),
                    ],
            ADMIN_CHOOSING: [RegexHandler('^Sorting$',
                                    mix_people),
                            RegexHandler('^Codes$',
                                   admin_codis),
                            RegexHandler('^Info$',
                                   admin_info),
                            ],
            SHOW_INFO: [MessageHandler(Filters.text,
                                   info,pass_user_data=True),
                      ],
        },

        fallbacks=[RegexHandler('^Save$', saveData)],
        allow_reentry=True,
        name="pimpamtomalacasitos"
        #persistent=True
    )
    change_handler = CommandHandler('change_name', change_name, pass_args=True)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(change_handler)
    # log all errors
    dispatcher.add_error_handler(error)

    global lang
    lang = getLang("CA")

    print("STARTING!")

    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()



if __name__ == '__main__':
    main()
