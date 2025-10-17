from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
import json
from datetime import datetime
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.models import User, Course, Enrollment, Activity, Response, GenAITask
from urllib.parse import urlparse
from app.genai_utils import generate_activity_draft, group_short_answers
from functools import wraps

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'lecturer':
            return redirect(url_for('main.lecturer_dashboard'))
        elif current_user.role == 'student':
            return redirect(url_for('main.student_dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('main.admin_dashboard'))
    return render_template('index.html', title='Home')

# --- Authentication Routes ---

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('main.login'))
        
        login_user(user, remember=remember)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)

    return render_template('login.html', title='Sign In')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    # Only admin should be able to register new users, but for initial setup, we'll allow it.
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student') # Default to student
        student_id = request.form.get('student_id') if role == 'student' else None

        user = User.query.filter_by(username=username).first()
        if user is not None:
            flash('Username already exists.', 'warning')
            return redirect(url_for('main.register'))

        user = User(username=username, email=email, role=role, student_id=student_id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user! Please log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html', title='Register')


# --- Dashboard Routes (Placeholders) ---

@main.route('/lecturer/dashboard')
@login_required
def lecturer_dashboard():
    if current_user.role != 'lecturer':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    # Fetch courses taught by the lecturer
    courses = Course.query.filter_by(lecturer_id=current_user.id).all()
    return render_template('lecturer/dashboard.html', title='Lecturer Dashboard', courses=courses)

@main.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    # Fetch enrolled courses
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    return render_template('student/dashboard.html', title='Student Dashboard', enrollments=enrollments)

@main.route('/student/course/<int:course_id>/activities')
@login_required
def student_course_activities(course_id):
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    # Check if the student is enrolled in this course
    enrollment = Enrollment.query.filter_by(student_id=current_user.id, course_id=course_id).first()
    if not enrollment:
        flash('您没有权限访问此课程。', 'danger')
        return redirect(url_for('main.student_dashboard'))
    
    course = Course.query.get_or_404(course_id)
    activities = Activity.query.filter_by(course_id=course_id).order_by(Activity.created_at.desc()).all()
    
    return render_template('student/course_activities.html', 
                         title=f'{course.code} - 课程活动', 
                         course=course, 
                         activities=activities)

@main.route('/student/activity/<int:activity_id>', methods=['GET', 'POST'])
@login_required
def student_activity_detail(activity_id):
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    activity = Activity.query.get_or_404(activity_id)
    
    # Check if the student is enrolled in this course
    enrollment = Enrollment.query.filter_by(student_id=current_user.id, course_id=activity.course_id).first()
    if not enrollment:
        flash('您没有权限访问此活动。', 'danger')
        return redirect(url_for('main.student_dashboard'))
    
    # Parse the activity content (it's stored as JSON)
    import json
    try:
        content_data = json.loads(activity.content)
    except:
        content_data = {}
    
    # Handle POST request (form submission)
    if request.method == 'POST':
        # Check if the student has already responded to this activity
        existing_response = Response.query.filter_by(
            activity_id=activity_id, 
            responder_id=current_user.id
        ).first()
        
        if existing_response:
            flash('您已经参与过此活动了。', 'warning')
        else:
            # Process different types of responses
            response_data = {}
            
            if activity.type == 'poll':
                # Handle poll response
                selected_option = request.form.get('poll_option')
                if selected_option:
                    response_data = {
                        'type': 'poll',
                        'selected_option': selected_option,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                else:
                    flash('请选择一个选项。', 'warning')
                    return render_template('student/activity_detail.html', 
                                         title=f'{activity.title}', 
                                         activity=activity,
                                         content_data=content_data)
            
            elif activity.type == 'word_cloud':
                # Handle word cloud response
                word_input = request.form.get('word_input')
                if word_input:
                    response_data = {
                        'type': 'word_cloud',
                        'words': word_input.strip(),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                else:
                    flash('请输入词汇。', 'warning')
                    return render_template('student/activity_detail.html', 
                                         title=f'{activity.title}', 
                                         activity=activity,
                                         content_data=content_data)
            
            elif activity.type == 'short_answer':
                # Handle short answer response
                answer = request.form.get('answer')
                if answer:
                    response_data = {
                        'type': 'short_answer',
                        'answer': answer.strip(),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                else:
                    flash('请输入答案。', 'warning')
                    return render_template('student/activity_detail.html', 
                                         title=f'{activity.title}', 
                                         activity=activity,
                                         content_data=content_data)
            
            # Save the response to database
            if response_data:
                new_response = Response(
                    activity_id=activity_id,
                    responder_id=current_user.id,
                    response_data=json.dumps(response_data)
                )
                db.session.add(new_response)
                db.session.commit()
                
                flash('您的回答已成功提交！', 'success')
                return redirect(url_for('main.student_activity_detail', activity_id=activity_id))
    
    # Check if the student has already responded
    user_response = Response.query.filter_by(
        activity_id=activity_id, 
        responder_id=current_user.id
    ).first()
    
    user_response_data = None
    if user_response:
        try:
            user_response_data = json.loads(user_response.response_data)
        except:
            user_response_data = {}
    
    return render_template('student/activity_detail.html', 
                         title=f'{activity.title}', 
                         activity=activity,
                         content_data=content_data,
                         user_response=user_response,
                         user_response_data=user_response_data)

@main.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    return render_template('admin/dashboard.html', title='Admin Dashboard')

# --- Course Management Routes ---

@main.route('/lecturer/course/create', methods=['GET', 'POST'])
@login_required
def create_course():
    if current_user.role != 'lecturer':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        code = request.form.get('code').upper()
        name = request.form.get('name')
        
        if Course.query.filter_by(code=code).first():
            flash(f'Course code {code} already exists.', 'warning')
            return redirect(url_for('main.create_course'))

        course = Course(code=code, name=name, lecturer_id=current_user.id)
        db.session.add(course)
        db.session.commit()
        flash(f'Course {code} - {name} created successfully.', 'success')
        return redirect(url_for('main.lecturer_dashboard'))

    return render_template('lecturer/create_course.html', title='Create New Course')

# --- API Routes (Initial Implementation) ---

@main.route('/api/genai/generate_activity/<int:course_id>', methods=['POST'])
@login_required
def genai_generate_activity(course_id):
    if current_user.role != 'lecturer':
        return jsonify({'error': 'Access denied'}), 403
    
    course = Course.query.get_or_404(course_id)
    if course.lecturer_id != current_user.id:
        return jsonify({'error': 'Unauthorized to manage this course'}), 403

    data = request.get_json()
    topic_or_content = data.get('topic_or_content')
    activity_type = data.get('activity_type', 'quiz') # Default to quiz for testing

    if not topic_or_content:
        return jsonify({'error': 'Missing topic or content'}), 400

    # Log the task
    task = GenAITask(
        user_id=current_user.id,
        task_type='activity_generation',
        input_data=json.dumps({'topic': topic_or_content, 'type': activity_type}),
        status='pending'
    )
    db.session.add(task)
    db.session.commit()

    # Call the GenAI utility
    generated_content = generate_activity_draft(topic_or_content, activity_type)

    if generated_content:
        task.output_data = json.dumps(generated_content)
        task.status = 'completed'
        db.session.commit()
        return jsonify({'success': True, 'content': generated_content}), 200
    else:
        task.status = 'failed'
        db.session.commit()
        return jsonify({'error': 'GenAI generation failed or not supported for this type yet.'}), 500



@main.route('/api/courses/<int:course_id>/students', methods=['POST'])
@login_required
def import_students(course_id):
    if current_user.role != 'lecturer':
        return jsonify({'error': 'Access denied'}), 403
    
    course = Course.query.get_or_404(course_id)
    if course.lecturer_id != current_user.id:
        return jsonify({'error': 'Unauthorized to manage this course'}), 403

    # Expecting a JSON list of students: [{"username": "...", "student_id": "...", "email": "..."}]
    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({'error': 'Invalid data format. Expected a list of students.'}), 400

    imported_count = 0
    for student_data in data:
        student_id_val = student_data.get('student_id')
        username = student_data.get('username')
        email = student_data.get('email')
        
        if not student_id_val or not username:
            continue # Skip invalid entries

        # Find or create student user
        student = User.query.filter_by(student_id=student_id_val, role='student').first()
        if not student:
            # Simple default password for imported students, they should change it on first login
            student = User(username=username, student_id=student_id_val, email=email, role='student')
            student.set_password('password123') # Placeholder password
            db.session.add(student)
            db.session.commit()

        # Enroll student
        enrollment = Enrollment.query.filter_by(course_id=course_id, student_id=student.id).first()
        if not enrollment:
            enrollment = Enrollment(course_id=course_id, student_id=student.id)
            db.session.add(enrollment)
            imported_count += 1

    db.session.commit()
    return jsonify({'message': f'Successfully imported and enrolled {imported_count} students.'}), 200

# --- Activity Management Routes (Placeholder) ---

@main.route('/lecturer/course/<int:course_id>/activities')
@login_required
def manage_activities(course_id):
    if current_user.role != 'lecturer':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    course = Course.query.get_or_404(course_id)
    if course.lecturer_id != current_user.id:
        flash('Unauthorized to manage this course.', 'danger')
        return redirect(url_for('main.lecturer_dashboard'))
    
    activities = Activity.query.filter_by(course_id=course_id).order_by(Activity.created_at.desc()).all()
    return render_template('lecturer/manage_activities.html', title=f'Manage Activities for {course.code}', course=course, activities=activities)

@main.route('/lecturer/activity/create/<int:course_id>', methods=['GET', 'POST'])
@login_required
def create_activity(course_id):
    if current_user.role != 'lecturer':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    course = Course.query.get_or_404(course_id)
    if course.lecturer_id != current_user.id:
        flash('Unauthorized to manage this course.', 'danger')
        return redirect(url_for('main.lecturer_dashboard'))

    # This route will handle the form submission for creating a new activity
    if request.method == 'POST':
        title = request.form.get('title')
        activity_type = request.form.get('type')
        content_data = {}

        if activity_type in ['poll', 'quiz']:
            options = request.form.get('options').split('\n')
            content_data = {
                'question': request.form.get('question'),
                'options': [opt.strip() for opt in options if opt.strip()],
            }
            if activity_type == 'quiz':
                content_data['correct_answer'] = request.form.get('correct_answer')
        elif activity_type == 'word_cloud':
            content_data = {
                'prompt': request.form.get('prompt')
            }
        elif activity_type == 'short_answer':
            content_data = {
                'question': request.form.get('question')
            }
        
        # Mini-game will be a placeholder for now
        if not title or not activity_type or not content_data:
            flash('請填寫所有必要的活動信息。', 'danger')
            return redirect(url_for('main.create_activity', course_id=course_id))

        activity = Activity(
            course_id=course_id,
            creator_id=current_user.id,
            title=title,
            type=activity_type,
            content=json.dumps(content_data),
            is_active=False
        )
        db.session.add(activity)
        db.session.commit()
        flash(f'活動 "{title}" 創建成功！', 'success')
        return redirect(url_for('main.manage_activities', course_id=course_id))

    return render_template('lecturer/create_activity.html', title=f'Create Activity for {course.code}', course=course)



@main.route('/lecturer/activity/<int:activity_id>/<action>', methods=['POST'])
@login_required
def toggle_activity_status(activity_id, action):
    if current_user.role != 'lecturer':
        return jsonify({'error': 'Access denied'}), 403
    
    activity = Activity.query.get_or_404(activity_id)
    if activity.creator_id != current_user.id:
        return jsonify({'error': 'Unauthorized to manage this activity'}), 403

    if action == 'start':
        activity.is_active = True
        flash(f'活動 "{activity.title}" 已開始！', 'success')
    elif action == 'stop':
        activity.is_active = False
        flash(f'活動 "{activity.title}" 已結束！', 'success')
    else:
        return jsonify({'error': 'Invalid action'}), 400

    db.session.commit()
    return redirect(url_for('main.manage_activities', course_id=activity.course_id))

@main.route('/api/response/<int:activity_id>', methods=['POST'])
@login_required
def submit_response(activity_id):
    if current_user.role != 'student':
        return jsonify({'error': 'Access denied'}), 403
    
    activity = Activity.query.get_or_404(activity_id)
    if not activity.is_active:
        return jsonify({'error': 'Activity is not currently active'}), 400

    # Basic check for student enrollment (optional but good practice)
    is_enrolled = Enrollment.query.filter_by(
        course_id=activity.course_id, 
        student_id=current_user.id
    ).first()
    if not is_enrolled:
        return jsonify({'error': 'Not enrolled in this course'}), 403

    data = request.get_json()
    response_data = data.get('response_data')
    
    if not response_data:
        return jsonify({'error': 'Missing response data'}), 400

    # Prevent duplicate submission (for simple activities)
    existing_response = Response.query.filter_by(
        activity_id=activity_id, 
        responder_id=current_user.id
    ).first()
    if existing_response:
        # For simplicity, we just update the existing response
        existing_response.response_data = json.dumps(response_data)
    else:
        response = Response(
            activity_id=activity_id,
            responder_id=current_user.id,
            response_data=json.dumps(response_data)
        )
        db.session.add(response)

    db.session.commit()
    return jsonify({'message': 'Response submitted successfully'}), 200

# --- GenAI Answer Grouping API ---

@main.route('/api/genai/group_answers/<int:activity_id>', methods=['POST'])
@login_required
def genai_group_answers(activity_id):
    if current_user.role != 'lecturer':
        return jsonify({'error': 'Access denied'}), 403
    
    activity = Activity.query.get_or_404(activity_id)
    if activity.creator_id != current_user.id:
        return jsonify({'error': 'Unauthorized to manage this activity'}), 403

    if activity.type != 'short_answer':
        return jsonify({'error': 'Answer grouping is only for Short Answer activities'}), 400

    # 1. Get all responses
    responses = Response.query.filter_by(activity_id=activity_id).all()
    if not responses:
        return jsonify({'message': 'No responses to group'}), 200

    # Extract the text of each response
    # Assuming response_data for short_answer is a simple string like {"answer": "..."}
    answers_text = []
    for response in responses:
        try:
            data = json.loads(response.response_data)
            # Assuming the short answer is stored under the key 'answer'
            answers_text.append(data.get('answer', '')) 
        except json.JSONDecodeError:
            answers_text.append('')

    # 2. Call the GenAI utility
    grouping_result = group_short_answers(answers_text)

    if grouping_result:
        # 3. Update the responses with group_id
        # We need to map the result back to the Response objects
        group_id_counter = 1
        for group_label, indices in grouping_result.items():
            for index in indices:
                # The index corresponds to the position in the 'responses' list
                if 0 <= index < len(responses):
                    responses[index].group_id = group_id_counter
            group_id_counter += 1
        
        # Log the task
        task = GenAITask(
            user_id=current_user.id,
            task_type='answer_grouping',
            input_data=json.dumps({'activity_id': activity_id, 'count': len(answers_text)}),
            output_data=json.dumps(grouping_result),
            status='completed'
        )
        db.session.add(task)
        db.session.commit()
        
        return jsonify({'message': 'Answers grouped successfully', 'groups': grouping_result}), 200
    else:
        # Log the failed task
        task = GenAITask(
            user_id=current_user.id,
            task_type='answer_grouping',
            input_data=json.dumps({'activity_id': activity_id, 'count': len(answers_text)}),
            status='failed'
        )
        db.session.add(task)
        db.session.commit()
        return jsonify({'error': 'GenAI grouping failed'}), 500



# --- Reporting and Dashboard Routes ---

@main.route('/lecturer/activity/report/<int:activity_id>')
@login_required
def activity_report(activity_id):
    if current_user.role != 'lecturer':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    activity = Activity.query.get_or_404(activity_id)
    if activity.creator_id != current_user.id:
        flash('Unauthorized to view this report.', 'danger')
        return redirect(url_for('main.lecturer_dashboard'))

    # Fetch responses
    responses = Response.query.filter_by(activity_id=activity_id).all()
    
    # Process activity content and responses
    activity_content = json.loads(activity.content)
    report_data = {
        'activity': activity,
        'content': activity_content,
        'responses': []
    }
    
    if activity.type == 'short_answer':
        # Grouping data for short_answer
        group_counts = db.session.query(Response.group_id, db.func.count(Response.id)).\
            filter(Response.activity_id == activity_id, Response.group_id.isnot(None)).\
            group_by(Response.group_id).all()
        
        # Fetch the GenAI task log for group labels
        genai_task = GenAITask.query.filter_by(
            task_type='answer_grouping', 
            status='completed'
        ).order_by(GenAITask.completed_at.desc()).first()
        
        group_labels = {}
        if genai_task and genai_task.output_data:
            try:
                grouping_result = json.loads(genai_task.output_data)
                # Reverse map the indices to find the group label for each group_id
                # This is a bit complex, simpler to just pass the grouping_result to the template
                # and let the template handle the presentation
                report_data['grouping_result'] = grouping_result
            except json.JSONDecodeError:
                pass

        report_data['group_counts'] = group_counts
        
    # Prepare individual responses for display
    for response in responses:
        try:
            data = json.loads(response.response_data)
        except json.JSONDecodeError:
            data = {'answer': 'Invalid data'}
            
        report_data['responses'].append({
            'responder': response.responder.username,
            'data': data,
            'group_id': response.group_id
        })

    return render_template('lecturer/activity_report.html', title=f'活動報告 - {activity.title}', report_data=report_data)

# --- Leaderboard and Student Dashboard Refinement ---

@main.route('/student/leaderboard')
@login_required
def student_leaderboard():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    # Placeholder for a simple global leaderboard based on total correct quiz answers
    # This will require more complex logic for scoring, but for now, we'll keep it simple.
    
    # Example: Count correct answers for all quizzes
    # This is a complex query and will be simplified for the initial implementation
    # For now, just show a placeholder page
    
    return render_template('student/leaderboard.html', title='我的排行榜')



# --- Admin Routes ---

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied: Admin privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function



@main.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/user_management.html', title='用戶管理', users=users)

@main.route('/admin/genai_tasks')
@login_required
@admin_required
def admin_genai_tasks():
    tasks = GenAITask.query.order_by(GenAITask.created_at.desc()).all()
    return render_template('admin/genai_task_log.html', title='GenAI 任務日誌', tasks=tasks)

@main.route('/student/quiz/<int:activity_id>', methods=['GET', 'POST'])
@login_required
def student_quiz(activity_id):
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    activity = Activity.query.get_or_404(activity_id)
    if activity.type != 'quiz':
        flash('该活动不是测验类型。', 'danger')
        return redirect(url_for('main.student_dashboard'))
    enrollment = Enrollment.query.filter_by(student_id=current_user.id, course_id=activity.course_id).first()
    if not enrollment:
        flash('您没有权限访问此测验。', 'danger')
        return redirect(url_for('main.student_dashboard'))
    import json
    try:
        quiz_data = json.loads(activity.content)
        if 'questions' not in quiz_data and 'question' in quiz_data:
            quiz_data = {'questions': [quiz_data]}
    except:
        quiz_data = {}
    # 查询是否已提交
    user_response = Response.query.filter_by(activity_id=activity_id, responder_id=current_user.id).first()
    user_answer = None
    if user_response:
        try:
            user_answer = json.loads(user_response.response_data).get('answer')
        except:
            user_answer = None
    # 处理提交，彻底防止重复
    if request.method == 'POST':
        if user_response:
            flash('您已提交过测验，不能重复提交。', 'warning')
            return redirect(url_for('main.student_quiz', activity_id=activity_id))
        selected = request.form.get('q1')
        if selected:
            response_data = {'type': 'quiz', 'answer': selected, 'timestamp': datetime.utcnow().isoformat()}
            new_response = Response(activity_id=activity_id, responder_id=current_user.id, response_data=json.dumps(response_data))
            db.session.add(new_response)
            db.session.commit()
            flash('测验已提交！', 'success')
            return redirect(url_for('main.student_quiz', activity_id=activity_id))
        else:
            flash('请选择一个选项。', 'warning')
    return render_template('student/quiz.html', title=activity.title, activity=activity, quiz_data=quiz_data, user_answer=user_answer)

