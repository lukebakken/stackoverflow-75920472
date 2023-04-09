from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import amqp_setup
import json
import requests
from invokes import invoke_http
import pika


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:8889/queue_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

CORS(app)

class Queue(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Enum('waiting', 'serving'), nullable=False)
    concert_id = db.Column(db.Integer, nullable=False, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
@app.route('/waiting-queue/<int:user_id>/<int:concert_id>')
def waiting_queue(user_id, concert_id):
    try:
        user = Queue.query.filter_by(user_id=user_id, concert_id=concert_id).first()
        if user is None:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        if user.status == 'serving':
            return jsonify({'queue_position': 0, 'status': 'serving'}), 200

        waiting_count = Queue.query.filter(Queue.status == 'waiting', Queue.concert_id == user.concert_id, Queue.created_at < user.created_at).count()
        
        if waiting_count == 3:
            print("waiting...")
            sendNotif(user_id)

        return jsonify({'queue_position': waiting_count + 1, 'status': 'waiting'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': "Error occurred when getting user queue position: " + str(e)}), 500
def sendNotif(user_id):
    # 2. calls notification 
    print('\n-----Invoking notification microservice-----')
    print('\n\n-----Publishing the notif message with routing_key=queue.notif-----')

    # notif_result = invoke_http('http://127.0.0.1:5100/sendQueueNotification/' + user_id, method='POST', json=user_id)
    
    message = json.dumps(user_id)

    amqp_setup.channel.basic_publish(exchange=amqp_setup.exchangename, routing_key="queue.notif", 
    body=message, properties=pika.BasicProperties(delivery_mode = 2)) 
    
    print("\nRequest published to RabbitMQ Exchange.\n")
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5009, debug=True)
