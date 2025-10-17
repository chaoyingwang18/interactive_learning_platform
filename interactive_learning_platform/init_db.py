from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Check if admin user already exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@polyu.edu.hk', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: username='admin', password='admin123'")
    else:
        print("Admin user already exists.")
    
    # Optionally, create a test lecturer and student
    lecturer = User.query.filter_by(username='lecturer1').first()
    if not lecturer:
        lecturer = User(username='lecturer1', email='lecturer1@polyu.edu.hk', role='lecturer')
        lecturer.set_password('password123')
        db.session.add(lecturer)
        db.session.commit()
        print("Test lecturer created: username='lecturer1', password='password123'")
    
    student = User.query.filter_by(username='student1').first()
    if not student:
        student = User(username='student1', email='student1@polyu.edu.hk', role='student', student_id='12345678A')
        student.set_password('password123')
        db.session.add(student)
        db.session.commit()
        print("Test student created: username='student1', password='password123', student_id='12345678A'")

