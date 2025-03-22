# app.py
from flask import Flask
from prediction import predict_disease
from admin import init_admin_routes
from user import init_user_routes
from derm import init_derm_routes
from chat import chat_init_routes
from flask_socketio import SocketIO
from models import db
import os

# Create the Flask app instance
app = Flask(__name__)
app.config["DEBUG"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/skindisease'  # Update with your MySQL credentials and database name
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'img')
app.secret_key = 'silent'

# Initialize SQLAlchemy with the Flask app
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

init_admin_routes(app)
init_user_routes(app)
predict_disease
init_derm_routes(app, socketio)
chat_init_routes(socketio, app)

if __name__ == "__main__":
    socketio.run(app, debug=True)

