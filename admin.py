# admin.py
from flask import session, redirect, url_for, render_template, request, make_response
from models import db, User, Dermatologist, SkinImages, Admin
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import jsonify
from collections import Counter

def init_admin_routes(app):

    @app.route('/api/SkinDiseasePredictions', methods=['GET'])
    def get_skin_disease_predictions():
        # Query and prepare data (replace with your actual logic)
        predictions = SkinImages.query.with_entities(SkinImages.predictions).all()
        predictions_list = [pred[0] for pred in predictions]
        disease_counts = dict(Counter(predictions_list))
        disease_labels = list(disease_counts.keys())
        disease_data = list(disease_counts.values())

        # Return JSON response
        return jsonify({
            'disease_labels': disease_labels,
            'disease_data': disease_data
        })

    @app.route('/generate_report')
    def generate_report_pdf():
        if 'adminlogin' not in session:
            return redirect(url_for('alogin'))
        
        user_count = User.query.count()
        derm_count = Dermatologist.query.count()

        # Fetch skin disease predictions data
        predictions = SkinImages.query.with_entities(SkinImages.predictions).all()
        predictions_list = [pred[0] for pred in predictions]
        disease_counts = dict(Counter(predictions_list))

        # Create a PDF buffer using ReportLab
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        
        # PDF Title
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawCentredString(300, 750, "Admin Dashboard Report")
        pdf.setFont("Helvetica", 12)

        # PDF Content - Total Users and Dermatologists
        pdf.drawString(50, 700, f"Total Users: {user_count}")
        pdf.drawString(50, 680, f"Total Dermatologists: {derm_count}")

        # PDF Content - Skin Disease Predictions
        pdf.drawString(50, 650, "Skin Disease Predictions:")
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(70, 630, "No")
        pdf.drawString(150, 630, "Types of Skin Disease")
        pdf.drawString(300, 630, "Total Count")
        pdf.setFont("Helvetica", 12)

        y = 610
        for index, (label, count) in enumerate(disease_counts.items(), start=1):
            pdf.drawString(70, y, f"{index}")
            pdf.drawString(150, y, f"{label}")
            pdf.drawString(300, y, f"{count}")
            y -= 20
        
        # Save the PDF file
        pdf.save()

        # Reset the buffer position and create a Flask response
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=admin_report.pdf'
        return response
    

    @app.route('/alogin', methods=['GET', 'POST'])
    def alogin():
        mesage = ''
        if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
            email = request.form['email']
            password = request.form['password']
            admin = Admin.query.filter_by(email=email).first()
            if admin and admin.password == password:
                session['adminlogin'] = True
                session['id'] = admin.id
                session['name'] = admin.name
                session['email'] = admin.email

                user_count = User.query.count()
                derm_count = Dermatologist.query.count()
                return render_template('adash.html', user_count=user_count, derm_count=derm_count)
            else:
                mesage = 'Please enter correct email / password !'
        return render_template('alogin.html', mesage=mesage)

    @app.route('/adash')
    def adash():
        if 'adminlogin' in session:
            user_count = User.query.count()
            derm_count = Dermatologist.query.count()
            return render_template('adash.html',user_count=user_count, derm_count=derm_count)
        else:
            return redirect(url_for('alogin'))

    @app.route('/userlist', methods=['GET', 'POST'])
    def auserlist():
        if 'adminlogin' in session:
            if request.method == 'POST':
                search_query = request.form.get('search_query', '')
                if search_query.isdigit():
                    users = User.query.filter_by(userid=int(search_query)).all()
                else:
                    users = User.query.filter(User.name.like(f'%{search_query}%')).all()
            else:
                users = User.query.all()
            return render_template('auserlist.html', users=users)
        else:
            return redirect(url_for('alogin'))

    @app.route('/deleteuser/<int:userid>', methods=['GET', 'POST'])
    def deleteuser(userid):
        if 'adminlogin' not in session:
            return redirect(url_for('/alogin'))
        
        user = User.query.get(userid)
        if not user:
            return "User not found", 404
        
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for('auserlist'))
    
    @app.route('/adminprofile')
    def adminprofile():
        if 'adminlogin' in session:
            user = Admin.query.get(session['id'])
            return render_template('aprofile.html', user=user)
        else:
            return redirect(url_for('login'))

    @app.route('/adminedit')
    def admin_edit_profile():
        if 'adminlogin' in session:
            user = Admin.query.get(session['id'])
            return render_template('aeditprofile.html', user=user)
        else:
            return redirect(url_for('login'))

    @app.route('/admin_update_profile', methods=['POST'])
    def admin_update_profile():
        if 'adminlogin' in session:
            user = Admin.query.get(session['id'])
            user.name = request.form['name']
            user.gender = request.form['gender']
            user.dob = request.form['dob']
            user.email = request.form['email']
            db.session.commit()
            return redirect(url_for('adminprofile'))
        else:
            return redirect(url_for('login'))