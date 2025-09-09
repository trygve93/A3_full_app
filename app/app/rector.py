from flask import Blueprint, render_template, request, redirect, url_for
from app.utils.security import login_required, role_required
from app.models.user import (list_teachers, list_students, create_user, delete_user,
    create_subject, list_subjects, assign_teacher_subject, assign_student_subject)

rector_bp = Blueprint('rector', __name__)

@rector_bp.route('/dashboard')
@login_required
@role_required('rector')
def dashboard():
    return render_template('rector_dashboard.html',
        teachers=list_teachers(),
        students=list_students(),
        subjects=list_subjects())

@rector_bp.route('/teachers/create', methods=['GET','POST'])
@login_required
@role_required('rector')
def create_teacher():
    if request.method=='POST':
        create_user(request.form['username'], request.form['password'], 'teacher', int(request.form['class_id']))
        return redirect(url_for('rector.dashboard'))
    return render_template('users_create.html', role='teacher')

@rector_bp.route('/teachers/<int:uid>/delete')
@login_required
@role_required('rector')
def delete_teacher(uid):
    delete_user(uid); return redirect(url_for('rector.dashboard'))

@rector_bp.route('/students/create', methods=['GET','POST'])
@login_required
@role_required('rector')
def create_student():
    if request.method=='POST':
        create_user(request.form['username'], request.form['password'], 'student', int(request.form['class_id']))
        return redirect(url_for('rector.dashboard'))
    return render_template('users_create.html', role='student')

@rector_bp.route('/students/<int:uid>/delete')
@login_required
@role_required('rector')
def delete_student(uid):
    delete_user(uid); return redirect(url_for('rector.dashboard'))

@rector_bp.route('/subjects', methods=['GET','POST'])
@login_required
@role_required('rector')
def subjects():
    if request.method=='POST':
        create_subject(request.form['name']); return redirect(url_for('rector.subjects'))
    return render_template('subjects.html', subjects=list_subjects())

@rector_bp.route('/assign/teacher-subject', methods=['POST'])
@login_required
@role_required('rector')
def assign_ts():
    assign_teacher_subject(int(request.form['teacher_id']), int(request.form['subject_id']))
    return redirect(url_for('rector.dashboard'))

@rector_bp.route('/assign/student-subject', methods=['POST'])
@login_required
@role_required('rector')
def assign_ss():
    assign_student_subject(int(request.form['student_id']), int(request.form['subject_id']))
    return redirect(url_for('rector.dashboard'))
