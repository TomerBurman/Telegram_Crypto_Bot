from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.messagehandler import MessageHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext.filters import Filters
from pycoingecko import CoinGeckoAPI
from bs4 import BeautifulSoup
import requests

updater = Updater("Your token here",
                  use_context=True)

crypto_api = CoinGeckoAPI()


# URL dictionary
urls = {'Market': 'https://crypto.com/price',
        'Gainers': 'https://crypto.com/price/showroom/biggest-gainers',
        'Losers': 'https://crypto.com/price/showroom/biggest-losers'
        }
# initial URL
url = urls['Market']


# Functionalities to the Bot
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Hello {} Welcome to {} bot. We supply updated prices of crypto currencies\n".format(update.message.from_user.first_name, context.bot.first_name))
    help(update, context)  # calling help


def help(update: Update, context: CallbackContext):
    update.message.reply_text("You can control me by sending one of the following commands:\n"
                              "/update - Sends an update on currencies sorted by your choice.\n"
                              "/sort - Sort by which parameter ? (Market cap, Top gainers/losers etc.)\n\n"
                              "You can also search for the coin you wish just by sending it's name"
                              "to me.(replace blank-spaces with '-')"
                              )


def optionsOfSort(update: Update, context: CallbackContext):
    '''
    When the user clicks one of the options, updateURL will be invoked
    :param update:
    :param context:
    :return:
    '''
    #  List of markups
    options = [
        [InlineKeyboardButton("by Top Gainers", callback_data='Gainers')],
        [InlineKeyboardButton("by Top Losers", callback_data='Losers')],
        [InlineKeyboardButton("by Market-cap", callback_data='Market')]
    ]
    #  initiating a markup
    reply_markup = InlineKeyboardMarkup(options)
    #  markup will show to the user
    update.message.reply_text(reply_markup=reply_markup, text="Which way do you want to sort them ?\n")


def update(update: Update, context: CallbackContext):
    '''
    scraping current url for cryptocurrencies and updates the user
    with a table format.
    :param update:
    :param context:
    :return:None
    '''
    form = "\n\n" + "{:<5} {:<15} {:<10} {:<25}\n".format("#", "Name", "Abb.", "Price")  # format
    # of : #     Name        Abb.        Price
    response = requests.get(url)  # getting the request response for the current url
    soup = BeautifulSoup(response.text,
                         'lxml')  # BeautifulSoup object with html content of the url and specifying a lxml parser
    table = soup.find('tbody')  # finding the table body
    rows = table.find_all('tr')  # find all table rows (coins)
    for i, row in zip(range(1, len(rows) + 1), rows):  # for each row in the table
        if url == urls['Market']:  # if url is set to Market-cap sort
            coin_name = row.find('div', class_='css-ttxvk0').p.text  # extracting name by p tag.
        else:
            coin_name = row.find('div', class_='css-ttxvk0').span.text  # extracting name by span tag
        coin_price = row.find('div', class_='css-b1ilzc').text  # extracting price
        coin_abbreviation = row.find('span', class_='chakra-text css-1jj7b1a').text  # extracting abbreviation
        form += '{:<5} {:<15} {:<10} {:<20}\n\n'.format(str(i), coin_name, coin_abbreviation, coin_price)  # Adding data to the format
    form += "For a more detailed information search the desired coin name"
    update.message.reply_text(form)  # updates the user with a reply text


def updateURL(update: Update, context: CallbackContext):
    '''
    updates URL by user choice in the query.
    :param update:
    :param context:
    :return:
    '''
    global url
    query_data = update.callback_query
    context.bot.send_message(chat_id=query_data.message.chat_id,
                             text='The coins will be shown sorted by {}'.format(query_data.data))
    url = urls[query_data.data]  # setting url


def price_message_handler(text_update: Update, context: CallbackContext):
    '''
    handles text messages sent to the bot
    uses get_price from CoinGeckoAPI which retrieves a dictionary with the coin name as a key, every coin has
    a currency and 24 hour change. e.g - coin_info['bitcoin']['usd] --> price of bitcoin in usd.
    :param text_update:
    :param context:
    :return:
    '''
    coin_info = crypto_api.get_price(text_update.message.text, vs_currencies='usd', include_24hr_change=True)
    if len(coin_info) > 0:
        text_update.message.reply_text(
            f'The price for {text_update.message.text} is : {coin_info[text_update.message.text.lower()]["usd"]:<,} US dollars.\n'
            f'24 hour change : {coin_info[text_update.message.text.lower()]["usd_24h_change"]:.2f}%')
    else:
        text_update.message.reply_text(f'The crypto {text_update.message.text} was not found. ')


# Adding handlers to the bot
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('update', update))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('sort', optionsOfSort))
dispatcher.add_handler(MessageHandler(Filters.text, price_message_handler))
dispatcher.add_handler(CallbackQueryHandler(updateURL))

if __name__ == '__main__':
    updater.start_polling()

