import requests
import json

# Define the URL to which you want to send the request
url = "http://localhost:808/book"

# Create the JSON object

data = {'url': 'test', 'name': 'test', 'date': 'test', 'city': 'test'}
# Convert the JSON object to a string
json_data = json.dumps(data)

# Set the headers to specify the content type as JSON
headers = {
    "Content-Type": "application/json"
}

# Send the POST request
response = requests.post(url, data=json_data, headers=headers)

# Check the response status code
if response.status_code == 200:
    print("POST request successful!")
else:
    print("POST request failed.")