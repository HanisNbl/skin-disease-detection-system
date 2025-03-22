import os
from flask import request, jsonify
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from models import db, Messages, User, Dermatologist

UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def chat_init_routes(socketio, app):

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    @socketio.on("join")
    def handle_join(data):
        room = data['room']
        join_room(room)
        send(f"{data['username']} has joined the room.", to=room)

    @socketio.on("leave")
    def handle_leave(data):
        room = data['room']
        leave_room(room)
        send(f"{data['username']} has left the room.", to=room)

    @socketio.on("private_message")
    def handle_private_message(data):
        room = data['room']
        message = data['message']
        sender = data['sender']
        receiver = data['receiver']
        image = data.get('image', None)

        # Save the message to the database
        new_message = Messages(sender_id=sender, receiver_id=receiver, message=message, image=image)
        db.session.add(new_message)
        db.session.commit()

        # Fetch the sender's name
        sender_user = User.query.get(sender)
        sender_name = sender_user.name if sender_user else 'Unknown'

        # Send the message to the specified room
        response_message = {
            'message': message,
            'sender': sender,
            'sender_name': sender_name,
            'receiver': receiver,
            'image': image,
            'timestamp': data['timestamp']
        }
        emit("private_message", response_message, room=room)
        
        # Emit notification for the dermatologist
        unread_count = Messages.query.filter_by(sender_id=sender, receiver_id=receiver, is_read=False).count()
        notification_message = f"{unread_count} new messages from {sender_name}"
        emit("notification", {'message': notification_message, 'sender': sender}, room=room)

    @app.route('/send_message', methods=['POST'])
    def send_message():
        room = request.form['room']
        message = request.form['message']
        sender = request.form['sender']
        receiver = request.form['receiver']
        timestamp = request.form['timestamp']

        # Handle file upload
        file = request.files.get('image')
        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_message = Messages(sender_id=sender, receiver_id=receiver, message=message, image=filename)
        db.session.add(new_message)
        db.session.commit()

        # Fetch the sender's name
        sender_user = User.query.get(sender)
        sender_name = sender_user.name if sender_user else 'Unknown'

        response_message = {
            'message': message,
            'sender': sender,
            'sender_name': sender_name,
            'receiver': receiver,
            'image': filename,
            'timestamp': timestamp
        }

        socketio.emit('private_message', response_message, room=room)

        # Notify the dermatologist in their notification room
        derm_room = f"derm-{receiver}"
        socketio.emit('private_message', response_message, room=derm_room)

        # Emit notification for the dermatologist
        unread_count = Messages.query.filter_by(sender_id=sender, receiver_id=receiver, is_read=False).count()
        notification_message = f"{unread_count} new messages from {sender_name}"
        socketio.emit('notification', {'message': notification_message, 'sender': sender}, room=derm_room)

        return jsonify({'success': True, 'message': response_message})
