from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# User Model (Lecturer, Student, Admin)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='student') # 'admin', 'lecturer', 'student'
    student_id = db.Column(db.String(20), index=True, unique=True) # For students

    # Relationships
    courses_taught = db.relationship('Course', backref='lecturer', lazy='dynamic', foreign_keys='Course.lecturer_id')
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic')
    activities_created = db.relationship('Activity', backref='creator', lazy='dynamic')
    responses = db.relationship('Response', backref='responder', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Flask-Login required properties and methods
    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

# Course Model
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), index=True, unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic')
    activities = db.relationship('Activity', backref='course', lazy='dynamic')

    def __repr__(self):
        return f'<Course {self.code}>'

# Enrollment Model (Student in Course)
class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Composite key constraint to prevent duplicate enrollments
    __table_args__ = (db.UniqueConstraint('course_id', 'student_id', name='_course_student_uc'),)

    def __repr__(self):
        return f'<Enrollment Course:{self.course_id} Student:{self.student_id}>'

# Activity Model (Poll, Quiz, Word Cloud, Short Answer, Mini-Game)
class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    type = db.Column(db.String(50), nullable=False) # 'poll', 'quiz', 'word_cloud', 'short_answer', 'mini_game'
    content = db.Column(db.Text, nullable=False) # JSON string for question/options/settings
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    # Relationships
    responses = db.relationship('Response', backref='activity', lazy='dynamic')

    def __repr__(self):
        return f'<Activity {self.title} ({self.type})>'

# Response Model (Student's answer to an Activity)
class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    responder_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    response_data = db.Column(db.Text, nullable=False) # JSON string for the answer
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # For Short Answer/GenAI grouping
    group_id = db.Column(db.Integer, index=True) # To group similar answers
    is_correct = db.Column(db.Boolean) # For quizzes

    def __repr__(self):
        return f'<Response Activity:{self.activity_id} Responder:{self.responder_id}>'

# GenAI Task Log
class GenAITask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_type = db.Column(db.String(50), nullable=False) # 'activity_generation', 'answer_grouping'
    input_data = db.Column(db.Text, nullable=False)
    output_data = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending') # 'pending', 'processing', 'completed', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<GenAITask {self.task_type} Status:{self.status}>'

