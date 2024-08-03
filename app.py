from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from telegram import Bot
import os

TELEGRAM_BOT_TOKEN= "7294713269:AAFwKEXMbLFMwKMDe6likn7NEbKEuLbVtxE"
TELEGRAM_CHAT_ID= '-1002070732383'

# Load environment variables from .env file
load_dotenv()

# Generate encryption key and secret key if not present
def generate_keys():
    if not os.getenv('SECRET_KEY'):
        secret_key = os.urandom(24).hex()
        with open('.env', 'a') as f:
            f.write(f'\nSECRET_KEY={secret_key}')

generate_keys()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cricket.db'
db = SQLAlchemy(app)
socketio = SocketIO(app)
telegram_bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    team = db.Column(db.String(50), nullable=False)

db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    username = data['username']
    user_id = get_telegram_user_id(username)
    if user_id and is_user_in_group(user_id):
        return jsonify({'status': 'success'})
    return jsonify({'status': 'fail'})

def get_telegram_user_id(username):
    try:
        updates = telegram_bot.get_updates()
        for update in updates:
            if update.message and update.message.from_user.username == username:
                return update.message.from_user.id
    except Exception as e:
        print(e)
    return None

def is_user_in_group(user_id):
    try:
        chat_member = telegram_bot.get_chat_member(telegram_chat_id, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(e)
    return False

@socketio.on('join')
def handle_join(data):
    username = data['username']
    team = data['team']
    player = Player.query.filter_by(username=username).first()
    if not player:
        player = Player(username=username, team=team)
        db.session.add(player)
        db.session.commit()
    emit('player_joined', {'username': username, 'team': team}, broadcast=True)

@socketio.on('score')
def handle_score(data):
    team = data['team']
    score = data['score']
    # Update score logic here
    emit('score_update', {'team': team, 'score': score}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
