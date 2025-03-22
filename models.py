from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, nullable=False)
    receiver_id = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp())
    is_read = db.Column(db.Boolean, default=False)

class User(db.Model):
    userid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(100), nullable=False)
    nophone = db.Column(db.String(11), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

# Define the Admin model
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

# Define the Dermatologist model
class Dermatologist(db.Model):
    dermaid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(100), nullable=False)
    nophone = db.Column(db.String(11), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

class SkinImages(db.Model):
    __tablename__ = 'skinimages'  # Specify the table name explicitly
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    image_data = db.Column(db.LargeBinary, nullable=False)
    predictions = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.current_timestamp())

class SkinInfo(db.Model):
    __tablename__ = 'skininfo' 
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.LargeBinary)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

class Appointment(db.Model):
    appointment_id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'))
    dermaid = db.Column(db.Integer, db.ForeignKey('dermatologist.dermaid'))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    platform = db.Column(db.String(50))
    message = db.Column(db.Text)
    status = db.Column(db.String(100), default='Pending')
    approved_at = db.Column(db.TIMESTAMP)
    rejected_at = db.Column(db.TIMESTAMP)

    # Relationship to User
    user = db.relationship('User', backref=db.backref('appointments', lazy=True))

    # Relationship to Dermatologist
    dermatologist = db.relationship('Dermatologist', backref=db.backref('appointments', lazy=True))

def add_skin_info(title, description, image_data):
    new_skin_info = SkinInfo(title=title, description=description, image=image_data)
    db.session.add(new_skin_info)
    db.session.commit()
    return new_skin_info.id

def delete_skin_info(info_id):
    skin_info = SkinInfo.query.get(info_id)
    if skin_info:
        db.session.delete(skin_info)
        db.session.commit()
        return True
    else:
        return False

def update_skin_info(info_id, title, description, image_data):
    skin_info = SkinInfo.query.get(info_id)
    if skin_info:
        skin_info.title = title
        skin_info.description = description
        skin_info.image = image_data
        db.session.commit()
        return True
    else:
        return False

def get_all_skin_info():
    return SkinInfo.query.all()