from flask import session, redirect, url_for, render_template, request
from models import db, Dermatologist, SkinInfo, Appointment, User, Messages
from models import add_skin_info, delete_skin_info, update_skin_info, get_all_skin_info
import base64
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Mail, Message


def init_derm_routes(app, socketio):

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'hanisnabila75@gmail.com'
    app.config['MAIL_PASSWORD'] = 'dnrj yrhv zztw tjvd'
    mail = Mail(app)


    @app.route('/dlogin', methods =['GET', 'POST'])
    def dlogin():
        mesage = ''
        if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
            email = request.form['email']
            password = request.form['password']
            derm = Dermatologist.query.filter_by(email=email).first()
            if derm and derm.password == password:
                session['loggedin'] = True
                session['dermaid'] = derm.dermaid
                session['name'] = derm.name
                session['email'] = derm.email
                return redirect(url_for('ddash'))
            else:
                mesage = 'Please enter correct email / password !'
        return render_template('dlogin.html', mesage = mesage)

    @app.route('/ddash')
    def ddash():
        if 'loggedin' in session:
            derm = Dermatologist.query.get(session['dermaid'])
            if derm:
                # Retrieve current date
                today = datetime.now().date()

                # Query appointments for the current date and order them by time
                appointments = Appointment.query.filter_by(dermaid=session['dermaid'], date=today).order_by(Appointment.time).all()

                return render_template('ddash.html', user=derm, appointments=appointments)
            else:
                return "User data not found", 404
        else:
            return redirect(url_for('dlogin'))

    @app.route('/dprofile')
    def dprofile():
        if 'loggedin' in session:
            derm = Dermatologist.query.get(session['dermaid'])
            return render_template('dprofile.html', user=derm)
        else:
            return redirect(url_for('dlogin'))
        
    @app.route('/dedit_profile')
    def dedit_profile():
        if 'loggedin' in session:
            user = Dermatologist.query.get(session['dermaid'])
            return render_template('deditprofile.html', user=user)
        else:
            return redirect(url_for('login'))
        
    @app.route('/dupdate', methods=['POST'])
    def dupdate_profile():
        if 'loggedin' in session:
            user = Dermatologist.query.get(session['dermaid'])
            user.name = request.form['name']
            user.gender = request.form['gender']
            user.dob = request.form['dob']
            user.nophone = request.form['nophone']
            user.email = request.form['email']
            db.session.commit()
            return redirect(url_for('dprofile'))
        else:
            return redirect(url_for('login'))

    @app.route('/dappointment')
    def dappointment():
        if 'loggedin' in session:
            appointments = Appointment.query.filter_by(dermaid=session['dermaid']).all()
            return render_template('dapp.html', appointments=appointments)
        else:
            return redirect(url_for('dlogin'))
        
    @app.route('/approve_appointment/<int:appointment_id>', methods=['POST'])
    def approve_appointment(appointment_id):
        if 'loggedin' in session:
            appointment = Appointment.query.get(appointment_id)
            if appointment:
                appointment.status = 'Approved'
                appointment.approved_at = datetime.now()
                db.session.commit()

                user = User.query.get(appointment.userid)
                msg = Message('Appointment Approved', sender='hanisnabila75@gmail.com', recipients=[user.email])
                msg.body = f'Your appointment on {appointment.date} at {appointment.time} has been approved.'
                mail.send(msg)

                return redirect(url_for('dappointment'))
            else:
                return "Appointment not found", 404
        else:
            return redirect(url_for('dlogin'))
        

    @app.route('/reject_appointment/<int:appointment_id>', methods=['POST'])
    def reject_appointment(appointment_id):
        if 'loggedin' in session:
            appointment = Appointment.query.get(appointment_id)
            if appointment:
                appointment.status = 'Rejected'
                appointment.rejected_at = datetime.now()
                db.session.commit()
                return redirect(url_for('dappointment'))
            else:
                return "Appointment not found", 404
        else:
            return redirect(url_for('dlogin'))


    @app.route('/dermcontact', methods=['GET', 'POST'])
    def derm_contact():
        if 'loggedin' not in session:
            return redirect(url_for('dlogin'))

        if request.method == 'POST':
            userid = request.form.get('userid')
            return redirect(url_for('derm_contact', userid=userid))

        derm_id = session['dermaid']
        users = db.session.query(User).join(Messages, User.userid == Messages.sender_id).filter(Messages.receiver_id == derm_id).distinct().all()

        unread_counts = {}
        for user in users:
            count = Messages.query.filter_by(sender_id=user.userid, receiver_id=derm_id, is_read=False).count()
            unread_counts[user.userid] = count

        userid = request.args.get('userid')
        messages = []

        if userid:
            userid = int(userid)
            user = User.query.get(userid)
            messages_sender = Messages.query.filter_by(sender_id=derm_id, receiver_id=userid).all()
            messages_receiver = Messages.query.filter_by(sender_id=userid, receiver_id=derm_id).all()
            messages = sorted(messages_sender + messages_receiver, key=lambda x: x.timestamp)

            # Mark messages as read
            for message in messages_receiver:
                message.is_read = True
                db.session.add(message)
            db.session.commit()

            # Emit event to remove notification
            socketio.emit('remove_notification', {'sender': userid}, room=f"derm-{derm_id}")

        else:
            user = None

        return render_template('dermchat.html', users=users, user=user, messages=messages, unread_counts=unread_counts)


    ##### SKIN INFORMATION ##########

    # Route to display dermatology skin information
    @app.route('/dskininfo')
    def dskininfo():
        if 'loggedin' in session:
            skin_infos = get_all_skin_info()

            # Convert binary image data to base64 encoding
            for info in skin_infos:
                info.image = base64.b64encode(info.image).decode('utf-8')

            return render_template('dskininfo.html', skin_infos=skin_infos)
        else:
            return redirect(url_for('dlogin'))  # Redirect to dermatologist login if not logged in
        
        
    @app.route('/addskininfo', methods=['POST', 'GET'])
    def add_skin_info_route():
        if 'loggedin' in session:
            if request.method == 'POST':
                title = request.form['title']
                description = request.form['description']
                image = request.files['image']

                # Check if an image file was actually uploaded
                if image and allowed_file(image.filename):
                    # Secure the filename
                    filename = secure_filename(image.filename)
                    # Read the image data in binary mode
                    image_data = image.read()

                    # Function to add skin info to the database
                    result = add_skin_info(title, description, image_data)
                    
                    if result:
                        return redirect(url_for('dskininfo'))
                    else:
                        return 'Failed to add skin information', 500
                else:
                    return 'Invalid file or file type not allowed', 400
            else:
                return render_template('daddinfo.html')  # Render the form for adding skin information
        else:
            return redirect(url_for('dlogin'))  # Redirect to dermatologist login if not logged in

    def allowed_file(filename):
        # Ensure files have one of the allowed extensions
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    # Route to edit dermatology skin information
    @app.route('/editskininfo/<int:info_id>', methods=['GET', 'POST'])
    def edit_skin_info_route(info_id):
        if 'loggedin' in session:
            if request.method == 'POST':
                # Get form data
                title = request.form['title']
                description = request.form['description']
                image = request.files['image'] if 'image' in request.files else None

                # Check if an image file was actually uploaded
                if image and allowed_file(image.filename):
                    # Secure the filename
                    filename = secure_filename(image.filename)
                    # Read the image data in binary mode
                    image_data = image.read()
                else:
                    # If no new image is uploaded, keep the existing image
                    skin_info = SkinInfo.query.get(info_id)
                    image_data = skin_info.image

                # Update skin information in the database
                result = update_skin_info(info_id, title, description, image_data)
                if result:
                    return redirect(url_for('dskininfo'))
                else:
                    return 'Failed to update skin information', 500
            else:
                # Fetch existing skin information based on ID
                skin_info = SkinInfo.query.get(info_id)
                if skin_info:
                    return render_template('deditinfo.html', skin_info=skin_info)
                else:
                    return 'Skin information not found', 404
        else:
            return redirect(url_for('dlogin'))  # Redirect to dermatologist login if not logged in


    # Route to delete dermatology skin information
    @app.route('/deleteskininfo/<int:info_id>', methods=['POST'])
    def delete_skin_info_route(info_id):
        if 'loggedin' in session:
            result = delete_skin_info(info_id)
            if result:
                return redirect(url_for('dskininfo'))
        else:
            return redirect(url_for('dlogin'))  # Redirect to dermatologist login if not logged in
        
    # Route to display a single article
    @app.route('/article/<int:info_id>')
    def article(info_id):
        if 'loggedin' in session:
            skin_info = SkinInfo.query.get(info_id)
            if skin_info:
                # Convert binary image data to base64 encoding
                skin_info.image = base64.b64encode(skin_info.image).decode('utf-8')
                return render_template('darticles.html', skin_info=skin_info)
            else:
                return "Article not found", 404
        else:
            return redirect(url_for('dlogin'))
