from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, abort, flash
from app.utils.security import login_required, role_required
from app.models.user import list_students, subjects_for_teacher, create_or_update_grade, get_grade_file_path
from app.utils.extensions import get_db

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/dashboard')
@login_required
@role_required('teacher')
def dashboard():
    class_id = session['class_id']
    return render_template('teacher_dashboard.html',
        students=list_students(class_id),
        subjects=subjects_for_teacher(session['user_id']))

@teacher_bp.route('/grades/create', methods=['POST'])
@login_required
@role_required('teacher')
def create_grade():
    teacher_id = session['user_id']; class_id = session['class_id']
    student_id = int(request.form['student_id']); subject_id = int(request.form['subject_id'])
    grade = request.form.get('grade','')
    conn=get_db(); cur=conn.cursor(); cur.execute("SELECT id,class_id FROM users WHERE id=? AND role='student'",(student_id,)); stu=cur.fetchone(); conn.close()
    if not stu or stu['class_id']!=class_id: abort(403)
    file_storage = request.files.get('pdf')
    try:
        create_or_update_grade(student_id, subject_id, teacher_id, grade, file_storage)
        flash('Karakter oppdatert.','ok')
    except ValueError as e:
        flash(str(e),'error')
    return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/grades/<int:grade_id>/download')
@login_required
@role_required('teacher')
def download_grade(grade_id):
    req={'id':session['user_id'],'role':session['role'],'class_id':session['class_id']}
    path = get_grade_file_path(grade_id, req)
    if not path: abort(403)
    return send_file(path, as_attachment=True)
