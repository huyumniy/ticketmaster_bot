from flask import Flask, request
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import asyncio
import re

app = Flask(__name__)

# Set up Slack API client
slack_token = "xoxb-773919780944-5719663745074-6Rn1vyf3mjpYnjdXthOxd7tV"
slack_client = WebClient(token=slack_token)

# Create a new book
@app.route('/book', methods=['POST'])
def create_book():
    send_to_group_channel(request.json['url'], request.json['name'], request.json['date'], request.json['city'])
    return ''


def send_to_group_channel(url, name, date, city):
    # Replace 'CHANNEL_ID' with the actual ID of your channel
    formatted_data = f'*Назва:* {name}\n*Дата:* {date}\n*Місто:* {city}\n*url:* {url}'
    try:
        slack_client.chat_postMessage(
            channel="#ticketmaster-bot",
            text=f"{formatted_data}",
            parse="mrkdwn"
        )
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=808)
