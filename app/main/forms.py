from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, BooleanField
from wtforms.validators import  Length, DataRequired, Email, EqualTo, ValidationError
from wtforms_sqlalchemy.fields import  QuerySelectField, QuerySelectMultipleField
from wtforms.widgets import ListWidget,CheckboxInput
from flask_login import current_user

from app import db
from app.main.models import Major, Student
import sqlalchemy as sqla

# def get_major():
#     return db.session.scalars(sqla.select(Major))

# def get_majorlabel (theMajor):
#     return theMajor.name

class CourseForm(FlaskForm):
    coursenum = StringField('Course Number',[Length(min=3, max=6)])
    title = StringField('Course Title', validators = [DataRequired()])
    major = QuerySelectField ('Major',
                              query_factory = lambda : db.session.scalars(sqla.select(Major)),
                              get_label =  lambda theMajor : theMajor.name,
                              allow_blank = False)
    submit = SubmitField('Post')

class EditForm(FlaskForm):
    firstname = StringField('First Name',validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    address =  TextAreaField('Address', [Length(min=0, max=200)])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Password', validators=[DataRequired(), EqualTo('password')])
    majors = QuerySelectMultipleField ('Majors',
                query_factory = lambda : db.session.scalars(sqla.select(Major).order_by(Major.name)),
                get_label =  lambda theMajor : theMajor.name,
                widget=ListWidget(prefix_label=False), 
                option_widget=CheckboxInput())
    submit = SubmitField('Post')
        
    def validate_email(self, email):
        query = sqla.select(Student).where(Student.email == email.data)
        student = db.session.scalars(query).first()
        if student is not None:
            if student.id != current_user.id:
                raise ValidationError('The email already exists! Please use a different email.')

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')