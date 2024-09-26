# from flask import Flask, jsonify, request
# import asyncio
# import threading
# import subprocess
# from aiogram import Bot, Dispatcher, executor, types
# from waitress import serve
# import sys

# # Initialize the Bot instance
# bot = Bot(token='7256914379:AAFSDgHNuCZy8JAx1Wxu_-WLjf_fniHnfUs')

# dp = Dispatcher(bot)

# app = Flask(__name__)

# status = True

# @app.route('/match', methods=['POST'])
# def send_match():
#     if status:
#         data = request.json
#         asyncio.run(send_to_group_channel(data))
#     return ''

# # Create a new book
# @app.route('/book', methods=['POST'])
# def create_book():
#     if request.json:
#         match_number = request.json['match_number']
#         total_price = request.json['total_price']
#         unit_price = request.json['unit_price']
#         category = request.json['category']
#         username = request.json['username']
#         password = request.json['password']
#         ads = request.json['ads']
#         formatted_data = f'<b>Матч:</b> <i>{match_number}</i>\n<b>Кількість квитків та категорія:</b> <i>{category}</i>\n<b>Ціна за квиток:</b> <i>{unit_price}</i>\n<b>Ціна за всі квитки:</b> <i>{total_price}</i>\n<b>username:</b> <i>{username}</i>\n<b>password:</b> <i>{password}</i>\n<b>ads:</b> <i>{ads}</i>'
#         asyncio.run(send_to_group_channel(formatted_data))
#     return ''

# async def send_to_group_channel(data):
#     # Replace 'GROUP_CHANNEL_ID' with the actual ID of your group channel
#     await bot.send_message(chat_id='-4228000254', text=data, parse_mode="html")


# @dp.message_handler(commands=['start'])
# async def start(message: types.Message):    
#     global status
#     status = True
#     await bot.send_message(chat_id=message.chat.id, text='Повідомлення про наявність квитків та матчів увімкнені.', parse_mode="HTML")


# @dp.message_handler(commands=['stop'])
# async def start(message: types.Message):    
#     global status
#     status = False
#     await bot.send_message(chat_id=message.chat.id, text='Повідомлення про наявність квитків та матчів призупинені.', parse_mode="HTML")


# if __name__ == '__main__':
#     is_win = "win32" if sys.platform == "win32" else None
#     if not is_win: subprocess.Popen(['gunicorn', '--workers=1', '--bind=0.0.0.0:8000', 'server:app'])
#     else: subprocess.Popen(['waitress-serve', '--listen=0.0.0.0:8000', 'server:app'])

#     # Start the Telegram bot
#     executor.start_polling(dp, skip_updates=True)


# # -4228000254



from flask import Flask, request
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import re

app = Flask(__name__)

# Set up Slack API client
slack_token = "xoxb-773919780944-7051434478641-JjRVrSxpIc4n6ePbRM4WjP70"
slack_client = WebClient(token=slack_token)

# Create a new book
@app.route('/', methods=['POST'])
def create_book():
    queue, cookie, user_agent, proxy, url = request.json['queue'], request.json['cookies'], request.json['user_agent'], request.json['proxy'], request.json['url']
    data = f"*Черга:* {queue}\n*URL:* {url}\n*Proxy:* {proxy}\n"
    send_to_group_channel(data, cookie, user_agent)
    return ''

@app.route('/book', methods=['POST'])
def slack_post():
    data_to_send = f"\n*url:* {request.json['url']}\n*name:* {request.json['name']}\n*date:* {request.json['date']}\n*Кількість квитків:* {request.json['num_of_tickets']}\n*Summary:* {request.json['total_cart']}\n*proxy:* {request.json['proxy']}\n*adspower:* {request.json['adspower']}"
    send_to_group_channel(data_to_send, request.json['cookie'], request.json['user-agent'])
    return ''

@app.route('/adspower', methods=['POST'])
def send_ads():
    data, adspower_api, adspower_number = request.json['data'], request.json['adspower_api'], request.json['adspower_number']
    data_to_send = f"{data}\n*adspower API:* {adspower_api}\n*adspower id:* {adspower_number}"
    send_message_to_group_channel(data_to_send)


def send_to_group_channel(data, cookies, ua):
    cookie_file = slack_client.files_upload_v2(
            title="Cookies",
            filename="cookies.txt",
            content=str(cookies),
        )
    cookie_url = cookie_file.get("file").get("permalink")
    user_file = slack_client.files_upload_v2(
        title="User-Agent",
        filename="userAgent.txt",
        content=str(ua),
    )
    user_url = user_file.get("file").get("permalink")
    
    slack_client.chat_postMessage(
        channel="#ticketmaster_notifications_temp",
        text=f"{data}\n*User-Agent:* {user_url}\n*Cookie:* {cookie_url}",
        parse="mrkdwn"
    )


def send_message_to_group_channel(data):
    slack_client.chat_postMessage(
        channel="ticketmaster_notifications_temp",
        text=f"{data}",
        parse="mrkdwn"
    )


if __name__ == '__main__':
    app.run(debug=True, port=808)