from typing import Optional
import sqlalchemy as sqla
import sqlalchemy.orm as sqlo
from datetime import datetime, timezone
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

@login.user_loader
def load_user(id):
    return db.session.get(Student, int(id))

students_majors_table = db.Table(
    'students_majors_table',
    db.metadata,
    sqla.Column('student_id', sqla.Integer, sqla.ForeignKey('student.id'), primary_key= True),
    sqla.Column('major_id', sqla.Integer, sqla.ForeignKey('major.id'), primary_key= True)
)

class Major(db.Model):
    id : sqlo.Mapped[int] = sqlo.mapped_column(primary_key=True)
    name : sqlo.Mapped[str] = sqlo.mapped_column(sqla.String(20))
    department : sqlo.Mapped[str] =  sqlo.mapped_column(sqla.String(150))
    #relationship
    courses : sqlo.WriteOnlyMapped['Course'] = sqlo.relationship(back_populates= 'major')
    students_in_major : sqlo.WriteOnlyMapped['Student'] = sqlo.relationship(
        secondary= students_majors_table,
        primaryjoin= (students_majors_table.c.major_id == id),
        back_populates= 'majors_of_student')

    # methods
    def __repr__(self):
        return '<Major  - {} name: {} - department: {}>'.format(self.id, self.name,self.department)
    
    def get_name(self):
        return self.name
    
    def get_department(self):
        return self.department

    def get_courses(self):
        return db.session.scalars(self.courses.select()).all()
     
    def get_students(self):
        return db.session.scalars(self.students_in_major.select()).all()

class Course(db.Model):
    id : sqlo.Mapped[int] = sqlo.mapped_column(primary_key=True)
    majorid : sqlo.Mapped[int] = sqlo.mapped_column(sqla.ForeignKey(Major.id), index = True)
    coursenum : sqlo.Mapped[str] = sqlo.mapped_column(sqla.String(4), index = True)   
    title : sqlo.Mapped[str] = sqlo.mapped_column(sqla.String(150))
    # relationships
    major : sqlo.Mapped[Major] = sqlo.relationship( back_populates= 'courses')
    roster : sqlo.WriteOnlyMapped['Enrolled'] = sqlo.relationship(back_populates= 'course_enrolled')

    # methods
    def __repr__(self):
        return '<Course id: {} - coursenum: {} - title: {}>'.format(self.id,self.coursenum, self.title)

    def get_coursenum(self):
        return self.coursenum
    
    def get_title(self):
        return self.title
    
    def get_major(self):
        return self.major
    

class Student(UserMixin, db.Model):
    id : sqlo.Mapped[int] = sqlo.mapped_column(primary_key=True)
    username : sqlo.Mapped[str] = sqlo.mapped_column(sqla.String(64), index = True, unique = True)    
    password_hash : sqlo.Mapped[Optional[str]] = sqlo.mapped_column(sqla.String(256)) 
    firstname : sqlo.Mapped[str] = sqlo.mapped_column(sqla.String(100))    
    lastname : sqlo.Mapped[str] = sqlo.mapped_column(sqla.String(100))
    address : sqlo.Mapped[str] = sqlo.mapped_column(sqla.String(256))  
    email : sqlo.Mapped[str] = sqlo.mapped_column(sqla.String(120), index = True, unique = True) 
    last_seen : sqlo.Mapped[Optional[datetime]] = sqlo.mapped_column(default = lambda : datetime.now(timezone.utc))
    #relationships
    majors_of_student : sqlo.WriteOnlyMapped['Major'] = sqlo.relationship(
        secondary= students_majors_table,
        primaryjoin= (students_majors_table.c.student_id == id),
        back_populates= 'students_in_major')
    
    enrollments : sqlo.WriteOnlyMapped['Enrolled'] = sqlo.relationship(back_populates= 'student_enrolled')

    #methods
    def __repr__(self):
        return '<Student {} - {} - {} {} - {} - {} - {};>'.format(self.id,self.username, self.firstname, self.lastname, self.email, self.address, self.last_seen)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash , password)
    
    def get_username(self):
        return self.username
    
    def get_firstname(self):
        return self.firstname
    
    def get_lastname(self):
        return self.lastname
    
    def get_email(self):
        return self.email
    
    def get_address(self):
        return self.address
    
    def get_last_seen_date(self):
        return self.last_seen
    
    def get_majors(self):
        return db.session.scalars(self.majors_of_student.select()).all()
        
    def is_enrolled(self,new_class):
        result = db.session.scalars(self.enrollments.select().where(Enrolled.course_id == new_class.id)).first()
        return result is not None

    def enroll(self,new_class):
        if not self.is_enrolled(new_class):
            # new_enrollment = Enrolled( course_enrolled = new_class, student_enrolled =  self)
            new_enrollment = Enrolled( course_id = new_class.id, student_id =  self.id)
            db.session.add(new_enrollment)
            db.session.commit()

    def unenroll(self,old_class):
        if self.is_enrolled(old_class):
            cur_enrollment = db.session.scalars(self.enrollments.select().where(Enrolled.course_id == old_class.id)).first()
            db.session.delete(cur_enrollment)
            db.session.commit()

    def enrolled_courses(self):
        return db.session.scalars(self.enrollments.select()).all()

    def get_enrolment_date(self, the_class):
        if self.is_enrolled(the_class):
            cur_enrollment = db.session.scalars(self.enrollments.select().where(Enrolled.course_id == the_class.id)).first()
            return cur_enrollment.enroll_date
        else:
            return None


class Enrolled(db.Model):
    student_id: sqlo.Mapped[int] = sqlo.mapped_column(sqla.ForeignKey(Student.id), 
                                                     primary_key=True)
    course_id : sqlo.Mapped[int] = sqlo.mapped_column(sqla.ForeignKey(Course.id), 
                                                     primary_key=True)
    enroll_date : sqlo.Mapped[Optional[datetime]] = sqlo.mapped_column(default = lambda : datetime.now(timezone.utc))

    #relationship
    student_enrolled : sqlo.Mapped[Student] = sqlo.relationship( back_populates= 'enrollments')
    course_enrolled : sqlo.Mapped[Course] = sqlo.relationship( back_populates= 'roster')
    #methods
    def __repr__(self):
        return '<Enrolled course: {} student: {} date: {}>'.format(self.course_enrolled, self.student_enrolled, self.enroll_date)
    
    def get_student(self):
        return self.student_enrolled
    
    def get_course(self):
        return self.course_enrolled   


