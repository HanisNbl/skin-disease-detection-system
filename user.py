from flask import session, redirect, url_for, render_template, request, flash, send_file
from models import db, User, Dermatologist, SkinImages, Appointment, Messages, get_all_skin_info
from prediction import *
import base64
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import os

def init_user_routes(app):

    @app.route('/generate_report/<int:image_id>', methods=['GET'])
    def generate_report(image_id):
        if 'loggedin' in session:
            image = SkinImages.query.filter_by(id=image_id, userid=session['userid']).first()
            if image:
                user = User.query.get(session['userid'])
                if not user:
                    return "User not found", 404

                # Create a buffer
                buffer = BytesIO()
                
                # Create a SimpleDocTemplate
                pdf = SimpleDocTemplate(buffer, pagesize=letter)
                elements = []

                # Styles
                styles = getSampleStyleSheet()
                
                # Logo and system name
                logo_path = os.path.join(app.static_folder, 'img/logo.png')
                logo = Image(logo_path, width=50, height=50)
                system_name = Paragraph("Skin Good", styles['Title'])


                # Title and user information
                title = Paragraph("Skin Image Report", styles['Title'])
                elements.append(title)
                elements.append(Spacer(1, 12))

                # Display the skin image
                image_io = BytesIO(image.image_data)
                skin_image = Image(image_io, width=250, height=250)
                elements.append(skin_image)
                elements.append(Spacer(1, 12))

                # Predicted condition and upload date
                prediction_info = [
                    ['Name:', user.name],
                    ['Predicted Condition:', image.predictions],
                    ['Upload Date:', image.upload_date]
                ]
                table = Table(prediction_info, colWidths=[150, 300])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (1, 0), colors.beige),
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)

                # Build the PDF
                pdf.build(elements)
                buffer.seek(0)

                # Send the PDF as a downloadable file
                return send_file(buffer, as_attachment=True, download_name=f'report_{image_id}.pdf')

            else:
                return "Image not found or unauthorized", 404
        else:
            return 'Unauthorized', 401




    @app.route('/')
    def home():
        user_count = User.query.count()
        derm_count = Dermatologist.query.count()
        return render_template('homepage.html', user = user_count, derm = derm_count)
    
    # Define allowed extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route('/upload_image', methods=['POST'])
    def upload_image():
        if 'file' not in request.files:
            return 'No file part'

        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        
        if file and allowed_file(file.filename):
            image_data = file.read()

            # Call the predict_disease function to get predictions
            img, predicted_class_name, treatment_info, confidence = predict_disease(image_data)

            # Convert the image to base64 for displaying in HTML
            _, encoded_image = cv2.imencode('.jpg', img)
            encoded_image = base64.b64encode(encoded_image).decode('utf-8')

            # Save the uploaded image to the database
            if 'loggedin' in session:
                userid = session['userid']
                new_skin_image = SkinImages(userid=userid, image_data=image_data, predictions=predicted_class_name)
                db.session.add(new_skin_image)
                db.session.commit()

            return render_template('userskincheck.html', class_name=predicted_class_name, image=encoded_image, treatment=treatment_info, confidence=confidence)
        else:
            return 'File type not allowed'

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        message = ''
        if request.method == 'POST' and all(key in request.form for key in ['name', 'gender', 'dob', 'nophone', 'password', 'email']):
                new_user = User(
                    name=request.form['name'],
                    gender=request.form['gender'],
                    dob=request.form['dob'],
                    nophone=request.form['nophone'],
                    email = request.form['email'],
                    password=request.form['password']
                )
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))
        else:
            message = 'Please fill out the form!'
        return render_template('userregister.html', message=message)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        message = ''
        if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
            email = request.form['email']
            password = request.form['password']
            user = User.query.filter_by(email=email).first()
            if user and user.password == password:
                session['loggedin'] = True
                session['userid'] = user.userid
                session['name'] = user.name
                session['email'] = user.email
                app.logger.info(f"User {user.name} logged in successfully.")  # Debugging message
                return redirect(url_for('userdash'))
            else:
                message = 'Please enter correct email or password!'
        return render_template('userlogin.html', message=message)

    @app.route('/userdash')
    def userdash():
        if 'loggedin' in session:
            user = User.query.get(session['userid'])
            if user:
                return render_template('userdash.html', user=user)
            else:
                return "User data not found", 404
        else:
            return redirect(url_for('login'))

    @app.route('/userskincheck')
    def userskincheck():
        if 'loggedin' in session:
            user = User.query.get(session['userid'])
            return render_template('userskincheck.html', user=user)
        else:
            return redirect(url_for('login'))

    @app.route('/userconsult')
    def user_consultation():
        if 'loggedin' in session:
            dermatologists = Dermatologist.query.all()
            return render_template('userconsult.html', dermatologists=dermatologists)
        else:
            return redirect(url_for('login'))

    @app.route('/userprofile')
    def userprofile():
        if 'loggedin' in session:
            user = User.query.get(session['userid'])
            return render_template('userprofile.html', user=user)
        else:
            return redirect(url_for('login'))

    @app.route('/edit_profile')
    def edit_profile():
        if 'loggedin' in session:
            user = User.query.get(session['userid'])
            return render_template('ueditprofile.html', user=user)
        else:
            return redirect(url_for('login'))

    @app.route('/update_profile', methods=['POST'])
    def update_profile():
        if 'loggedin' in session:
            user = User.query.get(session['userid'])
            user.name = request.form['name']
            user.gender = request.form['gender']
            user.dob = request.form['dob']
            user.nophone = request.form['nophone']
            user.email = request.form['email']
            db.session.commit()
            return redirect(url_for('userprofile'))
        else:
            return redirect(url_for('login'))

    @app.route('/uhistory')
    def userhistory():
        if 'loggedin' in session:
            images = SkinImages.query.filter_by(userid=session['userid']).all()
            
            # Convert each image's binary data to a Base64 string
            for image in images:
                image.base64_data = base64.b64encode(image.image_data).decode('utf-8')

            return render_template('uhistory.html', images=images)
        else:
            return 'Unauthorized', 401


    @app.route('/logout')
    def logout():
        session.pop('loggedin', None)
        session.pop('userid', None)
        session.pop('email', None)
        return redirect(url_for('home'))

    ############### APPOINTMENT BOOKING ###################
    @app.route('/book_appointment', methods=['GET', 'POST'])
    def book_appointment():
        if 'loggedin' not in session:
            return redirect(url_for('login'))

        if request.method == 'POST':
            date = request.form['date']
            time = request.form['time']
            platform = request.form['platform']
            message = request.form['message']
            dermaid = request.form['dermaid']
            
            appointment = Appointment(
                userid=session['userid'],
                dermaid=dermaid,
                date=datetime.strptime(date, '%Y-%m-%d').date(),
                time=datetime.strptime(time, '%H:%M').time(),
                message=message,
                platform=platform
            )
            db.session.add(appointment)
            db.session.commit()
            flash('Appointment request submitted. Awaiting dermatologist approval.', 'success')
            return redirect(url_for('appointment_status'))

        dermatologists = Dermatologist.query.all()
        return render_template('ubookapp.html', dermatologists=dermatologists)

    @app.route('/appointment_status')
    def appointment_status():
        if 'loggedin' not in session:
            return redirect(url_for('login'))

        user_appointments = Appointment.query.filter_by(userid=session['userid']).all()
        return render_template('uappointment.html', appointments=user_appointments)

    @app.route('/edit_appointment/<int:appointment_id>', methods=['GET', 'POST'])
    def edit_appointment(appointment_id):
        if 'loggedin' not in session:
            return redirect(url_for('login'))
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return "Appointment not found", 404

        if request.method == 'POST':
            appointment.date = request.form['date']
            appointment.time = request.form['time']
            appointment.platform = request.form['platform']
            appointment.message = request.form['message']
            appointment.dermaid = request.form['dermaid']
            db.session.commit()
            return redirect(url_for('appointment_status'))

        dermatologists = Dermatologist.query.all()
        return render_template('ueditapp.html', appointment=appointment, dermatologists=dermatologists)

    @app.route('/delete_appointment/<int:appointment_id>', methods=['GET', 'POST'])
    def delete_appointment(appointment_id):
        if 'loggedin' not in session:
            return redirect(url_for('login'))
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return "Appointment not found", 404

        db.session.delete(appointment)
        db.session.commit()
        return redirect(url_for('appointment_status'))
    

    ############ ONLINE CHAT ##################

    @app.route("/message")
    def message():
        return render_template("message.html")

    @app.route('/usercontact', methods=['GET', 'POST'])
    def user_contact():
        if 'loggedin' not in session:
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            dermaid = request.form.get('dermaid')
            return redirect(url_for('user_contact', dermaid=dermaid))

        dermatologists = Dermatologist.query.all()
        dermaid = request.args.get('dermaid')
        messages = []

        for dermatologist in dermatologists:
            unread_count = Messages.query.filter_by(receiver_id=session['userid'], sender_id=dermatologist.dermaid, is_read=False).count()
            dermatologist.unread_count = unread_count

        if dermaid:
            dermaid = int(dermaid)
            dermatologist = Dermatologist.query.get(dermaid)
            messages_sender = Messages.query.filter_by(sender_id=session['userid'], receiver_id=dermaid).all()
            messages_receiver = Messages.query.filter_by(sender_id=dermaid, receiver_id=session['userid']).all()
            messages = sorted(messages_sender + messages_receiver, key=lambda x: x.timestamp)

            # Mark messages as read
            for message in messages_receiver:
                message.is_read = True
                db.session.add(message)
            db.session.commit()

        else:
            dermatologist = None
        
        return render_template('usercontact.html', dermatologists=dermatologists, dermatologist=dermatologist, messages=messages)

############# articles ###################

    @app.route('/articles')
    def articles():
        if 'loggedin' in session:
            skin_infos = get_all_skin_info()

            # Convert binary image data to base64 encoding
            for info in skin_infos:
                info.image = base64.b64encode(info.image).decode('utf-8')

            return render_template('articles.html', skin_infos=skin_infos)
        else:
            return redirect(url_for('login'))  # Redirect to dermatologist login if not logged in
        