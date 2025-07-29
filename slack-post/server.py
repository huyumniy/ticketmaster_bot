from flask import Flask, request
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import re

app = Flask(__name__)

# Load Slack token from JSON file
json_file = os.path.join(os.getcwd(), "slack_token.json")
try:
    slack_token = json.load(open(json_file)).get("token")
    if not slack_token:
        raise ValueError("Token not found.")
    print("Slack token loaded.")
except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
    print(f"Error loading token: {e}")
    slack_token = None

# Initialize Slack client
client = WebClient(token=slack_token) if slack_token else None

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
    cookie_file = client.files_upload_v2(
            title="Cookies",
            filename="cookies.txt",
            content=str(cookies),
        )
    cookie_url = cookie_file.get("file").get("permalink")
    user_file = client.files_upload_v2(
        title="User-Agent",
        filename="userAgent.txt",
        content=str(ua),
    )
    user_url = user_file.get("file").get("permalink")
    
    client.chat_postMessage(
        channel="#ticketmaster-bot",
        text=f"{data}\n*User-Agent:* {user_url}\n*Cookie:* {cookie_url}",
        parse="mrkdwn"
    )


def send_message_to_group_channel(data):
    client.chat_postMessage(
        channel="ticketmaster-bot",
        text=f"{data}",
        parse="mrkdwn"
    )


if __name__ == '__main__':
    app.run(debug=True, port=808)
