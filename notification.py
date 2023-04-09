from flask import Flask, jsonify
from flask_cors import CORS
from twilio.rest import Client
import os
import requests
import json
import amqp_setup


monitorBindingKey='*.notif'

app = Flask(__name__)
CORS(app)

user_url = "http://127.0.0.1:5000/user/phoneNum/"

# Twilio account credentials
TWILIO_ACCOUNT_SID = "ACb73a42a689c04ad6bf175a645cfa9282"
TWILIO_AUTH_TOKEN = "72769e6ae2bb619d91fd600733634fbb"
TWILIO_PHONE_NUMBER = "+15178269570"

# send user reminder when they are 3 places away from the seat selection page
def send_notif_queue(user_id):
    try:
        result = invoke_http(user_url + user_id, method='GET')
        code = result['code']
        phone_num = result['phone_num']

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        if code in (200, 300):
            message = client.messages.create(
                to="+65" + str(phone_num),
                from_=TWILIO_PHONE_NUMBER,
                body="You are currently 3 places away from the Seat Selection Page! "
                     "\nDo take note that you will have 10 mins to select your seats after entering!"
            )
            return jsonify({"code": 200, "message": "Notification is sent"})
        else:
            return jsonify({"code": 404, "message": "Notification is not found"})

    except Exception as e:
        return jsonify({"code": 500, "message": "Failed to send notification: " + str(e)})


def recieveQueue():
    amqp_setup.check_setup()
    print("entered notif")
    queue_name = 'Notification'

    # set up a consumer and start to wait for coming messages
    amqp_setup.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    amqp_setup.channel.start_consuming() # an implicit loop waiting to receive messages;
    #it doesn't exit by default. Use Ctrl+C in the command window to terminate it.

def callback(channel, method, properties, body): # required signature for the callback; no return
    print("\nReceived an order log by " + __file__)

    channel.basic_ack(delivery_tag=method.delivery_tag)
    send_notif_queue(json.loads(body))
    print() # print a new line feed

if __name__ == '__main__':
    print("This is flask " + os.path.basename(__file__) + " for sending a notification...")
    recieveQueue()
    app.run(debug=True, port=5100)
