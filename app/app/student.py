from flask import Blueprint, render_template, session, send_file, abort
from app.utils.security import login_required, role_required
from app.models.user import list_grades_for_student, get_grade_file_path

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    me = session['user_id']
    return render_template('student_dashboard.html', grades=list_grades_for_student(me))

@student_bp.route('/grades/<int:grade_id>/download')
@login_required
@role_required('student')
def download_grade(grade_id):
    req={'id':session['user_id'],'role':session['role'],'class_id':session['class_id']}
    path = get_grade_file_path(grade_id, req)
    if not path: abort(403)
    return send_file(path, as_attachment=True)
